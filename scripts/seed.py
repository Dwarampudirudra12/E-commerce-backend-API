"""Seed M1 demo data: 4 roles, 4 demo users, categories, products + inventory.

Run: docker compose exec api python scripts/seed.py
Demo logins (password: Password123!):
  customer@example.com / seller@example.com / support@example.com / admin@example.com
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
import app.models  # noqa: F401
from app.models.user import Role, User
from app.models.catalog import Category, Inventory, Product
from app.core.security import hash_password

CATEGORIES = ["Electronics", "Accessories", "Home"]
PRODUCTS = [
    ("WM-204", "Wireless Mouse", 24.99, "Electronics", 38, 5),
    ("UC-110", "USB-C Cable", 9.50, "Accessories", 120, 10),
    ("KB-301", "Mechanical Keyboard", 59.99, "Electronics", 25, 5),
    ("MS-118", "Desk Mat", 14.99, "Home", 60, 10),
]

USERS = [
    ("customer@example.com", "Demo Customer", "CUSTOMER"),
    ("seller@example.com", "Demo Seller", "SELLER"),
    ("support@example.com", "Demo Support", "SUPPORT"),
    ("admin@example.com", "Demo Admin", "ADMIN"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        for name in ("CUSTOMER", "SELLER", "SUPPORT", "ADMIN"):
            if not db.query(Role).filter(Role.name == name).first():
                db.add(Role(name=name, description=f"{name.title()} role"))
        db.commit()
        roles = {r.name: r for r in db.query(Role).all()}

        for email, full_name, role in USERS:
            if not db.query(User).filter(User.email == email).first():
                db.add(User(email=email, password_hash=hash_password("Password123!"),
                            full_name=full_name, role=role, role_id=roles[role].id,
                            email_verified=True))
        db.commit()

        for c in CATEGORIES:
            if not db.query(Category).filter(Category.name == c).first():
                db.add(Category(name=c, slug=c.lower(), is_active=True))
        db.commit()
        cats = {c.name: c for c in db.query(Category).all()}
        seller = db.query(User).filter(User.email == "seller@example.com").first()

        for sku, name, price, cat, stock, reorder in PRODUCTS:
            p = db.query(Product).filter(Product.sku == sku).first()
            if not p:
                p = Product(sku=sku, name=name, description=f"Demo {name}",
                            price=price, category_id=cats[cat].id,
                            seller_id=seller.id if seller else None,
                            search_text=f"{name} {sku} {cat}".lower())
                db.add(p)
                db.flush()
                db.add(Inventory(product_id=p.id, on_hand=stock, reserved=0, reorder_level=reorder))
        db.commit()
        from app.models.payment import DiscountCode
        if not db.query(DiscountCode).filter(DiscountCode.code == "WELCOME10").first():
            db.add(DiscountCode(code="WELCOME10", percent_off=10, max_uses=1000,
                                used_count=0, is_active=True))
            db.commit()
        print("Seed OK: roles=%d users=%d products=%d" % (
            db.query(Role).count(), db.query(User).count(), db.query(Product).count()))
    finally:
        db.close()


if __name__ == "__main__":
    main()
