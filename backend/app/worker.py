import time

from .config import JOB_MAX_ATTEMPTS
from .db import SessionLocal
from .models import Job
from .queue import ack, dead_letter, dequeue, enqueue, requeue
from .services.generation import run_job


def handle_result(job_id: str, status: str) -> None:
    if status != "failed":
        ack(job_id)
        return
    db = SessionLocal()
    job = db.get(Job, job_id)
    if not job:
        db.close()
        ack(job_id)
        return
    if job.attempts < JOB_MAX_ATTEMPTS:
        job.status = "queued"
        db.commit()
        db.close()
        ack(job_id)
        enqueue(job_id)
        return
    job.status = "dead"
    db.commit()
    db.close()
    ack(job_id)
    dead_letter(job_id)


def main() -> None:
    requeue()
    while True:
        try:
            job_id = dequeue(5)
            if not job_id:
                time.sleep(0.5)
                continue
            try:
                status = run_job(job_id)
            except Exception:  # noqa: BLE001
                status = "failed"
            handle_result(job_id, status)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
