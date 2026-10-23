
from app.queue import ack, dequeue, enqueue, requeue


def test_queue_ack_and_requeue():
    from app.state import state

    state.reset_memory()
    enqueue("job-a")
    job_id = dequeue(0)
    assert job_id == "job-a"
    requeue()
    assert dequeue(0) == "job-a"
    ack("job-a")
    assert dequeue(0) is None
