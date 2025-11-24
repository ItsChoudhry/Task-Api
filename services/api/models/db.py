from sqlalchemy import Column, String, JSON, DateTime, text
from sqlalchemy.dialects.postgresql import ENUM
from enum import StrEnum
from .base import Base


class TaskStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    model = Column(String, nullable=False)
    param = Column(JSON, default=dict)
    inputs = Column(JSON, default=dict)
    status = Column(
        ENUM(TaskStatus, create_type=True), default=TaskStatus.PENDING, nullable=False
    )
    result_url = Column(String)
    error = Column(String)
    callback_url = Column(String)
    api_key_id = Column(String)
    created_at = Column(
        DateTime(timezone=True), server_default=text("TIMEZONE('utc', NOW())")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=text("TIMEZONE('utc', NOW())"),
    )
