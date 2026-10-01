"""Cart + checkout: totals math, 409 short-stock, state machine, cancel release."""
import pytest
import app.services.fraud as fraud_svc
from tests._helpers import (add_to_cart, auth_h, checkout, login, make_product,
                            register, set_stock)


@pytest.fixture(autouse=True)
def _rule_fraud():
    fraud_svc._model_bundle = {"model": None}
    yield
    fraud_svc.reset()


@pytest.fixture()
def shop(client):
    assert register(client, "seller@s.com", role="SELLER").status_code == 201
    assert register(client, "cust@s.com").status_code == 201
    st, ct = login(client, "seller@s.com"), login(client, "cust@s.com")
    mouse = make_product(client, st, sku="WM-204", name="Wireless Mouse", price=24.99)
    cable = make_product(client, st, sku="UC-110", name="USB-C Cable", price=9.50)
    set_stock(client, st, mouse["id"], 38)
    set_stock(client, st, cable["id"], 120)
    return {"st": st, "ct": ct, "mouse": mouse, "cable": cable}


def test_cart_crud(client, shop):
    add_to_cart(client, shop["ct"], shop["mouse"]["id"], 2)
    items = client.get("/api/v1/cart", headers=auth_h(shop["ct"])).json()
    assert len(items) == 1 and items[0]["quantity"] == 2
    item_id = items[0]["id"]
    r = client.patch(f"/api/v1/cart/items/{item_id}?quantity=3",
                     headers=auth_h(shop["ct"]))
    assert r.status_code == 200 and r.json()["quantity"] == 3
    assert client.delete(f"/api/v1/cart/items/{item_id}",
                         headers=auth_h(shop["ct"])).status_code == 204
    assert client.get("/api/v1/cart", headers=auth_h(shop["ct"])).json() == []


def test_checkout_math_matches_doc_example(client, shop):
    # 1 x 24.99 + 2 x 9.50 = 43.99 + 8% tax (3.52) + $4 shipping = $51.51
    add_to_cart(client, shop["ct"], shop["mouse"]["id"], 1)
    add_to_cart(client, shop["ct"], shop["cable"]["id"], 2)
    r = checkout(client, shop["ct"], key="doc-example")
    assert r.status_code == 200, r.text
    o = r.json()
    assert o["status"] == "PENDING_PAYMENT"
    assert o["subtotal"] == 43.99 and o["tax"] == 3.52 and o["shipping"] == 4.0
    assert o["total"] == 51.51 and o["order_number"].startswith("ORD-")
    assert client.get("/api/v1/cart", headers=auth_h(shop["ct"])).json() == []


def test_checkout_empty_cart_400(client, shop):
    assert checkout(client, shop["ct"], key="empty").status_code == 400


def test_checkout_missing_idempotency_key_422(client, shop):
    add_to_cart(client, shop["ct"], shop["mouse"]["id"], 1)
    r = client.post("/api/v1/orders", json={"shipping_address": {}},
                    headers=auth_h(shop["ct"]))
    assert r.status_code == 422


def test_insufficient_stock_409_and_nothing_reserved(client, shop):
    from tests._helpers import add_to_cart as _add
    p = make_product(client, shop["st"], sku="LOW-1", price=5.0)
    set_stock(client, shop["st"], p["id"], 2)
    _add(client, shop["ct"], p["id"], 5)
    r = checkout(client, shop["ct"], key="short")
    assert r.status_code == 409
    inv = client.get(f"/api/v1/products/{p['id']}/inventory",
                     headers=auth_h(shop["st"])).json()[0]
    assert inv["reserved"] == 0 and inv["on_hand"] == 2


def test_checkout_with_discount_code(client, shop, db):
    from app.models.payment import DiscountCode
    db.add(DiscountCode(code="T10", percent_off=10, max_uses=5, is_active=True))
    db.commit()
    add_to_cart(client, shop["ct"], shop["mouse"]["id"], 1)
    r = checkout(client, shop["ct"], key="disc", code="T10")
    assert r.status_code == 200, r.text
    assert r.json()["discount"] == 2.5  # 10% of 24.99


