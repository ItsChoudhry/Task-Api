from enum import Enum


class TaskStatus(str, Enum):
    RECEIVED = "received"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
