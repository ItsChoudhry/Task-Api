import time
import json
import boto3
from botocore.client import Config
from typing import Optional
import httpx
from redis import Redis
from rq import Queue
from prometheus_client import Counter, start_http_server


JOBS_COMPLETED = Counter("rq_jobs_completed_total", "Total completed jobs")
JOBS_FAILED = Counter("rq_jobs_failed_total", "Total failed jobs")

start_http_server(8001)

redis_conn = Redis(host="redis", port=6379, db=0)

q = Queue(name="tasks", connection=redis_conn)

# 1. Use INTERNAL host for uploads (this works inside Docker)
s3 = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin123",
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

# 2. Use EXTERNAL host only for generating URLs
s3_external = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin123",
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

BUCKET_NAME = "tasks"


def generate_presigned_url(task_id: str, expires_in: int = 3600) -> str:
    """Generate 1-hour expiring download URL"""
    key = f"{task_id}/result.json"
    return s3_external.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
        HttpMethod="GET",
    )


def send_request_update(task_id: str, status: str, result_url: Optional[str] = None):
    try:
        payload = {
            "task_id": task_id,
            "status": status,
        }
        if result_url:
            payload["result_url"] = result_url
        httpx.post(
            "http://api:8000/internal/update-status",
            json=payload,
            headers={"X-Internal-Key": "internal-key"},
            timeout=10,
        )
        print(f"Task {task_id} → {status}")
    except Exception as e:
        JOBS_FAILED.inc()
        print(f"Failed update status to {status} for {task_id}: {e}")


def process_task(task_id: str, model: str, inputs: dict):
    """This function will be called by the worker"""
    print(f"Worker: Starting task {task_id} with model {model}")

    send_request_update(task_id, "processing")

    time.sleep(10)

    result_data = {
        "task_id": task_id,
        "model": model,
        "inputs": inputs,
        "output": {"hello": "world", "generated_at": time.time()},
        "status": "success",
    }

    key = f"{task_id}/result.json"

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(result_data, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    download_url = generate_presigned_url(task_id)

    JOBS_COMPLETED.inc()
    send_request_update(task_id, "completed", download_url)


if __name__ == "__main__":
    from rq.worker import SimpleWorker

    worker = SimpleWorker([q], connection=redis_conn)
    worker.work()