def test_invalid_discount_code_400(client, shop):
    add_to_cart(client, shop["ct"], shop["mouse"]["id"], 1)
    assert checkout(client, shop["ct"], key="baddisc", code="NOPE").status_code == 400


def test_customer_lists_own_orders_only(client, shop, db):
    from tests._helpers import make_user_db
    make_user_db(db, "other@o.com", "CUSTOMER")
    add_to_cart(client, shop["ct"], shop["mouse"]["id"], 1)
    checkout(client, shop["ct"], key="mine")
    mine = client.get("/api/v1/orders", headers=auth_h(shop["ct"])).json()
    assert mine["total"] == 1
    ot = login(client, "other@o.com")
    assert client.get("/api/v1/orders", headers=auth_h(ot)).json()["total"] == 0
    oid = mine["items"][0]["id"]
    assert client.get(f"/api/v1/orders/{oid}", headers=auth_h(ot)).status_code == 403


def test_customer_cancel_releases_stock(client, shop):
    add_to_cart(client, shop["ct"], shop["mouse"]["id"], 2)
    oid = checkout(client, shop["ct"], key="cancelme").json()["id"]
    r = client.patch(f"/api/v1/orders/{oid}/status", json={"to_status": "CANCELLED"},
                     headers=auth_h(shop["ct"]))
    assert r.status_code == 200 and r.json()["status"] == "CANCELLED"
    inv = client.get(f"/api/v1/products/{shop['mouse']['id']}/inventory",
                     headers=auth_h(shop["st"])).json()[0]
    assert inv["reserved"] == 0 and inv["on_hand"] == 38


def test_illegal_transition_rejected(client, shop):
    add_to_cart(client, shop["ct"], shop["mouse"]["id"], 1)
    oid = checkout(client, shop["ct"], key="badtrans").json()["id"]
    r = client.patch(f"/api/v1/orders/{oid}/status", json={"to_status": "DELIVERED"},
                     headers=auth_h(shop["ct"]))
    assert r.status_code == 422


def test_manual_paid_rejected_use_webhook(client, shop, db):
    from tests._helpers import make_user_db
    make_user_db(db, "sup@s.com", "SUPPORT")
    sup = login(client, "sup@s.com")
    add_to_cart(client, shop["ct"], shop["mouse"]["id"], 1)
    oid = checkout(client, shop["ct"], key="nomanual").json()["id"]
    r = client.patch(f"/api/v1/orders/{oid}/status", json={"to_status": "PAID"},
                     headers=auth_h(sup))
    assert r.status_code == 422


def test_support_advances_and_audit_written(client, shop, db):
    from tests._helpers import make_user_db
    from app.models.observability import AuditLog
    make_user_db(db, "sup2@s.com", "SUPPORT")
    sup = login(client, "sup2@s.com")
    from tests._helpers import checkout as co
    from app.services.payment_gateway import sign_mock_webhook
    import json as _json
    add_to_cart(client, shop["ct"], shop["mouse"]["id"], 1)
    o = checkout(client, shop["ct"], key="adv").json()
    pay = client.get(f"/api/v1/payments/by-order/{o['id']}",
                     headers=auth_h(shop["ct"])).json()
    body = _json.dumps({"event_id": "ev-adv", "type": "payment.succeeded",
                        "gateway_ref": pay["gateway_ref"], "amount": pay["amount"]},
                       separators=(",", ":")).encode()
    client.post("/api/v1/payments/webhook", content=body,
                headers={"X-Signature": sign_mock_webhook(body),
                         "Content-Type": "application/json"})
    r = client.patch(f"/api/v1/orders/{o['id']}/status", json={"to_status": "PACKED"},
                     headers=auth_h(sup))
    assert r.status_code == 200 and r.json()["status"] == "PACKED"
    assert db.query(AuditLog).filter(AuditLog.action == "order.status_packed").count() >= 1
