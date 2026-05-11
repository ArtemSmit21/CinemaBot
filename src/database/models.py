from sqlalchemy import Column, Integer, Text, DateTime, BigInteger
from sqlalchemy.sql import func
from .config import Base


class MessageHistory(Base):
    __tablename__ = "message_history"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, index=True, nullable=False)
    message_id = Column(Integer)
    text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FilmStats(Base):
    __tablename__ = "film_stats"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, index=True, nullable=False)
    text = Column(Text)
