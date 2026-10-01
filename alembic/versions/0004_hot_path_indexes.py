"""M4 optimization: composite indexes for hot query paths.

Revision ID: 0004_hot_path_indexes
Revises: 0003_m3_additions
"""
from alembic import op

revision = "0004_hot_path_indexes"
down_revision = "0003_m3_additions"
branch_labels = None
depends_on = None

INDEXES = [
    ("ix_orders_user_status", "orders", ["user_id", "status"]),
    ("ix_orders_created", "orders", ["created_at"]),
    ("ix_order_items_order", "order_items", ["order_id"]),
    ("ix_audit_user_created", "audit_logs", ["user_id", "created_at"]),
    ("ix_ml_model_entity", "ml_predictions", ["model_name", "entity_id"]),
    ("ix_notifications_user_read", "notifications", ["user_id", "is_read"]),
    ("ix_inventory_product", "inventory", ["product_id"]),
]


def upgrade() -> None:
    for name, table, cols in INDEXES:
        op.create_index(name, table, cols)


def downgrade() -> None:
    for name, table, _ in INDEXES:
        op.drop_index(name, table_name=table)
