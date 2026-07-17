import re
from typing import List

from app.config import KEYWORDS


def find_matches(text: str, keywords: List[str] = None) -> List[str]:
    """Return the subset of keywords found (case-insensitive, whole-ish word)
    inside `text`. Used to decide relevance and to tag results.
    """
    if not text:
        return []
    keywords = keywords or KEYWORDS
    text_lower = text.lower()
    matches = []
    for kw in keywords:
        pattern = r"(?<![a-z0-9])" + re.escape(kw.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            matches.append(kw)
    return matches


def is_relevant(text: str, keywords: List[str] = None) -> bool:
    return len(find_matches(text, keywords)) > 0
