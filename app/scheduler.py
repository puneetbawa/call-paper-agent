import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import REFRESH_INTERVAL_HOURS
from app.services.fetcher import refresh_all

logger = logging.getLogger("cfp-agent.scheduler")

scheduler = BackgroundScheduler()


def _job():
    logger.info("Running scheduled CFP refresh...")
    try:
        refresh_all()
    except Exception:
        logger.exception("Scheduled refresh failed")


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            _job,
            "interval",
            hours=REFRESH_INTERVAL_HOURS,
            next_run_time=None,  # first run triggered manually at startup
            id="refresh_job",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            "Scheduler started, refreshing every %s hour(s)", REFRESH_INTERVAL_HOURS
        )
