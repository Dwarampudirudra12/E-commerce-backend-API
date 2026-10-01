"""M3 schema additions: notifications.is_read, demand_history, product_views.

Revision ID: 0003_m3_additions
Revises: 0002_order_number_nullable
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_m3_additions"
down_revision = "0002_order_number_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications",
                  sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_table(
        "demand_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("day", sa.Date(), nullable=False, index=True),
        sa.Column("qty", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_table(
        "product_views",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"),
                  nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("product_views")
    op.drop_table("demand_history")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_column("notifications", "is_read")
