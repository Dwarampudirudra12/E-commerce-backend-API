"""Payments: webhook verification, dedupe, failure path, refunds + limits."""
import json

import pytest
import app.services.fraud as fraud_svc
from app.services.payment_gateway import sign_mock_webhook
from tests._helpers import (add_to_cart, auth_h, checkout, login, make_product,
                            make_user_db, register, set_stock)


@pytest.fixture(autouse=True)
def _rule_fraud():
    fraud_svc._model_bundle = {"model": None}
    yield
    fraud_svc.reset()


@pytest.fixture()
def paid(client, db):
    register(client, "ps@s.com", role="SELLER")
    register(client, "pc@s.com")
    make_user_db(db, "psup@s.com", "SUPPORT")
    make_user_db(db, "padm@s.com", "ADMIN")
    st, ct = login(client, "ps@s.com"), login(client, "pc@s.com")
    sup, adm = login(client, "psup@s.com"), login(client, "padm@s.com")
    p = make_product(client, st, sku="PAY-1", price=20.0)
    set_stock(client, st, p["id"], 10)
    add_to_cart(client, ct, p["id"], 2)  # subtotal 40 + tax 3.20 + ship 4 = 47.20
    o = checkout(client, ct, key="pay-1").json()
    pay = client.get(f"/api/v1/payments/by-order/{o['id']}",
                     headers=auth_h(ct)).json()
    return {"st": st, "ct": ct, "sup": sup, "adm": adm, "order": o,
            "pay": pay, "product": p}


def _post_webhook(client, payload: dict, sign: bool = True):
    body = json.dumps(payload, separators=(",", ":")).encode()
    headers = {"Content-Type": "application/json"}
    if sign:
        headers["X-Signature"] = sign_mock_webhook(body)
    return client.post("/api/v1/payments/webhook", content=body, headers=headers)


def test_webhook_success_marks_paid_and_commits_stock(client, paid):
    r = _post_webhook(client, {"event_id": "ev-1", "type": "payment.succeeded",
                               "gateway_ref": paid["pay"]["gateway_ref"],
                               "amount": paid["pay"]["amount"]})
    assert r.status_code == 200 and r.json()["status"] == "SUCCEEDED"
    o = client.get(f"/api/v1/orders/{paid['order']['id']}",
                   headers=auth_h(paid["ct"])).json()
    assert o["status"] == "PAID"
    inv = client.get(f"/api/v1/products/{paid['product']['id']}/inventory",
                     headers=auth_h(paid["st"])).json()[0]
    assert inv["on_hand"] == 8 and inv["reserved"] == 0  # 10 - 2 committed


def test_webhook_bad_signature_rejected(client, paid):
    assert _post_webhook(client, {"event_id": "ev-x", "type": "payment.succeeded",
                                  "gateway_ref": paid["pay"]["gateway_ref"],
                                  "amount": 1}, sign=False).status_code == 400
    body = json.dumps({"event_id": "ev-x", "type": "payment.succeeded"}).encode()
    r = client.post("/api/v1/payments/webhook", content=body,
                    headers={"X-Signature": "tampered", "Content-Type": "application/json"})
    assert r.status_code == 400


def test_webhook_duplicate_delivery_deduped(client, paid):
    payload = {"event_id": "ev-dup", "type": "payment.succeeded",
               "gateway_ref": paid["pay"]["gateway_ref"], "amount": paid["pay"]["amount"]}
    assert _post_webhook(client, payload).status_code == 200
    r = _post_webhook(client, payload)
    assert r.json().get("deduped") is True
    inv = client.get(f"/api/v1/products/{paid['product']['id']}/inventory",
                     headers=auth_h(paid["st"])).json()[0]
    assert inv["on_hand"] == 8  # committed exactly once


def test_webhook_failure_notifies_and_keeps_order(client, paid):
    r = _post_webhook(client, {"event_id": "ev-f", "type": "payment.failed",
                               "gateway_ref": paid["pay"]["gateway_ref"],
                               "amount": paid["pay"]["amount"]})
    assert r.json()["status"] == "FAILED"
    o = client.get(f"/api/v1/orders/{paid['order']['id']}",
                   headers=auth_h(paid["ct"])).json()
    assert o["status"] == "PENDING_PAYMENT"  # retryable


def test_idempotent_retry_returns_original_order(client, paid):
    from tests._helpers import checkout as co
    r1 = co(client, paid["ct"], key="pay-1")
    assert r1.status_code == 200
    assert r1.json()["id"] == paid["order"]["id"]


def test_support_refund_within_limit(client, paid, db):
    from app.services.payment_gateway import sign_mock_webhook as _s
    _post_webhook(client, {"event_id": "ev-r", "type": "payment.succeeded",
                           "gateway_ref": paid["pay"]["gateway_ref"],
                           "amount": paid["pay"]["amount"]})
    r = client.post(f"/api/v1/payments/{paid['pay']['id']}/refund",
                    json={"reason": "damaged"}, headers=auth_h(paid["sup"]))
    assert r.status_code == 200, r.text
    o = client.get(f"/api/v1/orders/{paid['order']['id']}",
                   headers=auth_h(paid["ct"])).json()
    assert o["status"] == "REFUNDED"
    inv = client.get(f"/api/v1/products/{paid['product']['id']}/inventory",
                     headers=auth_h(paid["st"])).json()[0]
    assert inv["on_hand"] == 10  # restocked


def test_support_refund_over_limit_needs_admin(client, db):
    register(client, "bs@s.com", role="SELLER")
    register(client, "bc@s.com")
    make_user_db(db, "bsup@s.com", "SUPPORT")
    make_user_db(db, "badm@s.com", "ADMIN")
    st, ct = login(client, "bs@s.com"), login(client, "bc@s.com")
    sup, adm = login(client, "bsup@s.com"), login(client, "badm@s.com")
    p = make_product(client, st, sku="BIG-1", price=200.0)
    set_stock(client, st, p["id"], 5)
    add_to_cart(client, ct, p["id"], 1)  # total > $100 limit
    o = checkout(client, ct, key="big-1").json()
    pay = client.get(f"/api/v1/payments/by-order/{o['id']}",
                     headers=auth_h(ct)).json()
    _post_webhook(client, {"event_id": "ev-big", "type": "payment.succeeded",
                           "gateway_ref": pay["gateway_ref"], "amount": pay["amount"]})
    r = client.post(f"/api/v1/payments/{pay['id']}/refund", json={},
                    headers=auth_h(sup))
    assert r.status_code == 403
    r = client.post(f"/api/v1/payments/{pay['id']}/refund", json={},
                    headers=auth_h(adm))
    assert r.status_code == 200


def test_customer_cannot_refund(client, paid):
    _post_webhook(client, {"event_id": "ev-nr", "type": "payment.succeeded",
                           "gateway_ref": paid["pay"]["gateway_ref"],
                           "amount": paid["pay"]["amount"]})
    r = client.post(f"/api/v1/payments/{paid['pay']['id']}/refund", json={},
                    headers=auth_h(paid["ct"]))
    assert r.status_code == 403
