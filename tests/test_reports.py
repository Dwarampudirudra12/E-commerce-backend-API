"""Sales report (M2 monitoring): admin-only aggregates."""
import app.services.fraud as fraud_svc
from tests._helpers import (add_to_cart, auth_h, checkout, login, make_product,
                            make_user_db, register, set_stock)


def test_sales_summary_admin_only(client, db):
    fraud_svc._model_bundle = {"model": None}
    try:
        register(client, "rs@s.com", role="SELLER")
        register(client, "rc@s.com")
        make_user_db(db, "ra@s.com", "ADMIN")
        st, ct, adm = login(client, "rs@s.com"), login(client, "rc@s.com"), login(client, "ra@s.com")
        p = make_product(client, st, sku="REP-1", price=20.0)
        set_stock(client, st, p["id"], 10)
        add_to_cart(client, ct, p["id"], 2)
        o = checkout(client, ct, key="rep-1").json()
        assert client.get("/api/v1/reports/sales/summary",
                          headers=auth_h(ct)).status_code == 403
        r = client.get("/api/v1/reports/sales/summary", headers=auth_h(adm))
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["orders"] >= 1 and body["revenue"] >= o["total"]
        assert "PENDING_PAYMENT" in body["by_status"]
    finally:
        fraud_svc.reset()


def test_metrics_endpoint_exposes_counters(client):
    client.get("/health/live")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text
