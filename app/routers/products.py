from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.config import settings
from app.crud import create_product, list_expiring_soon, list_products
from app.database import get_db
from app.schemas import ProductCreate, ProductRead, to_read

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_user(data: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    """Add a product to the shelf."""
    today = date.today()
    product = create_product(db, **data.model_dump())
    return to_read(product, today)


@router.get("", response_model=list[ProductRead])
def list_all(
    db: Session = Depends(get_db)
) -> list[ProductRead]:
    """List every product on the shelf."""
    today = date.today()
    products = list_products(db)
    return [to_read(p, today) for p in products]

@router.get("/expiring-soon", response_model=list[ProductRead])
def expiring_soon(
    days: int = Query(
        default=settings.default_expiry_window_days,
        gt=0,
        le=settings.max_expiry_window_days,
        description="How many days ahead to look.",
    ),
    db: Session = Depends(get_db),
    ) -> list[ProductRead]:
    """Products expiring within the next `days` days, soonest first."""
    today = date.today()
    products = list_expiring_soon(db, days=days, today=today)
    return [to_read(p, today) for p in products]