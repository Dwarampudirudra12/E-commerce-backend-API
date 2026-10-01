"""Catalog + inventory routes (doc 3.2).

- Guest browses/searches; seller manages OWN products; admin manages all.
- Hot reads cached in Redis (60s), invalidated on writes.
- Image upload: S3 when AWS creds configured, else local ./uploads (M2 dev path).
"""
import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core import cache
from app.core.deps import RequireAdmin, RequireSeller, get_current_user
from app.db.session import get_db
from app.models.catalog import Category, Inventory, Product, ProductImage, ProductVariant
from app.models.user import User
from app.schemas.catalog import (
    CategoryIn, CategoryOut, InventoryOut, InventoryPatch, ProductIn,
    ProductOut, ProductPatch, VariantIn, VariantOut,
)
from app.services.activity import audit

router = APIRouter(prefix="/products", tags=["catalog"])
cat_router = APIRouter(prefix="/categories", tags=["catalog"])


def _slug(name: str) -> str:
    return "-".join(name.lower().split())


def _product_out(p: Product, db: Session) -> dict:
    inv = db.query(Inventory).filter(Inventory.product_id == p.id,
                                     Inventory.variant_id.is_(None)).first()
    d = {c.name: getattr(p, c.name) for c in p.__table__.columns}
    d["price"] = float(p.price)
    d["on_hand"] = inv.on_hand if inv else 0
    d["reserved"] = inv.reserved if inv else 0
    return d


def _owns_or_admin(user: User, product: Product) -> None:
    if user.role != "ADMIN" and product.seller_id != user.id:
        raise HTTPException(403, "Only the owning seller or admin")


# ---------- Categories (admin) ----------
@cat_router.post("", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryIn, admin: User = Depends(RequireAdmin),
                    db: Session = Depends(get_db)):
    if db.query(Category).filter(Category.name == data.name).first():
        raise HTTPException(409, "Category exists")
    c = Category(name=data.name, slug=_slug(data.name), parent_id=data.parent_id)
    db.add(c)
    audit(db, user_id=admin.id, action="catalog.category_create", entity_type="category")
    db.commit()
    db.refresh(c)
    return c


@cat_router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.is_active == True).all()  # noqa: E712


# ---------- Products ----------
@router.post("", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, user: User = Depends(RequireSeller),
                   db: Session = Depends(get_db)):
    if db.query(Product).filter(Product.sku == data.sku).first():
        raise HTTPException(409, "SKU already exists")
    p = Product(sku=data.sku, name=data.name, description=data.description,
                price=data.price, category_id=data.category_id, seller_id=user.id,
                search_text=f"{data.name} {data.sku}".lower())
    db.add(p)
    db.flush()
    db.add(Inventory(product_id=p.id, on_hand=0, reserved=0))
    audit(db, user_id=user.id, action="catalog.product_create",
          entity_type="product", entity_id=str(p.id))
    db.commit()
    cache.cache_delete_prefix("catalog")
    return _product_out(p, db)


@router.get("", response_model=dict)
def list_products(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  db: Session = Depends(get_db)):
    key = cache.cache_key("catalog", "list", str(page), str(page_size))
    if (hit := cache.cache_get(key)) is not None:
        return hit
    q = db.query(Product).filter(Product.is_active == True)  # noqa: E712
    total = q.count()
    items = [_product_out(p, db) for p in q.offset((page - 1) * page_size).limit(page_size).all()]
    out = {"items": items, "total": total, "page": page, "page_size": page_size}
    cache.cache_set(key, out)
    return out


