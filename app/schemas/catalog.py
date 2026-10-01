"""Catalog schemas (M2)."""
from pydantic import BaseModel, Field


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    parent_id: int | None = None


class CategoryOut(CategoryIn):
    id: int
    slug: str
    is_active: bool

    class Config:
        from_attributes = True


class ProductIn(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    price: float = Field(gt=0)
    category_id: int | None = None


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    description: str
    price: float
    category_id: int | None
    seller_id: int | None
    is_active: bool
    on_hand: int = 0
    reserved: int = 0

    class Config:
        from_attributes = True


class ProductPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class VariantIn(BaseModel):
    sku: str
    name: str = ""
    price_override: float | None = None


class VariantOut(VariantIn):
    id: int
    product_id: int

    class Config:
        from_attributes = True


class InventoryOut(BaseModel):
    product_id: int
    variant_id: int | None
    on_hand: int
    reserved: int
    reorder_level: int
    version: int

    class Config:
        from_attributes = True


class InventoryPatch(BaseModel):
    on_hand: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    version: int  # optimistic check — 409 on mismatch
