"""Order / cart schemas (M2)."""
from pydantic import BaseModel, Field


class CartItemIn(BaseModel):
    product_id: int
    variant_id: int | None = None
    quantity: int = Field(gt=0, le=99)


class CartItemOut(CartItemIn):
    id: int
    unit_price: float

    class Config:
        from_attributes = True


class CheckoutIn(BaseModel):
    shipping_address: dict = Field(default_factory=dict)
    discount_code: str | None = None


class OrderItemOut(BaseModel):
    product_id: int
    variant_id: int | None
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    order_number: str
    status: str
    subtotal: float
    tax: float
    shipping: float
    discount: float
    total: float
    risk_score: float | None = None
    items: list[OrderItemOut] = []

    class Config:
        from_attributes = True


class StatusPatch(BaseModel):
    to_status: str
    note: str = ""
