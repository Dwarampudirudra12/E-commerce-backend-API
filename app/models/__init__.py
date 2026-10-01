"""Import all models here so Base.metadata covers the full schema (Alembic + create_all)."""
from app.models.user import Address, EmailVerificationToken, PasswordResetToken, RevokedToken, Role, User  # noqa: F401
from app.models.catalog import Category, Inventory, Product, ProductImage, ProductVariant  # noqa: F401
from app.models.cart_order import Cart, CartItem, Order, OrderItem, OrderStatusHistory  # noqa: F401
from app.models.payment import DiscountCode, Payment, Refund  # noqa: F401
from app.models.observability import AuditLog, DemandHistory, MlPrediction, Notification, ProductView  # noqa: F401