@router.get("/search", response_model=dict)
def search_products(q: str = Query("", max_length=128),
                    category_id: int | None = None,
                    min_price: float | None = None, max_price: float | None = None,
                    sort: str = Query("name", pattern="^(name|price|created_at)$"),
                    order: str = Query("asc", pattern="^(asc|desc)$"),
                    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                    db: Session = Depends(get_db)):
    key = cache.cache_key("catalog", "search", q, str(category_id), str(min_price),
                           str(max_price), sort, order, str(page), str(page_size))
    if (hit := cache.cache_get(key)) is not None:
        return hit
    query = db.query(Product).filter(Product.is_active == True)  # noqa: E712
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(
            (Product.name.ilike(like)) | (Product.sku.ilike(like)) | (Product.search_text.ilike(like)))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    col = {"name": Product.name, "price": Product.price, "created_at": Product.id}[sort]
    query = query.order_by(col.desc() if order == "desc" else col.asc())
    total = query.count()
    items = [_product_out(p, db) for p in query.offset((page - 1) * page_size).limit(page_size).all()]
    out = {"items": items, "total": total, "page": page, "page_size": page_size}
    cache.cache_set(key, out)
    return out


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    key = cache.cache_key("catalog", "product", str(product_id))
    if (hit := cache.cache_get(key)) is not None:
        return hit
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    out = _product_out(p, db)
    cache.cache_set(key, out, ttl=120)
    return out


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductPatch, user: User = Depends(RequireSeller),
                   db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    _owns_or_admin(user, p)
    for f, v in data.model_dump(exclude_unset=True).items():
        setattr(p, f, v)
    if data.name:
        p.search_text = f"{p.name} {p.sku}".lower()
    audit(db, user_id=user.id, action="catalog.product_update",
          entity_type="product", entity_id=str(p.id))
    db.commit()
    cache.cache_delete_prefix("catalog")
    return _product_out(p, db)


# ---------- Variants ----------
@router.post("/{product_id}/variants", response_model=VariantOut, status_code=201)
def add_variant(product_id: int, data: VariantIn, user: User = Depends(RequireSeller),
                db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    _owns_or_admin(user, p)
    if db.query(ProductVariant).filter(ProductVariant.sku == data.sku).first():
        raise HTTPException(409, "Variant SKU exists")
    v = ProductVariant(product_id=p.id, **data.model_dump())
    db.add(v)
    db.flush()
    db.add(Inventory(product_id=p.id, variant_id=v.id))
    db.commit()
    cache.cache_delete_prefix("catalog")
    db.refresh(v)
    return v


# ---------- Inventory (seller own / admin) ----------
@router.get("/{product_id}/inventory", response_model=list[InventoryOut])
def get_inventory(product_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    if user.role not in ("ADMIN", "SELLER"):
        raise HTTPException(403, "Sellers and admins only")
    if user.role == "SELLER" and p.seller_id != user.id:
        raise HTTPException(403, "Only the owning seller")
    return db.query(Inventory).filter(Inventory.product_id == product_id).all()


@router.patch("/{product_id}/inventory", response_model=list[InventoryOut])
def update_inventory(product_id: int, data: InventoryPatch, user: User = Depends(RequireSeller),
                     db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    _owns_or_admin(user, p)
    inv = db.query(Inventory).filter(Inventory.product_id == product_id,
                                    Inventory.variant_id.is_(None)).first()
    if inv.version != data.version:
        raise HTTPException(409, "Stale version — reload and retry")
    if data.on_hand is not None:
        if data.on_hand < inv.reserved:
            raise HTTPException(422, "on_hand cannot go below reserved")
        inv.on_hand = data.on_hand
    if data.reorder_level is not None:
        inv.reorder_level = data.reorder_level
    inv.version += 1
    audit(db, user_id=user.id, action="catalog.inventory_update",
          entity_type="product", entity_id=str(p.id))
    db.flush()
    from app.services import alerts
    alerts.check_low_stock(db, product_id)
    db.commit()
    cache.cache_delete_prefix("catalog")
    return db.query(Inventory).filter(Inventory.product_id == product_id).all()


# ---------- Images: S3 when configured, else local ./uploads ----------
@router.post("/{product_id}/images", status_code=201)
def upload_image(product_id: int, file: UploadFile = File(...),
                 user: User = Depends(RequireSeller), db: Session = Depends(get_db)):
    from app.core.config import get_settings
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    _owns_or_admin(user, p)
    ext = os.path.splitext(file.filename or "")[1][:8]
    key = f"products/{product_id}/{uuid.uuid4().hex}{ext}"
    bucket = os.environ.get("S3_BUCKET", "")
    if os.environ.get("AWS_ACCESS_KEY_ID") and bucket:
        import boto3
        boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1")).upload_fileobj(
            file.file, bucket, key)
        url = f"s3://{bucket}/{key}"
    else:
        dest = os.path.join("uploads", key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(file.file.read())
        url = f"/uploads/{key}"
    img = ProductImage(product_id=p.id, url=url, alt_text=file.filename or "")
    db.add(img)
    db.commit()
    cache.cache_delete_prefix("catalog")
    return {"url": url}
