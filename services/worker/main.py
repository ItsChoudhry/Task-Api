import time
from typing import Optional
import httpx
from redis import Redis
from rq import Queue

redis_conn = Redis(host="redis", port=6379, db=0)

q = Queue(name="tasks", connection=redis_conn)


def send_request_update(task_id: str, status: str, result_url: Optional[str] = None):
    try:
        httpx.post(
            "http://api:8000/internal/update-status",
            json={
                "task_id": task_id,
                "status": status,
                "result_url": result_url,
            },
            headers={"X-Internal-Key": "internal-key"},
            timeout=10,
        )
        print(f"Task {task_id} → {status}")
    except Exception as e:
        print(f"Failed update status to {status} for {task_id}: {e}")


def process_task(task_id: str, model: str, inputs: dict):
    """This function will be called by the worker"""
    print(f"Worker: Starting task {task_id} with model {model}")

    send_request_update(task_id, "processing")

    time.sleep(30)

    result_url = f"https://results.example.com/{task_id}.json"
    send_request_update(task_id, "completed", result_url)


if __name__ == "__main__":
    from rq.worker import SimpleWorker

    worker = SimpleWorker([q], connection=redis_conn)
    worker.work()
