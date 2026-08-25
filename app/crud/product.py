from datetime import date, timedelta
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

def list_products(
    db: Session,
    *,
    today: date,
    search: str | None = None,
    expired: bool | None = None,
    ) -> list[Product]:
    """Every product, optionally narrowed by name and by expiry status."""
    stmt = select(Product)
    if search is not None:
        stmt = stmt.where(Product.name.iLike(f"%{search}%"))
        
    if expired is True:
        stmt = stmt.where(Product.expiry_date < today)
    elif expired is False:
        stmt = stmt.where(Product.expiry_date >= today)
        
    return list(db.execute(stmt.order_by(Product.name)).scalars().all())


def list_expiring_soon(db: Session, *, days: int, today: date) -> list[Product]:
    """Products expiring within `days` of `today`, soonest first.

    Already-expired stock is excluded: that needs removal, not a warning.
    """
    window_end = today + timedelta(days=days)
    stmt = (
        select(Product)
        .where(Product.expiry_date >= today)
        .where(Product.expiry_date <= window_end)
        .order_by(Product.expiry_date)
    )
    return list(db.execute(stmt).scalars().all())

def get_product(db: Session, product_id: int) -> Product | None:
    """Fetch one product by id. Returns None if it does not exist."""
    return db.get(Product, product_id)

def update_product(db: Session, product_id: int, fields: dict) -> Product | None:
    """Apply the given fields to a product. Returns None if it does not exist.

    `fields` must contain ONLY the keys the caller intends to change.
    """
    product = db.get(Product, product_id)
    if product is None:
        return None
    
    for key, value in fields.items():
        setattr(product, key, value)
        
    db.commit()
    db.refresh(product)
    return product