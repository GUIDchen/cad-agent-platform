from app.session import sign_session, verify_session
from app.wecom import make_state, verify_state


def test_session_roundtrip():
    token = sign_session(7)
    assert verify_session(token) == 7


def test_session_tampered():
    token = sign_session(7)
    raw, sig = token.split(".")
    assert verify_session(raw + "." + ("0" * len(sig))) is None
    assert verify_session("bad") is None


def test_state_roundtrip():
    state = make_state()
    assert verify_state(state)
    assert not verify_state(state + "x")
    assert not verify_state("bad")
