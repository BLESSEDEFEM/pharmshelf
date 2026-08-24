from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class Product(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    expiry_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
    )
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name!r}, qty={self.quantity})>"
    
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_products_quantity_non_negative"),
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
    )