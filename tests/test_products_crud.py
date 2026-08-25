from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.crud import create_product, list_products


def test_crud_layer_works_without_any_http(db_session):
    """no app, no client, no URL."""
    create_product(
        db_session,
        name="Amoxicillin 250mg",
        quantity=12,
        price=Decimal("1800.00"),
        expiry_date=date(2026, 8, 20),
    )

    products = list_products(db_session, today=date(2026, 8, 15))

    assert len(products) == 1
    assert products[0].name == "Amoxicillin 250mg"
    assert products[0].price == Decimal("1800.00")   # still exact
    
def test_database_refuses_a_negative_quantity(db_session):
    """Bypasses Pydantic entirely, so it tests the DATABASE layer."""
    with pytest.raises(IntegrityError):
        create_product(
            db_session,
            name="Impossible Stock",
            quantity=-5,                       # Pydantic never sees this
            price=Decimal("100.00"),
            expiry_date=date(2027, 1, 1),
        )
    db_session.rollback()