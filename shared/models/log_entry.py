from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession

from .base_class import Base


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, index=True)
    level = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


async def log_entry(session: AsyncSession, message: str, level: str) -> None:
    new_log = LogEntry(message=message, level=level)
    session.add(new_log)
    await session.commit()
