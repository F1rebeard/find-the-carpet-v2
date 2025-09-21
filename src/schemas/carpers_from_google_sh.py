from pydantic import BaseModel, Field, field_validator


class CarpetRowFromGoogleSheets(BaseModel):
    """Carpet row from Google Sheets."""

    carpet_id: int = Field(..., alias="Id Ковра")
    collection: str = Field(..., alias="Коллекция")
    geometry: str = Field(..., alias="Геометрия")
    size: str = Field(..., alias="Размер")
    design: str = Field(..., alias="Дизайн")
    color_1: str = Field(..., alias="Цвет 1")
    color_2: str | None = Field(None, alias="Цвет 2")
    color_3: str | None = Field(None, alias="Цвет 3")
    style: str = Field(..., alias="Стиль")
    quantity: int = Field(..., alias="Количество, шт")
    base_price: float = Field(..., alias="Базовая стоимость")

    @field_validator("quantity")
    @classmethod
    def quantity_not_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Количество не может быть отрицательным")
        return value

    @field_validator("base_price")
    @classmethod
    def base_price_not_negative(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Базовая стоимость должна быть больше 0")
        return value
