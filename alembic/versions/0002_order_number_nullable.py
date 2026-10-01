"""Allow NULL order_number at INSERT time (assigned from row id right after).

Revision ID: 0002_order_number_nullable
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_order_number_nullable"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("orders", "order_number", existing_type=sa.String(32), nullable=True)


def downgrade() -> None:
    op.alter_column("orders", "order_number", existing_type=sa.String(32), nullable=False)
