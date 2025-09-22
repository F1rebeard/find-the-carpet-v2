from dataclasses import dataclass
from typing import Any, TypeVar

from loguru import logger
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import db
from src.database.models.carpets import Carpet
from src.schemas.carpers_from_google_sh import CarpetRowFromGoogleSheets
from src.services.google_sheets.async_client import AsyncSheetClient

T = TypeVar("T", bound=BaseModel)


def parse_table_from_google_sheets(
    rows: list[list[str]],
    header: list[str],
    model: type[T],
) -> tuple[list[T], list[dict[str, Any]]]:

    passed_values: list[T] = []
    failed_values: list[dict[str, Any]] = []
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


@dataclass(slots=True)
class CarpetsSyncResult:
    total_rows: int
    inserted: int
    updated: int
    skipped: int
    bad_data: int = 0
    invalid_report: str | None = None

    @property
    def has_changes(self) -> bool:
        return (self.inserted + self.updated) > 0


class GoogleSheetsCarpetService:
    """Synchronize carpets table with data from Google Sheets."""

    def __init__(self, session: AsyncSession, sheet_client: AsyncSheetClient | None = None):
        self.session = session
        self.sheet_client = sheet_client or AsyncSheetClient()
        self._field_alias_map = {
            name: field.alias or name for name, field in CarpetRowFromGoogleSheets.model_fields.items()
        }

    async def sync_carpets(
        self, spreadsheet_id: str, worksheet_title: str | None = None
    ) -> CarpetsSyncResult:
        values = await self.sheet_client.fetch_all(spreadsheet_id, worksheet_title)
        if not values:
            logger.warning("⚠️ Google Sheet returned no data")
            return CarpetsSyncResult(
                    total_rows=0,
                    inserted=0,
                    updated=0,
                    skipped=0,
                    bad_data=0,
                    invalid_report="В таблице нету данных.",
                )

        header, *rows = values
        if not header:
            logger.warning("⚠️ Google Sheet header row is empty")
            return CarpetsSyncResult(
                total_rows=0,
                inserted=0,
                updated=0,
                skipped=0,
                bad_data=0,
                invalid_report="В таблице отсутствует строка заголовков."
            )

        valid_rows, invalid_rows = parse_table_from_google_sheets(
            rows=rows,
            header=header,
            model=CarpetRowFromGoogleSheets,
        )
        invalid_report = self._build_invalid_report(invalid_rows)
        if not valid_rows:
            logger.warning("⚠️ No valid rows after validation; nothing to sync")
            return CarpetsSyncResult(
                total_rows=0,
                inserted=0,
                updated=0,
                skipped=0,
                bad_data=0,
                invalid_report=invalid_report
            )
        existing_carpets = await self._load_existing_carpets()
        inserted = updated = skipped = 0
        for row in valid_rows:
            payload = self._row_to_payload(row)
            carpet = existing_carpets.get(payload["carpet_id"])
            if carpet is None:
                self.session.add(Carpet(**payload))
                inserted += 1
                logger.debug(f"➕ New carpet scheduled for insert: {payload['carpet_id']}")
                continue

            if self._has_changes(carpet, payload):
                for field, value in payload.items():
                    setattr(carpet, field, value)
                updated += 1
                logger.debug(f"♻️ Carpet updated: {payload['carpet_id']}")
            else:
                skipped += 1
                logger.debug(f"⏭️ Carpet unchanged: {payload['carpet_id']}")

        total_rows = len(valid_rows) + len(invalid_rows)
        bad_data = total_rows - inserted - updated - skipped
        logger.info(
            "📊 Carpets sync summary — total:{} inserted:{} updated:{} skipped:{} bad_data:{}",
            total_rows,
            inserted,
            updated,
            skipped,
            bad_data,
        )
        return CarpetsSyncResult(
            total_rows=total_rows,
            inserted=inserted,
            updated=updated,
            skipped=skipped,
            bad_data=bad_data,
            invalid_report=invalid_report,
        )

    async def _load_existing_carpets(self) -> dict[int, Carpet]:
        result = await self.session.execute(select(Carpet))
        carpets = {carpet.carpet_id: carpet for carpet in result.scalars()}
        logger.debug(f"📦 Loaded {len(carpets)} carpets from database")
        return carpets

    @staticmethod
    def _row_to_payload(row: CarpetRowFromGoogleSheets) -> dict[str, Any]:
        return {
            "carpet_id": row.carpet_id,
            "collection": row.collection,
            "geometry": row.geometry,
            "size": row.size,
            "design": row.design,
            "color_1": row.color_1,
            "color_2": row.color_2 or None,
            "color_3": row.color_3 or None,
            "style": row.style,
            "quantity": row.quantity,
            "price": float(row.base_price),
        }

    def _has_changes(self, carpet: Carpet, payload: dict[str, Any]) -> bool:
        for field, new_value in payload.items():
            current_value = getattr(carpet, field)
            if field == "price":
                # Compare floats with tolerance to avoid noisy updates
                if current_value is None and new_value is not None:
                    return True
                if new_value is None and current_value is not None:
                    return True
                if current_value is not None and abs(float(current_value) - float(new_value)) > 1e-6:
                    return True
            else:
                if current_value != new_value:
                    return True
        return False

    def _build_invalid_report(self, invalid_rows: list[dict[str, Any]]) -> str | None:
        if not invalid_rows:
            return None

        lines = ["⚠️ Обнаружены ошибки при синхронизации ковров:"]
        for item in invalid_rows:
            row_number = item.get("row")
            errors = item.get("errors", [])
            raw_data = item.get("raw_data", [])

            messages: list[str] = []
            for error in errors:
                loc = error.get("loc", ())
                field_name = loc[-1] if loc else "unknown"
                alias = self._field_alias_map.get(field_name, str(field_name))
                messages.append(f"{alias}: {error.get('msg')}")

            row_preview = ", ".join(cell for cell in raw_data if cell) or "пустая строка"
            lines.append(f"• Строка {row_number}: {'; '.join(messages)}")
            lines.append(f"  ↳ Данные: {row_preview}")

        return "\n".join(lines)


# TODO: Remove manual script once integrated with bot workflow.
async def main() -> None:
    await db.connect()
    try:
        async with db.get_session() as session:
            service = GoogleSheetsCarpetService(session=session)
            result = await service.sync_carpets(
                spreadsheet_id="1i9C46L666ecwJKU1J5u9L-mB0d5T5mgBPVL9rz1jJ1g",
                worksheet_title="Ковры",
            )
            print("Total rows:", result.total_rows)
            print("Inserted:", result.inserted)
            print("Updated:", result.updated)
            print("Skipped:", result.skipped)
            if result.invalid_report:
                print("Invalid rows report:\n", result.invalid_report)
    finally:
        await db.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
