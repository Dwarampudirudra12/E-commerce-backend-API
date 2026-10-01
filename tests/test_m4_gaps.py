"""M4 coverage-gap closers: model-loaded fraud, worker, templates, auth cycles,
user endpoints, edge branches. Keeps the suite comfortably above 80%."""
import json

import jwt as pyjwt
import pytest
import app.services.fraud as fraud_svc
from app.core.deps import RequireAdmin, require_capability, require_roles
from app.models.user import User
from tests._helpers import (add_to_cart, auth_h, checkout, login, make_product,
                            make_user_db, register, set_stock)


@pytest.fixture(autouse=True)
def _reset_fraud():
    yield
    fraud_svc.reset()


# ---------- fraud with a real (tiny) model: ablation path ----------
def test_model_scoring_with_ablation_factors(tmp_path, monkeypatch):
    from app.ml.train import train
    train(n=1200, seed=5, out_dir=str(tmp_path))
    monkeypatch.setattr(fraud_svc, "MODEL_PATH", str(tmp_path / "fraud_model.joblib"))
    fraud_svc.reset()
    score, label, factors = fraud_svc.score_order(
        {"amount": 900, "item_count": 9, "discount_ratio": 0.6,
         "account_age_days": 0.2, "hours_since_last_order": 0.5,
         "orders_last_hour": 4, "failed_payments": 3,
         "country_mismatch": 1, "new_device": 1, "hour_of_day": 2})
    assert label == "high" and score > 0.5 and len(factors) >= 1


# ---------- templates + worker ----------
def test_templates_render_all_events():
    from app.services.templates import TEMPLATES, render
    for ev in TEMPLATES:
        s, b = render(ev, {"order_number": "1", "name": "N", "amount": 5,
                           "order_id": 1, "score": 0.9, "sku": "S",
                           "available": 1, "reorder_level": 5, "days": 2, "qty": 3})
        assert s and b
    assert render("unknown-event", {})[0] == "unknown-event"


def test_worker_tasks(monkeypatch):
    import app.worker as w
    assert w.send_email_task.run("a@b.c", "s", "b") == "sent to a@b.c"
    assert w.daily_report_task.run()["ok"] is True
    monkeypatch.setattr("app.ml.train.train", lambda **k: {"roc_auc": 0.999})
    assert w.retrain_task.run()["promoted"] is True


