import threading
import time
from collections import Counter

from .config import REDIS_URL


class StateStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._requests: Counter = Counter()
        self._duration_count = 0.0
        self._duration_sum = 0.0
        self._replay: dict[str, float] = {}
        self._rates: dict[str, list[float]] = {}
        self._queue: list[str] = []
        self._processing: list[str] = []
        self._dead: list[str] = []
        self.client = None
        if REDIS_URL:
            try:
                import redis
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("REDIS_URL 已配置但未安装 redis 包") from exc
            self.client = redis.from_url(REDIS_URL, decode_responses=True)

    def first_time(self, key: str, ttl: int = 600) -> bool:
        if self.client is not None:
            return bool(self.client.set(f"cad:replay:{key}", "1", nx=True, ex=ttl))
        now = time.time()
        with self._lock:
            for item, created in list(self._replay.items()):
                if now - created > ttl:
                    self._replay.pop(item, None)
            if key in self._replay:
                return False
            self._replay[key] = now
            return True

    def rate(self, key: str, limit: int, window: int) -> bool:
        if self.client is not None:
            full = f"cad:rate:{key}"
            count = self.client.incr(full)
            if count == 1:
                self.client.expire(full, window)
            return int(count) <= limit
        now = time.time()
        with self._lock:
            entries = [t for t in self._rates.get(key, []) if now - t < window]
            if len(entries) >= limit:
                self._rates[key] = entries
                return False
            entries.append(now)
            self._rates[key] = entries
            return True

    def push_job(self, job_id: str) -> None:
        if self.client is not None:
            self.client.rpush("cad:jobs", job_id)
            return
        with self._lock:
            self._queue.append(job_id)

    def pop_job(self, timeout: int = 5) -> str | None:
        if self.client is not None:
            return self.client.brpoplpush("cad:jobs", "cad:jobs:processing", timeout=timeout)
        with self._lock:
            if not self._queue:
                return None
            job_id = self._queue.pop(0)
            self._processing.append(job_id)
            return job_id

    def ack_job(self, job_id: str) -> None:
        if self.client is not None:
            self.client.lrem("cad:jobs:processing", 0, job_id)
            return
        with self._lock:
            if job_id in self._processing:
                self._processing.remove(job_id)

    def dead_letter(self, job_id: str) -> None:
        if self.client is not None:
            self.client.rpush("cad:jobs:dead", job_id)
            return
        with self._lock:
            self._dead.append(job_id)

    def remove_dead(self, job_id: str) -> None:
        if self.client is not None:
            self.client.lrem("cad:jobs:dead", 0, job_id)
            return
        with self._lock:
            if job_id in self._dead:
                self._dead.remove(job_id)

    def clear_dead(self) -> int:
        if self.client is not None:
            count = int(self.client.llen("cad:jobs:dead"))
            self.client.delete("cad:jobs:dead")
            return count
        with self._lock:
            count = len(self._dead)
            self._dead.clear()
            return count

    def dead_jobs(self) -> list[str]:
        if self.client is not None:
            return list(self.client.lrange("cad:jobs:dead", 0, 99))
        with self._lock:
            return list(self._dead)

    def requeue_processing(self) -> int:
        if self.client is not None:
            count = 0
            while True:
                item = self.client.rpoplpush("cad:jobs:processing", "cad:jobs")
                if not item:
                    break
                count += 1
            return count
        with self._lock:
            count = len(self._processing)
            self._queue.extend(self._processing)
            self._processing.clear()
            return count

    def record_request(self, method: str, path: str, status: int) -> None:
        field = f"{method}|{path}|{status}"
        if self.client is not None:
            self.client.hincrby("cad:metrics:requests", field, 1)
            return
        with self._lock:
            self._requests[field] += 1

    def add_duration(self, seconds: float) -> None:
        if self.client is not None:
            self.client.incrbyfloat("cad:metrics:duration_count", 1)
            self.client.incrbyfloat("cad:metrics:duration_sum", seconds)
            return
        with self._lock:
            self._duration_count += 1
            self._duration_sum += seconds

    def request_metrics(self) -> dict[str, int]:
        if self.client is not None:
            return {k: int(v) for k, v in self.client.hgetall("cad:metrics:requests").items()}
        with self._lock:
            return dict(self._requests)

    def duration_metrics(self) -> tuple[float, float]:
        if self.client is not None:
            values = self.client.mget("cad:metrics:duration_count", "cad:metrics:duration_sum")
            return float(values[0] or 0), float(values[1] or 0)
        with self._lock:
            return self._duration_count, self._duration_sum

    def healthy(self) -> bool:
        if self.client is None:
            return True
        try:
            return bool(self.client.ping())
        except Exception:  # noqa: BLE001
            return False

    def reset_memory(self) -> None:
        with self._lock:
            self._requests.clear()
            self._duration_count = 0.0
            self._duration_sum = 0.0
            self._replay.clear()
            self._rates.clear()


state = StateStore()
