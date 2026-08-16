from contextvars import ContextVar

support_url: ContextVar[str] = ContextVar("support_url", default="")
screen_ids: ContextVar[dict[str, str]] = ContextVar("screen_ids", default={})
