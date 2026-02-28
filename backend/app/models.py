from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    created_by = Column(String(50), nullable=False)
    is_private = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    channel_name = Column(String(100), nullable=False, default="general")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
