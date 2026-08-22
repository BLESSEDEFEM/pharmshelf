from datetime import date
from decimal import Decimal

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

    products = list_products(db_session)

    assert len(products) == 1
    assert products[0].name == "Amoxicillin 250mg"
    assert products[0].price == Decimal("1800.00")   # still exact