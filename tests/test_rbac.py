"""RBAC: 4 roles enforced (doc permission matrix p3)."""
from app.core.security import hash_password
from app.models.user import Role, User


def _make(db, email, role):
    r = db.query(Role).filter(Role.name == role).first()
    u = User(email=email, password_hash=hash_password("Password123!"),
             full_name=role, role=role, role_id=r.id if r else None, email_verified=True)
    db.add(u)
    db.commit()
    return u


def _token(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def test_admin_can_list_users_customer_cannot(client, db):
    _make(db, "cust@e.com", "CUSTOMER")
    _make(db, "adm@e.com", "ADMIN")
    ct, at = _token(client, "cust@e.com"), _token(client, "adm@e.com")
    assert client.get("/api/v1/users", headers=_auth(ct)).status_code == 403
    r = client.get("/api/v1/users", headers=_auth(at))
    assert r.status_code == 200 and len(r.json()) >= 2


def test_admin_can_promote_to_support(client, db):
    _make(db, "cust@e.com", "CUSTOMER")
    _make(db, "adm@e.com", "ADMIN")
    at = _token(client, "adm@e.com")
    users = client.get("/api/v1/users", headers=_auth(at)).json()
    cid = next(u["id"] for u in users if u["email"] == "cust@e.com")
    r = client.patch(f"/api/v1/users/{cid}/role", json={"role": "SUPPORT"}, headers=_auth(at))
    assert r.status_code == 200 and r.json()["role"] == "SUPPORT"


def test_unauthenticated_me_401(client):
    assert client.get("/api/v1/users/me").status_code == 401
