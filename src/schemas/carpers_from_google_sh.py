from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, Field, FieldValidationInfo, field_validator, model_validator


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

    @field_validator("size", mode="before")
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

    @field_validator("color_1", "color_2", "color_3", mode="before")
    @classmethod
    def normalize_color(
        cls,
        value: str | None,
        info: FieldValidationInfo,
    ) -> str | None:
        if value is None:
            if info.field_name == "color_1":
                raise ValueError("Цвет 1 обязателен")
            return None

        cleaned = str(value).strip()
        if not cleaned:
            if info.field_name == "color_1":
                raise ValueError("Цвет 1 обязателен")
            return None

        normalized = cls._format_color(cleaned)
        if not normalized:
            raise ValueError("Цвет содержит недопустимое значение")
        return normalized

    @model_validator(mode="before")
    @classmethod
    def ensure_color_present(cls, values: object) -> object:
        if not isinstance(values, dict):
            return values

        color_keys = (
            "color_1",
            "color_2",
            "color_3",
            "Цвет 1",
            "Цвет 2",
            "Цвет 3",
        )

        for key in color_keys:
            raw_value = values.get(key)
            if isinstance(raw_value, str) and raw_value.strip():
                return values

        raise ValueError("Должен быть указан хотя бы один цвет")

    @model_validator(mode="after")
    def ensure_unique_colors(self) -> "CarpetRowFromGoogleSheets":
        unique_colors: set[str] = set()
        for color in (self.color_1, self.color_2, self.color_3):
            if color is None:
                continue
            if color in unique_colors:
                raise ValueError("Цвета у одного ковра не должны повторяться")
            unique_colors.add(color)
        return self

    @field_validator("base_price", mode="before")
    @classmethod
    def parse_base_price(cls, value: float | str) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if value is None:
            raise ValueError("Базовая стоимость отсутствует")
        cleaned = (
            str(value)
            .replace("₽", "")
            .replace(" ", "")
            .replace("\xa0", "")
            .replace(",", ".")
        )
        if not cleaned:
            raise ValueError("Базовая стоимость отсутствует")
        try:
            return float(cleaned)
        except ValueError as exc:
            raise ValueError("Не удалось преобразовать базовую стоимость в число") from exc

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

    @staticmethod
    def _format_color(value: str) -> str:
        raw_tokens = value.replace(",", " ").split()
        normalized_tokens: list[str] = []

        for token in raw_tokens:
            normalized = token[0].upper() + token[1:].lower() if len(token) > 1 else token.upper()
            if not normalized[0].isalpha():
                raise ValueError("Цвет должен начинаться с заглавной буквы")
            normalized_tokens.append(normalized)

        normalized_color = " ".join(normalized_tokens)
        if not normalized_color:
            return ""
        return normalized_color
