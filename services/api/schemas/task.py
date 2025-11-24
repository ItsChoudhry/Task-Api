from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from .tast_status import TaskStatus


class Task(BaseModel):
    id: str
    idempotency_key: Optional[str] = None
    model: str
    param: dict[str, str]
    inputs: dict[str, str]
    status: TaskStatus
    result_url: Optional[str] = None
    error: Optional[str] = None
    callback_url: Optional[str] = None
    api_key_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    def update_status(
        self,
        new_status: TaskStatus,
        result_url: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.status = new_status
        self.result_url = result_url
        self.error = error
        self.updated_at = datetime.now(timezone.utc)

    def __str__(self) -> str:
        status_emoji = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.PROCESSING: "⚙️",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
        }.get(self.status, "🔄")

        base = (
            f"Task(id='{self.id}' | "
            f"{status_emoji} {self.status.value.upper()} | "
            f"model='{self.model}')"
        )

        extras = []
        if self.idempotency_key:
            extras.append(f"idem_key='{self.idempotency_key}'")
        if self.result_url:
            extras.append(f"result_url='{self.result_url}'")
        if self.error:
            extras.append(f"error='{self.error}'")
        if self.callback_url:
            extras.append(f"callback='{self.callback_url}'")

        if extras:
            base += f" [{', '.join(extras)}]"

        base += f" | ⏱ {self.updated_at.strftime('%H:%M:%S')} UTC"
        return base

    def __repr__(self) -> str:
        return (
            f"Task(id={self.id!r}, status={self.status.value!r}, "
            f"model={self.model!r}, updated_at={self.updated_at.isoformat()!r})"
        )


class CreateTask(BaseModel):
    model: str
    param: dict[str, str]
    inputs: dict[str, str]
    callback_url: Optional[str] = None
