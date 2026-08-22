from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product

def create_product(
    db: Session,
    *,
    name: str,
    quantity: int,
    price: Decimal,
    expiry_date: date
    ) -> Product:
    """Insert one product and return it, with database-generated values filled in."""
    product = Product(
        name=name,
        quantity=quantity,
        price=price,
        expiry_date=expiry_date,
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def list_products(db: Session) -> list[Product]:
    """Return every product, ordered by name."""
    stmt = select(Product).order_by(Product.name)
    return list(db.execute(stmt).scalars().all())