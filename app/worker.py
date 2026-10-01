"""Celery app + nightly jobs (doc 3.6/3.7, M3).

- beat schedule: nightly model retraining, daily ops report.
- Redis is the broker (docker service `redis`).
- Run: docker compose --profile jobs up worker beat
"""
import os

from celery import Celery
from celery.schedules import crontab

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery = Celery("ecom", broker=redis_url, backend=redis_url)
celery.conf.update(
    task_always_eager=os.environ.get("CELERY_EAGER", "") == "1",
    beat_schedule={
        "nightly-retrain": {"task": "ecom.retrain", "schedule": crontab(hour=2, minute=0)},
        "daily-ops-report": {"task": "ecom.daily_report", "schedule": crontab(hour=6, minute=0)},
    },
)


@celery.task(name="ecom.send_email")
def send_email_task(to: str, subject: str, body: str) -> str:
    from app.services.email_service import send_email
    send_email(to, subject, body)
    return f"sent to {to}"


@celery.task(name="ecom.retrain")
def retrain_task() -> dict:
    """Nightly retraining: promote only on validation improvement (doc 3.6)."""
    from app.ml.train import train
    import json
    prev = {}
    try:
        with open("app/ml/artifacts/fraud_metrics.json") as f:
            prev = json.load(f)
    except Exception:
        pass
    new = train(n=15000, tuned=True)
    if prev and new["roc_auc"] < prev.get("roc_auc", 0):
        return {"promoted": False, "roc_auc": new["roc_auc"], "prev": prev.get("roc_auc")}
    return {"promoted": True, **new}


@celery.task(name="ecom.daily_report")
def daily_report_task() -> dict:
    return {"ok": True, "note": "daily operations report (M3 stub -> Grafana + email in M4)"}
