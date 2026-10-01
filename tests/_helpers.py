"""Shared M2 test helpers."""
from app.core.security import hash_password
from app.models.user import Role, User


def register(client, email, password="Password123!", full_name="T User", role="CUSTOMER"):
    return client.post("/api/v1/auth/register",
                       json={"email": email, "password": password,
                             "full_name": full_name, "role": role})


def login(client, email, password="Password123!"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def auth_h(token):
    return {"Authorization": f"Bearer {token['access_token']}"}


def make_user_db(db, email, role):
    r = db.query(Role).filter(Role.name == role).first()
    u = User(email=email, password_hash=hash_password("Password123!"),
             full_name=role, role=role, role_id=r.id if r else None, email_verified=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def make_product(client, seller_token, sku="T-001", name="Test Widget", price=24.99):
    r = client.post("/api/v1/products",
                    json={"sku": sku, "name": name, "description": "t", "price": price},
                    headers=auth_h(seller_token))
    assert r.status_code == 201, r.text
    return r.json()


def set_stock(client, seller_token, product_id, qty):
    inv = client.get(f"/api/v1/products/{product_id}/inventory",
                     headers=auth_h(seller_token)).json()[0]
    r = client.patch(f"/api/v1/products/{product_id}/inventory",
                     json={"on_hand": qty, "version": inv["version"]},
                     headers=auth_h(seller_token))
    assert r.status_code == 200, r.text
    return r.json()


def add_to_cart(client, cust_token, product_id, qty=1):
    r = client.post("/api/v1/cart/items",
                    json={"product_id": product_id, "quantity": qty},
                    headers=auth_h(cust_token))
    assert r.status_code == 201, r.text
    return r.json()


def checkout(client, cust_token, key="k-1", address=None, code=None):
    body = {"shipping_address": address or {"country": "US"}, "discount_code": code}
    return client.post("/api/v1/orders", json=body,
                       headers={**auth_h(cust_token), "Idempotency-Key": key})
