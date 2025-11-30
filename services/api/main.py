from contextlib import asynccontextmanager

from .schemas.task_status import TaskStatus
from services.api.routers.internal import internal_router

from .schemas.task import Task
from .services.store import tasks
from .routers.protected import protected_router
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    placeholder_task = Task(
        id=str("0"),
        idempotency_key=str(uuid.uuid4()),
        model="Placeholder model",
        param={},
        inputs={},
        status=TaskStatus.PROCESSING,
        result_url="",
        error="",
        callback_url="",
        api_key_id="",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    tasks[placeholder_task.id] = placeholder_task
    print(f"Added placeholder task with ID: {placeholder_task.id}")

    yield

    tasks.clear()
    print("Cleared tasks on shutdown")


app = FastAPI(
    title="task_pipeline",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

app.include_router(protected_router)
app.include_router(internal_router)


@app.get("/healthz")
def health_check():
    try:
        # _perform_health_checks()
        return JSONResponse(status_code=200, content={"status": "healthy"})
    except Exception as e:
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "error": e})


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom OpenAPI docs at /docs with Swagger UI."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + "",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_ui_parameters={
            "persistAuthorization": True,
        },
    )


@app.get("/openapi.json", include_in_schema=False)
def get_openapi_schema():
    return app.openapi()
