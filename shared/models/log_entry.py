from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from .base_class import Base


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True)
    message = Column(String, index=True)
    level = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
