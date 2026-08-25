from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.config import settings
from app.crud import create_product, get_product, list_expiring_soon, list_products, update_product
from app.database import get_db
from app.schemas import ProductCreate, ProductRead, ProductUpdate, to_read

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
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
        description="Case-insensitive match anywhere in the product name.",
    ),
    expired: bool | None = Query(
        default=None,
        description="true = expired only. false = not expired only. Omit for all.",
    ),
    db: Session = Depends(get_db)
) -> list[ProductRead]:
    """List the shelf, optionally filtered."""
    today = date.today()
    products = list_products(db, today=today, search=search, expired=expired)
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


@router.get("/{product_id}", response_model=ProductRead)
def get_one(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    """Fetch one product by id."""
    today = date.today()
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return to_read(product, today)


@router.patch("/{product_id}", response_model=ProductRead)
def update(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
) -> ProductRead:
    """Change only the fields that were sent."""
    today = date.today()
    product = update_product(
        db,
        product_id,
        data.model_dump(exclude_unset=True),
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return to_read(product, today)