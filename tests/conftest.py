import os
import tempfile

tmp = tempfile.mkdtemp(prefix="cad-platform-test-")
os.environ["DATA_DIR"] = tmp
os.environ["STORAGE_DIR"] = os.path.join(tmp, "storage")
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/test.db"
os.environ["EXECUTION_MODE"] = "inline"
os.environ["ALLOW_DEV_AUTH"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.replay import reset as reset_replay  # noqa: E402
from app.seed import seed  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_state(client):
    db = SessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    seed()
    reset_replay()
    client.cookies.clear()
    yield


def headers(name: str) -> dict:
    return {"X-User": name}
