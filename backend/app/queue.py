from .state import state


def enqueue(job_id: str) -> None:
    state.push_job(job_id)


def dequeue(timeout: int = 5) -> str | None:
    return state.pop_job(timeout)


def ack(job_id: str) -> None:
    state.ack_job(job_id)


def requeue() -> int:
    return state.requeue_processing()


def dead_letter(job_id: str) -> None:
    state.dead_letter(job_id)


def dead_jobs() -> list[str]:
    return state.dead_jobs()


def remove_dead(job_id: str) -> None:
    state.remove_dead(job_id)


def clear_dead() -> int:
    return state.clear_dead()
