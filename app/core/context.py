from contextvars import ContextVar

# Variáveis de contexto da requisição atual
# ContextVar é thread-safe e coroutine-safe — perfeito para async
_current_user_id: ContextVar[int | None] = ContextVar("current_user_id", default=None)
_current_ip: ContextVar[str | None] = ContextVar("current_ip", default=None)


def set_current_user_id(user_id: int | None) -> None:
    _current_user_id.set(user_id)


def get_current_user_id() -> int | None:
    return _current_user_id.get()


def set_current_ip(ip: str | None) -> None:
    _current_ip.set(ip)


def get_current_ip() -> str | None:
    return _current_ip.get()