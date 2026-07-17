from typing import Optional

from pydantic import BaseModel


class EventOut(BaseModel):
    id: int
    source: str
    category: Optional[str] = None
    title: str
    link: str
    description: Optional[str] = None
    location: Optional[str] = None
    deadline: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    matched_keywords: Optional[str] = None

    class Config:
        from_attributes = True
