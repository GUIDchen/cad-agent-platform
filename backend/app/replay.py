from .state import state

_replay_ttl = 600


def seen_before(key: str, ttl: int = _replay_ttl) -> bool:
    return not state.first_time(key, ttl)


def reset() -> None:
    state.reset_memory()
