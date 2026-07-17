import logging
import re

import feedparser
import requests

from app.config import (
    REQUEST_TIMEOUT,
    USER_AGENT,
    WIKICFP_CATEGORIES,
    WIKICFP_RSS_TEMPLATE,
)
from app.db import Event, get_session
from app.services.filters import find_matches

logger = logging.getLogger("cfp-agent.fetcher")

DEADLINE_RE = re.compile(r"(Deadline|Submission Deadline)[:\s]*([^\n<]{4,40})", re.I)
WHEN_RE = re.compile(r"When[:\s]*([^\n<]{4,60})", re.I)
WHERE_RE = re.compile(r"Where[:\s]*([^\n<]{2,80})", re.I)


def _extract(pattern, text):
    if not text:
        return None
    m = pattern.search(text)
    return m.group(m.lastindex).strip() if m else None


def fetch_category(category: str):
    """Fetch and parse a single WikiCFP RSS category feed. Returns list of
    dict entries. Network errors are logged and swallowed so one bad feed
    doesn't stop the whole refresh job."""
    url = WIKICFP_RSS_TEMPLATE.format(category=requests.utils.quote(category))
    try:
        resp = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch WikiCFP category '%s': %s", category, exc)
        return []

    parsed = feedparser.parse(resp.content)
    results = []
    for entry in parsed.entries:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        description = getattr(entry, "description", "") or getattr(
            entry, "summary", ""
        )
        if not title or not link:
            continue
        results.append(
            {
                "title": title,
                "link": link,
                "description": description,
                "deadline": _extract(DEADLINE_RE, description),
                "when": _extract(WHEN_RE, description),
                "where": _extract(WHERE_RE, description),
            }
        )
    return results


def refresh_all(categories=None):
    """Fetch every configured category, keep only entries that match our
    research-area keywords, and upsert them into the database.

    Returns a summary dict with counts.
    """
    categories = categories or WIKICFP_CATEGORIES
    session = get_session()
    fetched, kept, inserted, updated = 0, 0, 0, 0
    try:
        for category in categories:
            entries = fetch_category(category)
            for e in entries:
                fetched += 1
                haystack = f"{e['title']} {e['description']} {category}"
                matches = find_matches(haystack)
                if not matches:
                    continue
                kept += 1

                existing = (
                    session.query(Event).filter_by(link=e["link"]).one_or_none()
                )
                if existing:
                    existing.deadline = e["deadline"] or existing.deadline
                    existing.start_date = e["when"] or existing.start_date
                    existing.location = e["where"] or existing.location
                    existing.matched_keywords = ", ".join(sorted(set(matches)))
                    updated += 1
                else:
                    session.add(
                        Event(
                            source="wikicfp",
                            category=category,
                            title=e["title"],
                            link=e["link"],
                            description=e["description"],
                            deadline=e["deadline"],
                            start_date=e["when"],
                            location=e["where"],
                            matched_keywords=", ".join(sorted(set(matches))),
                        )
                    )
                    inserted += 1
            session.commit()
    finally:
        session.close()

    summary = {
        "categories_checked": len(categories),
        "entries_fetched": fetched,
        "entries_relevant": kept,
        "inserted": inserted,
        "updated": updated,
    }
    logger.info("Refresh complete: %s", summary)
    return summary
