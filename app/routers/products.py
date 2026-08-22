from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import create_product, list_products
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