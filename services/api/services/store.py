from ..schemas.task import Task

# Tmp to replace with db later
tasks: dict[str, Task] = {}

idempotency_map: dict[str, str] = {}
