from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class PaymentMethod(StrEnum):
    """Payment type."""

    CASHLESS = "Безналичный"
    BANK = "Банк"
    CASH = "Наличный"
    CARD = "Картой"


class SalesFromGoogleSH(BaseModel):
    """Sales data imported from Google Sheets."""

    carpet_id: int = Field(..., alias="Id ковра")
    sale_date: date = Field(..., alias="Дата продажи")
    quantity: int = Field(..., alias="Кол-во проданных, шт.")
    payment_method: PaymentMethod = Field(..., alias="Тип оплаты")
    basic_price: float = Field(..., alias="Цена базовая")
    sale_price: float = Field(..., alias="Цена продажи")
    discount: float = Field(0.0, alias="Скидка, %")
    note: str | None = Field(None, alias="Дополнительная информация")
    collection: str | None = Field(None, alias="Коллекция")
    style: str | None = Field(None, alias="Стиль")

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Кол-во проданных должно быть > 0")
        return value

    @field_validator("basic_price", "sale_price")
    @classmethod
    def price_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Цена должна быть больше > 0")
        return value

    @field_validator("discount")
    @classmethod
    def discount_range_from_zero_to_hundred(cls, value: float) -> float:
        if not (0 <= value <= 100):
            raise ValueError("Диапазон скидки от 0 до 100%")
        return value
