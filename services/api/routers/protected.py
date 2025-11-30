from datetime import datetime, timezone
import logging
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.models.base import get_db
from ..auth import require_api_key
from services.api.schemas.task import CreateTask, Task
from services.api.models.db import TaskDB, TaskDBStatus
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from fastapi.responses import JSONResponse
import httpx

rate_limit_map: dict[str, tuple[int, datetime]] = {}


def check_rate(x_api_key: str = Header(...)):
    now = datetime.now(timezone.utc)
    LIMIT = 10
    WINDOW = 60

    if x_api_key in rate_limit_map:
        count, last_time = rate_limit_map[x_api_key]
        elapsed = (now - last_time).total_seconds()

        if elapsed > WINDOW:
            count = 0
        else:
            count += 1
    else:
        count = 1

    rate_limit_map[x_api_key] = (count, now)

    if count > LIMIT:
        retry_after = int(WINDOW - elapsed)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


protected_router = APIRouter(
    dependencies=[Depends(require_api_key), Depends(check_rate)], tags=["protected"]
)


@protected_router.post("/v1/tasks")
async def add_task(
    task: CreateTask,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
):
    idem_key = idempotency_key or str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    # 1. Idempotency check — replay if already exists
    existing = await db.execute(
        select(TaskDB).where(TaskDB.idempotency_key == idem_key)
    )
    existing = existing.scalar_one_or_none()

    if existing:
        return JSONResponse(
            status_code=200,
            content={"task_id": existing.id},
            headers={"Location": f"/v1/tasks/{existing.id}"},
        )

    new_task = TaskDB(
        id=task_id,
        idempotency_key=idem_key,
        model=task.model,
        param=task.param or {},
        inputs=task.inputs or {},
        status=TaskDBStatus.received,
        callback_url=task.callback_url,
        api_key_id=x_api_key,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(new_task)

    try:
        await db.commit()
        await db.refresh(new_task)
    except IntegrityError:
        await db.rollback()
        # Race condition — someone else won → replay their task
        replay = await db.execute(select(Task).where(Task.idempotency_key == idem_key))
        replay_task = replay.scalar_one_or_none()
        if replay_task:
            return JSONResponse(
                status_code=200,
                content={"task_id": replay_task.id},
                headers={"Location": f"/v1/tasks/{replay_task.id}"},
            )
        raise HTTPException(500, "Database error")

    background_tasks.add_task(trigger_worker, task_id, task.model, task.inputs)

    response = JSONResponse(content={"task_id": task_id})
    response.status_code = 201
    response.headers["Location"] = f"/v1/tasks/{task_id}"
    return response


def trigger_worker(id: str, model: str, inputs: dict):
    payload = {
        "task_id": id,
        "model": model,
        "inputs": inputs,
    }
    try:
        httpx.post(
            "http://worker:9000/process",
            json=payload,
            headers={"X-Worker-Key": "worker-key"},
            timeout=30.0,
        )
        logging.info("Triggered worker")
    except Exception as e:
        logging.error(f"Trigger worker failed {e}")


@protected_router.get("/v1/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await db.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return Task.model_validate(task)


@protected_router.get("/v1/models")
def list_models():
    return {"ChatBpd": ["0.1.0"], "Cloudsunut": ["0.2.1"]}


@protected_router.get("/readyz")
async def ready_check(db: AsyncSession = Depends(get_db)):
    try:
        # _perform_health_checks()
        # check redis ping, minIO access check
        await db.execute(select(1))
        return JSONResponse(status_code=200, content={"status": "ready"})
    except Exception as e:
        logging.error(f"Readiness probe failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
