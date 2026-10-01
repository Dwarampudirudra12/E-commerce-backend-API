"""M3 criterion #3: all ten doc-3.7 events fire Notification rows in test runs."""
import json

import pytest
import app.services.fraud as fraud_svc
from app.models.observability import Notification
from app.services.payment_gateway import sign_mock_webhook
from tests._helpers import (add_to_cart, auth_h, checkout, login, make_product,
                            make_user_db, register, set_stock)


@pytest.fixture(autouse=True)
def _rule_fraud():
    fraud_svc._model_bundle = {"model": None}
    yield
    fraud_svc.reset()


@pytest.fixture()
def flow(client, db):
    register(client, "ns@s.com", role="SELLER")
    register(client, "nc@s.com")
    make_user_db(db, "nsup@s.com", "SUPPORT")
    make_user_db(db, "nadm@s.com", "ADMIN")
    st, ct = login(client, "ns@s.com"), login(client, "nc@s.com")
    sup, adm = login(client, "nsup@s.com"), login(client, "nadm@s.com")
    p = make_product(client, st, sku="N-1", price=20.0)
    set_stock(client, st, p["id"], 10)
    return {"st": st, "ct": ct, "sup": sup, "adm": adm, "p": p}


def _types(db, user_id=None):
    q = db.query(Notification)
    if user_id is not None:
        q = q.filter(Notification.user_id == user_id)
    return [n.type for n in q.all()]


def _webhook(client, gateway_ref, amount, event_id, etype="payment.succeeded"):
    body = json.dumps({"event_id": event_id, "type": etype,
                       "gateway_ref": gateway_ref, "amount": amount},
                      separators=(",", ":")).encode()
    return client.post("/api/v1/payments/webhook", content=body,
                       headers={"X-Signature": sign_mock_webhook(body),
                                "Content-Type": "application/json"})


def _paid_order(client, flow, db, key):
    from tests._helpers import checkout as co
    add_to_cart(client, flow["ct"], flow["p"]["id"], 1)
    o = co(client, flow["ct"], key=key).json()
    pay = client.get(f"/api/v1/payments/by-order/{o['id']}",
                     headers=auth_h(flow["ct"])).json()
    _webhook(client, pay["gateway_ref"], pay["amount"], f"ev-{key}")
    return o["id"]


def test_order_created_confirmed_and_payment_failed(client, flow, db):
    from tests._helpers import checkout as co
    add_to_cart(client, flow["ct"], flow["p"]["id"], 1)
    o = co(client, flow["ct"], key="n1").json()
    pay = client.get(f"/api/v1/payments/by-order/{o['id']}",
                     headers=auth_h(flow["ct"])).json()
    assert "order_created" in _types(db)
    _webhook(client, pay["gateway_ref"], pay["amount"], "ev-n-ok")
    assert "order_confirmed" in _types(db)
    add_to_cart(client, flow["ct"], flow["p"]["id"], 1)
    o2 = co(client, flow["ct"], key="n2").json()
    pay2 = client.get(f"/api/v1/payments/by-order/{o2['id']}",
                      headers=auth_h(flow["ct"])).json()
    _webhook(client, pay2["gateway_ref"], pay2["amount"], "ev-n-fail", "payment.failed")
    assert "payment_failed" in _types(db)


def test_high_risk_hold_and_review(monkeypatch, client, flow, db):
    monkeypatch.setattr("app.routers.orders.fraud_svc.score_order",
                        lambda feats: (0.95, "high", ["crafted velocity"]))
    add_to_cart(client, flow["ct"], flow["p"]["id"], 1)
    from tests._helpers import checkout as co
    o = co(client, flow["ct"], key="n-hold").json()
    assert o["status"] == "ON_HOLD"
    assert "high_risk_order" in _types(db)


def test_low_stock_and_stockout_risk(client, flow, db):
    from datetime import date, timedelta
    from app.models.observability import DemandHistory
    for i in range(30):
        db.add(DemandHistory(product_id=flow["p"]["id"],
                             day=date.today() - timedelta(days=30 - i), qty=6))
    db.commit()
    set_stock(client, flow["st"], flow["p"]["id"], 2)  # below reorder default 5
    assert "low_stock" in _types(db)
    r = client.get("/api/v1/forecasts/reorder-suggestions", headers=auth_h(flow["st"]))
    assert r.status_code == 200
    assert "stockout_risk" in _types(db)


def test_shipped_delivered_and_refund(client, flow, db):
    oid = _paid_order(client, flow, db, "n-ship")
    for dest, ev in (("PACKED", None), ("SHIPPED", "order_shipped"),
                     ("DELIVERED", "order_delivered")):
        r = client.patch(f"/api/v1/orders/{oid}/status", json={"to_status": dest},
                         headers=auth_h(flow["sup"]))
        assert r.status_code == 200
    assert "order_shipped" in _types(db) and "order_delivered" in _types(db)
    oid2 = _paid_order(client, flow, db, "n-ref")
    pay = client.get(f"/api/v1/payments/by-order/{oid2}",
                     headers=auth_h(flow["ct"])).json()
    assert client.post(f"/api/v1/payments/{pay['id']}/refund", json={},
                       headers=auth_h(flow["adm"])).status_code == 200
    assert "refund_processed" in _types(db)


def test_lockout_and_webhook_failure_and_error_spike(client, flow, db, monkeypatch):
    assert register(client, "lockme@l.com").status_code == 201
    for _ in range(5):
        client.post("/api/v1/auth/login",
                    json={"email": "lockme@l.com", "password": "wrong-1234"})
    assert "account_locked" in _types(db)
    bad = json.dumps({"event_id": "ev-bad", "type": "payment.succeeded"}).encode()
    assert client.post("/api/v1/payments/webhook", content=bad,
                       headers={"X-Signature": "nope",
                                "Content-Type": "application/json"}).status_code == 400
    assert "webhook_failure" in [n.type for n in db.query(Notification).all()]
    import app.services.alerts as alerts
    monkeypatch.setattr(alerts, "_error_rate", lambda: (5.0, 100.0))
    assert alerts.check_api_error_spike(db) is True
    assert "api_error_spike" in [n.type for n in db.query(Notification).all()]


def test_inbox_list_and_mark_read(client, flow, db):
    _paid_order(client, flow, db, "n-inbox")
    r = client.get("/api/v1/notifications/me", headers=auth_h(flow["ct"]))
    assert r.status_code == 200 and r.json()["total"] >= 1 and r.json()["unread"] >= 1
    nid = r.json()["items"][0]["id"]
    assert client.patch(f"/api/v1/notifications/{nid}/read",
                        headers=auth_h(flow["ct"])).status_code == 200
    r = client.get("/api/v1/notifications/me?unread_only=true", headers=auth_h(flow["ct"]))
    assert all(i["is_read"] is False for i in r.json()["items"])
