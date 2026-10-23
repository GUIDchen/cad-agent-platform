from contextvars import ContextVar

request_ip: ContextVar[str | None] = ContextVar("request_ip", default=None)
request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
