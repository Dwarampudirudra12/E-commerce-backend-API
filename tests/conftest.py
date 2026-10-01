"""Pytest fixtures: isolated SQLite DB per test session, seeded roles."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_m1.db"
os.environ["APP_ENV"] = "test"  # bypasses rate limiting (M4)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import Role

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    for name in ("CUSTOMER", "SELLER", "SUPPORT", "ADMIN"):
        if not db.query(Role).filter(Role.name == name).first():
            db.add(Role(name=name, description=name))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    # Fresh tables per test (fast for M1 scale).
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    s = TestingSession()
    for name in ("CUSTOMER", "SELLER", "SUPPORT", "ADMIN"):
        s.add(Role(name=name, description=name))
    s.commit()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def client(db):
    def override():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
