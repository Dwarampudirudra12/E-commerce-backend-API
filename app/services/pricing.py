"""Pricing: subtotal + tax + shipping - discount (doc 3.3 checkout step 4)."""
from app.core.config import get_settings
from app.models.payment import DiscountCode


def calc_totals(subtotal: float, discount_code: DiscountCode | None = None) -> dict:
    s = get_settings()
    discount = round(float(subtotal) * float(discount_code.percent_off) / 100, 2) if discount_code else 0.0
    taxable = float(subtotal) - discount
    tax = round(taxable * s.TAX_RATE, 2)
    shipping = 0.0 if taxable >= s.FREE_SHIPPING_THRESHOLD else s.SHIPPING_FLAT
    total = round(taxable + tax + shipping, 2)
    return {"subtotal": round(float(subtotal), 2), "tax": tax, "shipping": shipping,
            "discount": discount, "total": total}
