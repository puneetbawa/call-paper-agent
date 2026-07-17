import logging
import threading
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import KEYWORDS, WIKICFP_CATEGORIES
from app.db import Event, get_session, init_db
from app.models import EventOut
from app.scheduler import scheduler, start_scheduler
from app.services.fetcher import refresh_all
from app.services.ics_export import build_ics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cfp-agent")

app = FastAPI(
    title="CFP & Conference Schedule Agent",
    description=(
        "Aggregates Calls for Papers and conference schedules relevant to "
        "speech processing, speech applications, NLP, and healthcare NLP."
    ),
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()
    # Kick off a first fetch in the background so the app boots instantly.
    threading.Thread(target=refresh_all, daemon=True).start()


def _query_events(
    session,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    has_deadline: bool = False,
    limit: int = 200,
):
    q = session.query(Event)
    if category:
        q = q.filter(Event.category.ilike(f"%{category}%"))
    if keyword:
        q = q.filter(
            (Event.matched_keywords.ilike(f"%{keyword}%"))
            | (Event.title.ilike(f"%{keyword}%"))
        )
    if has_deadline:
        q = q.filter(Event.deadline.isnot(None))
    return q.order_by(Event.fetched_at.desc()).limit(limit).all()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/categories")
def list_categories():
    return {"categories": WIKICFP_CATEGORIES, "keywords": KEYWORDS}


@app.get("/api/cfps", response_model=list[EventOut])
def api_list_cfps(
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    has_deadline: bool = Query(False),
    limit: int = Query(200, le=1000),
):
    session = get_session()
    try:
        events = _query_events(session, category, keyword, has_deadline, limit)
        return events
    finally:
        session.close()


@app.get("/api/cfps/{event_id}", response_model=EventOut)
def api_get_cfp(event_id: int):
    session = get_session()
    try:
        ev = session.query(Event).get(event_id)
        if not ev:
            return Response(status_code=404, content="Not found")
        return ev
    finally:
        session.close()


@app.post("/api/refresh")
def api_refresh():
    """Manually trigger a refresh (also runs automatically on a schedule)."""
    summary = refresh_all()
    return summary


@app.get("/api/calendar.ics")
def api_calendar():
    session = get_session()
    try:
        events = session.query(Event).order_by(Event.fetched_at.desc()).all()
        ics_bytes = build_ics(events)
    finally:
        session.close()
    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=cfp_schedule.ics"},
    )


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, category: Optional[str] = None, keyword: Optional[str] = None):
    session = get_session()
    try:
        events = _query_events(session, category=category, keyword=keyword, limit=200)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "events": events,
                "categories": WIKICFP_CATEGORIES,
                "selected_category": category or "",
                "selected_keyword": keyword or "",
            },
        )
    finally:
        session.close()
