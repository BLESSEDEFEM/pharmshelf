"""add non-negative checks on quantity and price

Revision ID: edfdb99f6b0c
Revises: 76d91a89d670
Create Date: 2026-08-24 11:02:52.848441

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edfdb99f6b0c'
down_revision: Union[str, Sequence[str], None] = '76d91a89d670'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_products_quantity_non_negative",
        "products",
        "quantity >= 0",
    )
    op.create_check_constraint(
        "ck_products_price_non_negative",
        "products",
        "price >= 0",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_products_price_non_negative", "products", type_="check")
    op.drop_constraint("ck_products_quantity_non_negative", "products", type_="check")
