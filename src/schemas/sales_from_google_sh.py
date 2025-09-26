from datetime import date
from decimal import Decimal, InvalidOperation
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
    carpet_design: str = Field(..., alias="Дизайн")
    carpet_size: str = Field(..., alias="Размер")
    collection: str | None = Field(None, alias="Коллекция")
    style: str | None = Field(None, alias="Стиль")
    sale_date: date = Field(..., alias="Дата продажи")
    quantity: int = Field(..., alias="Кол-во проданных, шт.")
    payment_method: PaymentMethod = Field(..., alias="Тип оплаты")
    basic_price: float = Field(..., alias="Цена базовая")
    sale_price: float = Field(..., alias="Цена продажи")
    discount: float = Field(0.0, alias="Скидка, %")
    note: str | None = Field(None, alias="Дополнительная информация")
    sold_to: str | None = Field(None, alias="Покупатель")

    @field_validator("carpet_size", mode="before")
    @classmethod
    def normalize_size(cls, value: str) -> str:
        if value is None:
            raise ValueError("Размер отсутствует")

        raw_value = str(value).strip()
        if not raw_value:
            raise ValueError("Размер отсутствует")

        cleaned = (
            raw_value.casefold()
            .replace(" ", "")
            .replace(",", ".")
            .replace("×", "x")
            .replace("х", "x")
        )

        if cleaned.count("x") != 1:
            raise ValueError("Размер должен содержать один разделитель 'x'")

        width_raw, height_raw = cleaned.split("x")
        width = cls._format_size_part(width_raw)
        height = cls._format_size_part(height_raw)
        return f"{width}x{height}"

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Кол-во проданных должно быть > 0")
        return value

    @field_validator("basic_price", "sale_price", mode="before")
    @classmethod
    def parse_base_price(cls, value: float | str) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if value is None:
            raise ValueError("Базовая стоимость отсутствует")
        cleaned = str(value).replace("₽", "").replace(" ", "").replace("\xa0", "").replace(",", ".")
        if not cleaned:
            raise ValueError("Базовая стоимость отсутствует")
        try:
            return float(cleaned)
        except ValueError as exc:
            raise ValueError("Не удалось преобразовать базовую стоимость в число") from exc

    @field_validator("basic_price", "sale_price")
    @classmethod
    def price_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Цена должна быть больше > 0")
        return value

    @field_validator("discount", mode="before")
    @classmethod
    def parse_discount(cls, value: float | str | None) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if value is None or value == "":
            return 0.0

        cleaned = str(value).replace(",", ".").strip()
        if not cleaned:
            return 0.0

        try:
            return float(cleaned)
        except ValueError as e:
            raise ValueError("Не удалось преобразовать скидку в числовой формат") from e

    @field_validator("discount", mode="after")
    @classmethod
    def discount_range_from_zero_to_hundred(cls, value: float) -> float:
        if not (0 <= value <= 100):
            raise ValueError("Диапазон скидки от 0 до 100%")
        return value

    @staticmethod
    def _format_size_part(raw_value: str) -> str:
        if not raw_value:
            raise ValueError("Размер содержит пустое значение")

        try:
            number = Decimal(raw_value)
        except InvalidOperation as exc:
            raise ValueError("Размер должен содержать числовые значения") from exc

        normalized = number.normalize()
        if normalized == normalized.to_integral():
            return str(normalized.quantize(Decimal(1)))
        formatted = format(normalized, "f").rstrip("0").rstrip(".")
        return formatted or "0"
