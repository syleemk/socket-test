from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
