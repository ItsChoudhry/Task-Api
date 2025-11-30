from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.models.base import get_db
from services.api.models.db import TaskDB
from ..schemas.task_status import TaskStatus

internal_router = APIRouter()


class StatusUpdatePayload(BaseModel):
    task_id: str
    status: TaskStatus
    result_url: str | None = None
    error: str | None = None


@internal_router.post("/internal/update-status")
async def update_status(
    payload: StatusUpdatePayload,
    x_internal_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    if x_internal_key != "internal-key":  # will replace with queue anyway
        raise HTTPException(403, "Forbidden")

    task = await db.get(TaskDB, payload.task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    task.status = payload.status.value
    if payload.result_url:
        task.result_url = payload.result_url
    if payload.error:
        task.error = payload.error
    task.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(task)

    print(f"[INTERNAL] Task {payload.task_id} → {task.status}")
    return {"status": "updated"}
