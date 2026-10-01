"""M1 health + DB table-count gate (>=12 tables)."""
from app.db.base import Base


def test_live(client):
    r = client.get("/health/live")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_ready_sqlite(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["checks"]["database"] == "up"


def test_schema_has_12_tables():
    assert len(Base.metadata.tables) >= 12, f"only {len(Base.metadata.tables)} tables"