# ---------- auth full cycles ----------
def test_verify_email_cycle(client, db):
    from datetime import datetime, timedelta, timezone
    from app.core.security import generate_raw_token, hash_token
    from app.models.user import EmailVerificationToken, User
    assert register(client, "v@v.com").status_code == 201
    u = db.query(User).filter(User.email == "v@v.com").first()
    raw = generate_raw_token()
    db.add(EmailVerificationToken(user_id=u.id, token_hash=hash_token(raw),
                                 expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
    db.commit()
    assert client.post("/api/v1/auth/verify-email", json={"token": raw}).status_code == 200
    assert client.post("/api/v1/auth/verify-email",
                       json={"token": "bogus"}).status_code == 400


def test_reset_password_cycle_and_unlock(client, db):
    from datetime import datetime, timedelta, timezone
    from app.core.security import generate_raw_token, hash_token
    from app.models.user import PasswordResetToken, User
    assert register(client, "r@r.com").status_code == 201
    u = db.query(User).filter(User.email == "r@r.com").first()
    raw = generate_raw_token()
    db.add(PasswordResetToken(user_id=u.id, token_hash=hash_token(raw),
                              expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
    db.commit()
    r = client.post("/api/v1/auth/reset-password",
                    json={"token": raw, "new_password": "BrandNew123!"})
    assert r.status_code == 200
    assert login(client, "r@r.com", password="BrandNew123!")["access_token"]


def test_expired_and_wrong_type_tokens_rejected(client, db):
    from datetime import datetime, timedelta, timezone
    from app.core.config import get_settings
    make_user_db(db, "e@e.com", "CUSTOMER")
    tok = login(client, "e@e.com")
    payload = {"sub": "1", "role": "CUSTOMER", "type": "access", "jti": "x",
               "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}
    expired = pyjwt.encode(payload, get_settings().SECRET_KEY, algorithm="HS256")
    assert client.get("/api/v1/users/me",
                      headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    assert client.get("/api/v1/users/me",
                      headers=auth_h({"access_token": tok["refresh_token"]})).status_code == 401


def test_revoked_access_token_rejected(client, db):
    from datetime import datetime, timedelta, timezone
    from app.models.user import RevokedToken
    make_user_db(db, "rv@e.com", "CUSTOMER")
    tok = login(client, "rv@e.com")
    data = pyjwt.decode(tok["access_token"], options={"verify_signature": False})
    u = db.query(User).filter(User.email == "rv@e.com").first()
    db.add(RevokedToken(jti=data["jti"], user_id=u.id,
                        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)))
    db.commit()
    assert client.get("/api/v1/users/me", headers=auth_h(tok)).status_code == 401


def test_rbac_helpers_unit():
    from app.models.user import User as U
    admin, cust = U(role="ADMIN"), U(role="CUSTOMER")
    assert RequireAdmin(admin) is admin
    try:
        RequireAdmin(cust)
        raise SystemExit("should have raised")
    except Exception as e:
        assert getattr(e, "status_code", None) == 403
    assert require_roles("A", "B")(U(role="B")).role == "B"
    assert require_capability("browse_catalog")(cust) is cust


# ---------- users endpoints ----------
def test_profile_addresses_and_unlock(client, db):
    make_user_db(db, "adm2@e.com", "ADMIN")
    adm = login(client, "adm2@e.com")
    assert register(client, "u@u.com").status_code == 201
    ct = login(client, "u@u.com")
    r = client.patch("/api/v1/users/me", json={"full_name": "New Name"},
                     headers=auth_h(ct))
    assert r.json()["full_name"] == "New Name"
    a = client.post("/api/v1/users/me/addresses",
                    json={"label": "home", "country": "US", "is_default": True},
                    headers=auth_h(ct))
    assert a.status_code == 201
    assert len(client.get("/api/v1/users/me/addresses",
                          headers=auth_h(ct)).json()) == 1
    uid = client.get("/api/v1/users", headers=auth_h(adm)).json()
    target = next(u["id"] for u in uid if u["email"] == "u@u.com")
    assert client.post(f"/api/v1/users/{target}/unlock",
                       headers=auth_h(adm)).status_code == 200
    assert client.patch(f"/api/v1/users/{target}/role", json={"role": "NOPE"},
                        headers=auth_h(adm)).status_code == 400


# ---------- alerts / cache / gateway edges ----------
def test_alert_early_returns_and_cache_fallback(client, db, monkeypatch):
    import app.core.cache as cache
    from app.services import alerts
    monkeypatch.setattr(cache, "_get_client", lambda: None)
    assert cache.cache_get("k") is None
    cache.cache_set("k", {"a": 1})
    cache.cache_delete_prefix("x")
    assert cache.cache_key("a", "b") == cache.cache_key("a", "b")
    assert alerts.check_api_error_spike(db) is False  # not enough traffic
    from app.services.payment_gateway import verify_mock_signature, verify_stripe_signature
    assert verify_mock_signature(b"body", "wrong") is False
    assert verify_stripe_signature(b"body", "garbage", "secret") is False


def test_low_stock_no_fire_when_healthy(client, db):
    from app.services import alerts
    register(client, "ls@s.com", role="SELLER")
    st = login(client, "ls@s.com")
    p = make_product(client, st, sku="LS-1", price=5.0)
    set_stock(client, st, p["id"], 100)
    assert alerts.check_low_stock(db, p["id"]) is False
    assert alerts.check_low_stock(db, 999999) is False


# ---------- ml edge branches ----------
def test_forecast_and_recommend_edges():
    from datetime import date
    from app.ml.forecast import (days_until_stockout, forecast, holdout_mape,
                                 mape, moving_average_forecast, reorder_qty, wape)
    assert forecast([], 7) == ([0.0] * 7, "moving-average")
    assert moving_average_forecast([(date(2026, 1, 1), 4)], 3) == [4.0, 4.0, 4.0]
    assert mape([], []) == 0.0 and wape([0, 0], [1, 2]) == 0.0
    assert holdout_mape([(date(2026, 1, 1), 1)], 14) == (0.0, "moving-average")
    assert days_until_stockout(1000, [1.0] * 14) is None
    assert reorder_qty([1.0] * 14, on_hand=1000) == 0
    from app.ml.recommend import hit_rate_at_10, personal_for, similar_items
    assert similar_items(999, [[1, 2]]) == []
    assert personal_for([], [[1, 2]]) == []
    assert hit_rate_at_10([[1]]) == 0.0
    from app.services.pricing import calc_totals
    assert calc_totals(100, None)["shipping"] == 0.0  # free over threshold
    assert calc_totals(10, None)["shipping"] == 4.0


# ---------- rate limiting (M4) ----------
def test_auth_rate_limit_429(client, monkeypatch):
    from app.core import ratelimit
    from app.core.config import get_settings
    monkeypatch.setattr(ratelimit, "_redis", lambda: None)
    monkeypatch.setattr(get_settings(), "APP_ENV", "dev")
    ratelimit.reset_memory()
    try:
        codes = {client.post("/api/v1/auth/login",
                             json={"email": "nobody@x.com", "password": "wrong-1234"}
                             ).status_code for _ in range(12)}
        assert 429 in codes
    finally:
        monkeypatch.setattr(get_settings(), "APP_ENV", "test")
        ratelimit.reset_memory()


# ---------- router error branches ----------
def test_router_error_branches(client, db):
    register(client, "eb@s.com", role="SELLER")
    register(client, "ebc@s.com")
    st, ct = login(client, "eb@s.com"), login(client, "ebc@s.com")
    p = make_product(client, st, sku="EB-1", price=5.0)
    set_stock(client, st, p["id"], 10)
    # cart 404s
    assert client.patch("/api/v1/cart/items/999999?quantity=1",
                        headers=auth_h(ct)).status_code == 404
    assert client.delete("/api/v1/cart/items/999999",
                         headers=auth_h(ct)).status_code == 404
    assert client.post("/api/v1/cart/items", json={"product_id": 999999, "quantity": 1},
                       headers=auth_h(ct)).status_code == 404
    # category duplicate
    make_user_db(db, "ebadm@e.com", "ADMIN")
    adm = login(client, "ebadm@e.com")
    assert client.post("/api/v1/categories", json={"name": "Dup"},
                       headers=auth_h(adm)).status_code == 201
    assert client.post("/api/v1/categories", json={"name": "Dup"},
                       headers=auth_h(adm)).status_code == 409
    # variant duplicate SKU
    v = client.post(f"/api/v1/products/{p['id']}/variants", json={"sku": "V-1"},
                    headers=auth_h(st))
    assert v.status_code == 201
    assert client.post(f"/api/v1/products/{p['id']}/variants", json={"sku": "V-1"},
                       headers=auth_h(st)).status_code == 409
    # orders 404 + seller empty scope
    assert client.get("/api/v1/orders/999999", headers=auth_h(ct)).status_code == 404
    assert client.get("/api/v1/payments/by-order/999999",
                      headers=auth_h(ct)).status_code == 404
    # payments errors
    assert client.post("/api/v1/payments/999999/refund", json={},
                       headers=auth_h(adm)).status_code == 400
    bad = json.dumps({"event_id": "e1", "type": "nope"}).encode()
    from app.services.payment_gateway import sign_mock_webhook
    assert client.post("/api/v1/payments/webhook", content=bad,
                       headers={"X-Signature": sign_mock_webhook(bad),
                                "Content-Type": "application/json"}).status_code == 400
    # refund invalid amount
    add_to_cart(client, ct, p["id"], 1)
    o = checkout(client, ct, key="eb-1").json()
    pay = client.get(f"/api/v1/payments/by-order/{o['id']}",
                     headers=auth_h(ct)).json()
    body = json.dumps({"event_id": "ev-eb", "type": "payment.succeeded",
                       "gateway_ref": pay["gateway_ref"], "amount": pay["amount"]},
                      separators=(",", ":")).encode()
    client.post("/api/v1/payments/webhook", content=body,
                headers={"X-Signature": sign_mock_webhook(body),
                         "Content-Type": "application/json"})
    assert client.post(f"/api/v1/payments/{pay['id']}/refund",
                      json={"amount": 99999}, headers=auth_h(adm)).status_code == 422
    # reports invalid kind + empty trend
    assert client.get("/api/v1/reports/export.csv?kind=bogus",
                      headers=auth_h(adm)).status_code == 422
    assert client.get("/api/v1/reports/revenue-trend?days=1",
                      headers=auth_h(adm)).status_code == 200
    assert client.get("/", headers={}).status_code == 200
