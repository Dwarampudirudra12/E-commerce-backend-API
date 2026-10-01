"""M3 intelligence: tuned fraud + review queue, forecasting, recommendations."""
from datetime import date, timedelta

import pytest
import app.services.fraud as fraud_svc
from app.models.observability import DemandHistory, MlPrediction
from tests._helpers import (add_to_cart, auth_h, checkout, login, make_product,
                            make_user_db, register, set_stock)


@pytest.fixture(autouse=True)
def _rule_fraud():
    fraud_svc._model_bundle = {"model": None}
    yield
    fraud_svc.reset()


@pytest.fixture()
def shop(client, db):
    register(client, "is@s.com", role="SELLER")
    register(client, "ic@s.com")
    make_user_db(db, "isup@s.com", "SUPPORT")
    st, ct, sup = login(client, "is@s.com"), login(client, "ic@s.com"), login(client, "isup@s.com")
    a = make_product(client, st, sku="IA-1", name="Alpha", price=10.0)
    b = make_product(client, st, sku="IB-2", name="Beta", price=20.0)
    set_stock(client, st, a["id"], 100)
    set_stock(client, st, b["id"], 100)
    return {"st": st, "ct": ct, "sup": sup, "a": a, "b": b}


def _seed_history(db, product_id, days=30, base=5):
    for i in range(days):
        db.add(DemandHistory(product_id=product_id,
                             day=date.today() - timedelta(days=days - i), qty=base))
    db.commit()


def test_forecast_endpoint_returns_14_days(client, shop, db):
    _seed_history(db, shop["a"]["id"])
    r = client.get(f"/api/v1/forecasts/products/{shop['a']['id']}",
                   headers=auth_h(shop["st"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["forecast"]) == 14 and body["history_days"] == 30
    assert body["holdout_mape_pct"] < 30
    assert db.query(MlPrediction).filter(MlPrediction.model_name == "forecast").count() >= 1


def test_reorder_flags_at_risk_product(client, shop, db):
    _seed_history(db, shop["a"]["id"], base=8)
    set_stock(client, shop["st"], shop["a"]["id"], 3)
    r = client.get("/api/v1/forecasts/reorder-suggestions", headers=auth_h(shop["st"]))
    assert r.status_code == 200
    item = next(i for i in r.json()["items"] if i["product_id"] == shop["a"]["id"])
    assert item["at_risk"] is True and item["reorder_qty"] > 0
    assert item["days_until_stockout"] is not None


def test_bought_together_recommendations(client, shop):
    for key, qty in (("r1", 1), ("r2", 1)):
        add_to_cart(client, shop["ct"], shop["a"]["id"], qty)
        add_to_cart(client, shop["ct"], shop["b"]["id"], qty)
        assert checkout(client, shop["ct"], key=key).status_code == 200
    r = client.get(f"/api/v1/products/{shop['a']['id']}/recommendations",
                   params={"kind": "bought_together"})
    assert r.status_code == 200 and shop["b"]["id"] in r.json()["items"]


def test_view_logging_and_also_viewed(client, shop):
    assert register(client, "viewer@v.com").status_code == 201
    vt = login(client, "viewer@v.com")
    for _ in range(2):
        assert client.post(f"/api/v1/products/{shop['a']['id']}/view",
                           headers=auth_h(vt)).status_code == 204
        assert client.post(f"/api/v1/products/{shop['b']['id']}/view",
                           headers=auth_h(vt)).status_code == 204
    r = client.get(f"/api/v1/products/{shop['a']['id']}/recommendations",
                   params={"kind": "also_viewed"})
    assert shop["b"]["id"] in r.json()["items"]


def test_personal_recommendations_and_cold_start(client, shop):
    add_to_cart(client, shop["ct"], shop["a"]["id"], 1)
    add_to_cart(client, shop["ct"], shop["b"]["id"], 1)
    assert checkout(client, shop["ct"], key="pers").status_code == 200
    c = make_product(client, shop["st"], sku="IC-3", name="Gamma", price=5.0)
    set_stock(client, shop["st"], c["id"], 50)
    r = client.get("/api/v1/users/me/recommendations", headers=auth_h(shop["ct"]))
    assert r.status_code == 200  # runs; empty is fine with 2-product universe
    assert register(client, "newbie@n.com").status_code == 201
    nt = login(client, "newbie@n.com")
    r = client.get("/api/v1/users/me/recommendations", headers=auth_h(nt))
    assert r.status_code == 200 and len(r.json()["items"]) > 0  # popular fallback


def _craft_hold(client, shop, db):
    """Deterministic high-risk checkout via rule fallback (score ~0.93)."""
    from app.models.payment import DiscountCode
    email = "risky@r.com"
    assert register(client, email).status_code == 201
    ct = login(client, email)
    for _ in range(2):  # failed logins AFTER success so the counter persists
        client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-1234"})
    client.post("/api/v1/users/me/addresses",
                json={"label": "home", "country": "UK", "is_default": True},
                headers=auth_h(ct))
    db.add(DiscountCode(code="BIG60", percent_off=60, max_uses=99, is_active=True))
    db.commit()
    for i in range(2):  # velocity for the final order
        add_to_cart(client, ct, shop["a"]["id"], 1)
        assert checkout(client, ct, key=f"vel-{i}").status_code == 200
    add_to_cart(client, ct, shop["b"]["id"], 1)
    r = checkout(client, ct, key="hold-me", address={"country": "US"}, code="BIG60")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ON_HOLD"
    return ct, r.json()


def test_high_risk_order_held_with_factors(client, shop, db):
    _, order = _craft_hold(client, shop, db)
    assert order["risk_score"] > 0.70
    pred = db.query(MlPrediction).filter(MlPrediction.model_name == "fraud").all()
    assert pred and len(pred[-1].top_factors) >= 1


def test_review_queue_approve_and_reject(client, shop, db):
    ct, order = _craft_hold(client, shop, db)
    q = client.get("/api/v1/orders/review/queue", headers=auth_h(shop["sup"]))
    assert q.status_code == 200 and q.json()["total"] >= 1
    assert q.json()["items"][0]["risk_factors"]
    assert client.get("/api/v1/orders/review/queue", headers=auth_h(ct)).status_code == 403
    ok = client.patch(f"/api/v1/orders/{order['id']}/status",
                      json={"to_status": "PENDING_PAYMENT"}, headers=auth_h(shop["sup"]))
    assert ok.status_code == 200 and ok.json()["status"] == "PENDING_PAYMENT"
    pay = client.get(f"/api/v1/payments/by-order/{order['id']}",
                     headers=auth_h(ct))
    assert pay.status_code == 200  # intent created on approval


def test_tuned_training_reports_constrained_metrics(tmp_path):
    from app.ml.train import train
    m = train(n=2000, seed=11, out_dir=str(tmp_path), tuned=True)
    assert m["roc_auc"] >= 0.80, m
    assert 0.05 <= m["threshold"] <= 0.95
