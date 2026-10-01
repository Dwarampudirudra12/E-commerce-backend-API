"""M3 analytics: KPIs, trends, top products, fraud distribution, CSV export."""
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
def data(client, db):
    register(client, "as@s.com", role="SELLER")
    register(client, "ac@s.com")
    make_user_db(db, "aa@s.com", "ADMIN")
    st, ct, adm = login(client, "as@s.com"), login(client, "ac@s.com"), login(client, "aa@s.com")
    p = make_product(client, st, sku="AN-1", price=20.0)
    set_stock(client, st, p["id"], 50)
    add_to_cart(client, ct, p["id"], 2)
    o = checkout(client, ct, key="an-1").json()
    return {"st": st, "ct": ct, "adm": adm, "p": p, "order": o}


def test_overview_kpis_admin_and_seller_scope(client, data, db):
    r = client.get("/api/v1/reports/sales/summary", headers=auth_h(data["adm"]))
    assert r.status_code == 200 and r.json()["orders"] >= 1
    assert r.json()["revenue"] >= data["order"]["total"]
    r = client.get("/api/v1/reports/sales/summary", headers=auth_h(data["st"]))
    assert r.status_code == 200 and r.json()["orders"] >= 1  # own product
    make_user_db(db, "other-seller@o.com", "SELLER")
    assert client.get("/api/v1/reports/sales/summary",
                      headers=auth_h(login(client, "other-seller@o.com"))
                      ).json()["orders"] == 0  # nothing of theirs sold


def test_revenue_trend_top_products_fraud_dist(client, data):
    assert client.get("/api/v1/reports/revenue-trend",
                      headers=auth_h(data["adm"])).json()["points"]
    top = client.get("/api/v1/reports/top-products", headers=auth_h(data["adm"])).json()
    assert top["items"] and top["items"][0]["product_id"] == data["p"]["id"]
    dist = client.get("/api/v1/reports/fraud-distribution",
                      headers=auth_h(data["adm"])).json()
    assert sum(dist.values()) >= 1  # checkout scored this order


def test_csv_exports(client, data):
    r = client.get("/api/v1/reports/export.csv?kind=orders", headers=auth_h(data["adm"]))
    assert r.status_code == 200 and r.text.splitlines()[0].startswith("id,order_number")
    assert data["order"]["order_number"] in r.text
    r = client.get("/api/v1/reports/export.csv?kind=products", headers=auth_h(data["st"]))
    assert "AN-1" in r.text


def test_seller_cannot_use_admin_only(client, data):
    assert client.get("/api/v1/reports/fraud-distribution",
                      headers=auth_h(data["st"])).status_code == 403
