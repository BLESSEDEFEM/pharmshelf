from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.product import Product


class ProductCreate(BaseModel):
    """What a caller may send to POST /products."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(default=0, ge=0)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    expiry_date: date

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class ProductUpdate(BaseModel):
    """What a caller may send to PATCH /products/{id}. Everything optional."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    quantity: int | None = Field(default=None, ge=0)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    expiry_date: date | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) else v


class ProductRead(BaseModel):
    """What every endpoint returns."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    quantity: int
    price: Decimal
    expiry_date: date
    created_at: datetime
    updated_at: datetime

    is_expired: bool
    days_until_expiry: int


def to_read(product: Product, today: date) -> ProductRead:
    """Build a response from a row, using ONE 'today' supplied by the caller."""
    return ProductRead(
        id=product.id,
        name=product.name,
        quantity=product.quantity,
        price=product.price,
        expiry_date=product.expiry_date,
        created_at=product.created_at,
        updated_at=product.updated_at,
        is_expired=product.expiry_date < today,
        days_until_expiry=(product.expiry_date - today).days,
    )
