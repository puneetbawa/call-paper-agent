import datetime as dt
import os

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

# Make sure the sqlite folder exists (only matters for the sqlite:/// case).
# NOTE: "sqlite:///" (3 slashes) = relative path, "sqlite:////" (4 slashes)
# = absolute path. We must only strip the URL prefix, never a leading "/"
# from the path itself, or absolute paths silently become relative ones.
_SQLITE_PREFIX = "sqlite:///"
if DATABASE_URL.startswith(_SQLITE_PREFIX):
    path = DATABASE_URL[len(_SQLITE_PREFIX):]  # keeps leading "/" if absolute
    folder = os.path.dirname(path) or "."
    os.makedirs(folder, exist_ok=True)
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Event(Base):
    """A Call for Papers / conference entry."""

    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("link", name="uq_event_link"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(64), nullable=False)          # e.g. "wikicfp"
    category = Column(String(128), nullable=True)         # feed category searched
    title = Column(String(512), nullable=False)
    link = Column(String(1024), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(256), nullable=True)
    deadline = Column(String(64), nullable=True)           # raw submission deadline text
    start_date = Column(String(64), nullable=True)
    end_date = Column(String(64), nullable=True)
    matched_keywords = Column(Text, nullable=True)         # comma-separated
    fetched_at = Column(DateTime, default=dt.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
