from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from ..services.store import tasks
from ..schemas.tast_status import TaskStatus

internal_router = APIRouter()


class StatusUpdatePayload(BaseModel):
    task_id: str
    status: TaskStatus
    result_url: str | None = None
    error: str | None = None


@internal_router.post("/internal/update-status")
def update_status(
    payload: StatusUpdatePayload,
    x_internal_key: str = Header(...),
):
    if x_internal_key != "internal-key":  # will replace with queue anyway
        raise HTTPException(403, "Forbidden")

    task = tasks.get(payload.task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    task.update_status(
        new_status=payload.status,
        result_url=payload.result_url,
        error=payload.error,
    )

    print(f"[INTERNAL] Task {payload.task_id} → {payload.status.value}")
    return {"status": "updated"}
