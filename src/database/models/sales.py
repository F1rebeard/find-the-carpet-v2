import uuid
from datetime import date

from sqlalchemy import UUID, Date, Double, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models.base import Base


class SalesData(Base):
    """Carpet sales data."""

    __tablename__ = "sales"

    sale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sale_date: Mapped[date] = mapped_column(Date, server_default=func.now(), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)
    basic_price: Mapped[float] = mapped_column(Double, nullable=False)
    sale_price: Mapped[float] = mapped_column(Double, nullable=False)
    discount: Mapped[float] = mapped_column(Double, nullable=False)
    sold_to: Mapped[str] = mapped_column(String(32), nullable=False)
    carpet_id: Mapped[int] = mapped_column(ForeignKey("carpets.id"), nullable=False)
