"""Admin/ops read endpoints + test-mode payment confirmation."""
import pytest
import app.services.fraud as fraud_svc
from tests._helpers import (add_to_cart, auth_h, checkout, login, make_product,
                            make_user_db, register, set_stock)


@pytest.fixture(autouse=True)
def _rule_fraud():
    fraud_svc._model_bundle = {"model": None}
    yield
    fraud_svc.reset()


@pytest.fixture()
def ctx(client, db):
    register(client, "x@s.com", role="SELLER")
    register(client, "x@c.com")
    make_user_db(db, "x@sup.com", "SUPPORT")
    make_user_db(db, "x@adm.com", "ADMIN")
    st = login(client, "x@s.com")
    ct = login(client, "x@c.com")
    sup = login(client, "x@sup.com")
    adm = login(client, "x@adm.com")
    return {"st": st, "ct": ct, "sup": sup, "adm": adm}


def test_audit_logs_admin_only(client, ctx):
    assert client.get("/api/v1/audit-logs", headers=auth_h(ctx["ct"])).status_code == 403
    r = client.get("/api/v1/audit-logs", headers=auth_h(ctx["adm"]))
    assert r.status_code == 200 and r.json()["total"] >= 1
    r = client.get("/api/v1/audit-logs", params={"action": "user.login"},
                   headers=auth_h(ctx["adm"]))
    assert all("user.login" in a["action"] for a in r.json()["items"])


def test_refunds_and_payments_lists(client, ctx, db):
    p = make_product(client, ctx["st"], sku="OP-1", price=10.0)
    set_stock(client, ctx["st"], p["id"], 5)
    add_to_cart(client, ctx["ct"], p["id"], 1)
    o = checkout(client, ctx["ct"], key="ops-1").json()
    assert o["user_id"] is not None  # attribution for support lookup
    assert client.get("/api/v1/refunds", headers=auth_h(ctx["ct"])).status_code == 403
    assert client.get("/api/v1/refunds", headers=auth_h(ctx["sup"])).status_code == 200
    assert client.get("/api/v1/payments", headers=auth_h(ctx["sup"])).status_code == 200


def test_order_history_visibility(client, ctx, db):
    p = make_product(client, ctx["st"], sku="OP-2", price=10.0)
    set_stock(client, ctx["st"], p["id"], 5)
    add_to_cart(client, ctx["ct"], p["id"], 1)
    o = checkout(client, ctx["ct"], key="ops-2").json()
    r = client.get(f"/api/v1/orders/{o['id']}/history", headers=auth_h(ctx["ct"]))
    assert r.status_code == 200 and len(r.json()["items"]) >= 2
    make_user_db(db, "other@o.com", "CUSTOMER")
    ot = login(client, "other@o.com")
    assert client.get(f"/api/v1/orders/{o['id']}/history",
                      headers=auth_h(ot)).status_code == 403


def test_confirm_test_payment_flow(client, ctx):
    p = make_product(client, ctx["st"], sku="OP-3", price=10.0)
    set_stock(client, ctx["st"], p["id"], 5)
    add_to_cart(client, ctx["ct"], p["id"], 1)
    o = checkout(client, ctx["ct"], key="ops-3").json()
    r = client.post(f"/api/v1/payments/by-order/{o['id']}/confirm-test",
                    headers=auth_h(ctx["ct"]))
    assert r.status_code == 200 and r.json()["status"] == "SUCCEEDED"
    assert client.get(f"/api/v1/orders/{o['id']}",
                      headers=auth_h(ctx["ct"])).json()["status"] == "PAID"
    # second call dedupes
    assert client.post(f"/api/v1/payments/by-order/{o['id']}/confirm-test",
                       headers=auth_h(ctx["ct"])).json().get("deduped") is True
