from typing import TypeVar

from loguru import logger
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def parse_table_from_google_sheets(
    rows: list[list[str]],
    header: list[str],
    model: type[T],
) -> tuple:

    passed_values: list[T] = []
    failed_values: list[dict] = []
    idx = {name: i for i, name in enumerate(header)}
    for row_number, raw_data in enumerate(rows, start=2):
        data: dict[str, str | None] = {}
        for _, field in model.model_fields.items():
            alias = field.alias
            i = idx.get(alias)
            if i is not None:
                data[alias] = (
                    raw_data[i].strip() if i < len(raw_data) and raw_data[i] is not None else None
                )
                logger.debug(f"[{row_number}] {alias}: {data[alias]}")
        try:
            passed_values.append(model(**data))
        except ValidationError as e:
            failed_values.append({"row": row_number, "errors": e.errors(), "raw_data": raw_data})

    return passed_values, failed_values
