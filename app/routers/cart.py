"""Persistent cart (doc 3.3): add / update / remove; prices re-validated at checkout."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.cart_order import Cart, CartItem
from app.models.catalog import Product, ProductVariant
from app.models.user import User
from app.schemas.order import CartItemIn, CartItemOut

router = APIRouter(prefix="/cart", tags=["cart"])


def _get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.flush()
    return cart


def _price_of(db: Session, product_id: int, variant_id: int | None) -> float:
    if variant_id:
        v = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not v:
            raise HTTPException(404, "Variant not found")
        if v.price_override is not None:
            return float(v.price_override)
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p or not p.is_active:
        raise HTTPException(404, "Product not found or inactive")
    return float(p.price)


@router.get("", response_model=list[CartItemOut])
def get_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        return []
    return db.query(CartItem).filter(CartItem.cart_id == cart.id).all()


@router.post("/items", response_model=CartItemOut, status_code=201)
def add_item(data: CartItemIn, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    price = _price_of(db, data.product_id, data.variant_id)
    cart = _get_or_create_cart(db, user.id)
    existing = db.query(CartItem).filter(
        CartItem.cart_id == cart.id, CartItem.product_id == data.product_id,
        CartItem.variant_id == data.variant_id).first()
    if existing:
        existing.quantity = min(existing.quantity + data.quantity, 99)
        existing.unit_price = price
        db.commit()
        db.refresh(existing)
        return existing
    item = CartItem(cart_id=cart.id, product_id=data.product_id,
                    variant_id=data.variant_id, quantity=data.quantity, unit_price=price)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/items/{item_id}", response_model=CartItemOut)
def update_item(item_id: int, quantity: int,
                user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if quantity < 1 or quantity > 99:
        raise HTTPException(422, "Quantity must be 1..99")
    item = db.query(CartItem).join(Cart).filter(
        CartItem.id == item_id, Cart.user_id == user.id).first()
    if not item:
        raise HTTPException(404, "Cart item not found")
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=204)
def remove_item(item_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    item = db.query(CartItem).join(Cart).filter(
        CartItem.id == item_id, Cart.user_id == user.id).first()
    if not item:
        raise HTTPException(404, "Cart item not found")
    db.delete(item)
    db.commit()
    return None
