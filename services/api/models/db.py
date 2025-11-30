from typing import Annotated
from sqlalchemy import Column, String, JSON, DateTime, text
from sqlalchemy.dialects.postgresql import ENUM
from enum import StrEnum

from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class TaskDBStatus(StrEnum):
    received = "received"
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


TaskStatusColumn = Annotated[
    TaskDBStatus,
    mapped_column(
        ENUM(TaskDBStatus, name="task_status", create_type=True),
        nullable=False,
        default=TaskDBStatus.received,
    ),
]


class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    model = Column(String, nullable=False)
    param = Column(JSON, default=dict)
    inputs = Column(JSON, default=dict)
    status: Mapped[TaskStatusColumn]
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
