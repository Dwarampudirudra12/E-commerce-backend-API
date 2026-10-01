"""Catalog + inventory: RBAC, search, caching, optimistic inventory, uploads."""
import pytest
import app.services.fraud as fraud_svc
from tests._helpers import auth_h, login, make_product, register, set_stock


@pytest.fixture(autouse=True)
def _no_redis_and_rule_fraud(monkeypatch):
    import app.core.cache as cache
    monkeypatch.setattr(cache, "_get_client", lambda: None)
    fraud_svc._model_bundle = {"model": None}
    yield
    fraud_svc.reset()


def _seller(client, email="seller@t.com"):
    assert register(client, email, role="SELLER").status_code == 201
    return login(client, email)


def test_seller_creates_product_and_admin_category(client, db):
    from app.core.security import hash_password
    from app.models.user import Role, User
    r = db.query(Role).filter(Role.name == "ADMIN").first()
    db.add(User(email="adm@t.com", password_hash=hash_password("Password123!"),
                full_name="A", role="ADMIN", role_id=r.id, email_verified=True))
    db.commit()
    at = login(client, "adm@t.com")["access_token"]
    c = client.post("/api/v1/categories", json={"name": "Gadgets"},
                    headers={"Authorization": f"Bearer {at}"})
    assert c.status_code == 201, c.text
    st = _seller(client)
    p = make_product(client, st)
    assert p["on_hand"] == 0 and p["seller_id"] is not None


def test_duplicate_sku_409(client):
    st = _seller(client)
    make_product(client, st, sku="DUP-1")
    r = client.post("/api/v1/products", json={"sku": "DUP-1", "name": "x", "price": 5},
                    headers=auth_h(st))
    assert r.status_code == 409


def test_guest_can_browse_and_search(client):
    st = _seller(client)
    make_product(client, st, sku="B-1", name="Blue Hammer", price=10.0)
    assert client.get("/api/v1/products").status_code == 200
    r = client.get("/api/v1/products/search", params={"q": "hammer"})
    assert r.status_code == 200 and r.json()["total"] == 1
    r = client.get("/api/v1/products/search",
                   params={"q": "hammer", "min_price": 100})
    assert r.json()["total"] == 0


def test_search_pagination_and_sort(client):
    st = _seller(client)
    for i in range(5):
        make_product(client, st, sku=f"P-{i}", name=f"Gizmo {i}", price=5.0 + i)
    r = client.get("/api/v1/products/search",
                   params={"q": "gizmo", "page": 2, "page_size": 2,
                           "sort": "price", "order": "desc"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5 and body["page"] == 2 and len(body["items"]) == 2
    assert body["items"][0]["price"] > body["items"][1]["price"]


def test_customer_cannot_create_product(client):
    assert register(client, "c@t.com").status_code == 201
    ct = login(client, "c@t.com")
    r = client.post("/api/v1/products", json={"sku": "X-1", "name": "x", "price": 5},
                    headers=auth_h(ct))
    assert r.status_code == 403


def test_seller_cannot_edit_others_product(client):
    a = _seller(client, "a@t.com")
    b = _seller(client, "b@t.com")
    p = make_product(client, a, sku="A-1")
    r = client.patch(f"/api/v1/products/{p['id']}", json={"price": 1.0},
                     headers=auth_h(b))
    assert r.status_code == 403


def test_inventory_update_and_stale_version_409(client):
    st = _seller(client)
    p = make_product(client, st)
    set_stock(client, st, p["id"], 50)
    inv = client.get(f"/api/v1/products/{p['id']}/inventory",
                     headers=auth_h(st)).json()[0]
    assert inv["on_hand"] == 50
    r = client.patch(f"/api/v1/products/{p['id']}/inventory",
                     json={"on_hand": 60, "version": inv["version"] - 1},
                     headers=auth_h(st))
    assert r.status_code == 409


def test_inventory_below_reserved_rejected(client):
    st = _seller(client)
    p = make_product(client, st)
    set_stock(client, st, p["id"], 5)
    assert register(client, "c2@t.com").status_code == 201
    ct = login(client, "c2@t.com")
    client.post("/api/v1/cart/items", json={"product_id": p["id"], "quantity": 3},
                headers=auth_h(ct))
    from tests._helpers import checkout
    assert checkout(client, ct, key="inv-k").status_code == 200
    inv = client.get(f"/api/v1/products/{p['id']}/inventory",
                     headers=auth_h(st)).json()[0]
    assert inv["reserved"] == 3
    r = client.patch(f"/api/v1/products/{p['id']}/inventory",
                     json={"on_hand": 2, "version": inv["version"]},
                     headers=auth_h(st))
    assert r.status_code == 422


def test_image_upload_local(client):
    st = _seller(client)
    p = make_product(client, st)
    r = client.post(f"/api/v1/products/{p['id']}/images",
                    files={"file": ("pic.png", b"fakepng-bytes", "image/png")},
                    headers=auth_h(st))
    assert r.status_code == 201, r.text
    assert r.json()["url"].startswith("/uploads/")


def test_product_detail_cached_path(client):
    st = _seller(client)
    p = make_product(client, st)
    assert client.get(f"/api/v1/products/{p['id']}").status_code == 200
    assert client.get(f"/api/v1/products/{p['id']}").status_code == 200
    assert client.get("/api/v1/products/999999").status_code == 404
