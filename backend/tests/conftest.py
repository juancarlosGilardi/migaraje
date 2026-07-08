import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    Base.metadata.create_all(engine)
    yield TestClient(app)
    Base.metadata.drop_all(engine)


@pytest.fixture()
def auth_headers(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "juan@test.pe", "name": "Juan Carlos", "password": "clave-segura-123"},
    )
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
