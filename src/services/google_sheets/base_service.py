from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.google_sheets.async_client import AsyncSheetClient
from src.services.google_sheets.utils import parse_table_from_google_sheets

T = TypeVar("T", bound=BaseModel)
K = TypeVar("K")  # Key type
E = TypeVar("E")  # Entity type


@dataclass(slots=True)
class SyncResult:
    """Generic sync result for Google Sheets operations."""

    entity_name: str
    total_rows: int
    inserted: int
    updated: int
    skipped: int
    bad_data: int = 0
    deleted: int = 0
    invalid_report: str | None = None

    @property
    def has_changes(self) -> bool:
        return (self.inserted + self.updated + self.deleted) > 0


class BaseGoogleSheetsService(ABC, Generic[T, K, E]):
    """Base service for synchronizing data from Google Sheets to database."""

    def __init__(self, session: AsyncSession, sheet_client: AsyncSheetClient | None = None):
        self.session = session
        self.sheet_client = sheet_client or AsyncSheetClient()
        self._field_alias_map = {
            name: field.alias or name
            for name, field in self.get_schema_model().model_fields.items()
        }

    @abstractmethod
    def get_schema_model(self) -> type[T]:
        """Return the Pydantic schema model for this service."""
        pass

    @abstractmethod
    def get_entity_name(self) -> str:
        """Return the entity name for logging and error reporting."""
        pass

    @abstractmethod
    async def load_existing_records(self) -> dict[K, E]:
        """Load existing records from database, keyed by identifier."""
        pass

    @abstractmethod
    def extract_key_from_payload(self, payload: dict[str, Any]) -> K:
        """Extract the key from payload for record lookup."""
        pass

    @abstractmethod
    def row_to_payload(self, row: T) -> dict[str, Any]:
        """Convert validated row to database payload."""
        pass

    @abstractmethod
    def create_entity(self, payload: dict[str, Any]) -> E:
        """Create new entity instance from payload."""
        pass

    @abstractmethod
    def has_changes(self, entity: E, payload: dict[str, Any]) -> bool:
        """Check if entity has changes compared to payload."""
        pass

    async def sync_data(
        self, spreadsheet_id: str, worksheet_title: str | None = None
    ) -> SyncResult:
        """Synchronize data from Google Sheets to database."""
        values = await self.sheet_client.fetch_all(spreadsheet_id, worksheet_title)
        entity_name = self.get_entity_name()

        if not values:
            logger.warning("⚠️ Google Sheet returned no data")
            return SyncResult(
                entity_name=entity_name,
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
            return SyncResult(
                entity_name=entity_name,
                total_rows=0,
                inserted=0,
                updated=0,
                skipped=0,
                bad_data=0,
                invalid_report="В таблице отсутствует строка заголовков.",
            )

        valid_rows, invalid_rows = parse_table_from_google_sheets(
            rows=rows,
            header=header,
            model=self.get_schema_model(),
        )
        invalid_report = self._build_invalid_report(invalid_rows)

        if not valid_rows:
            logger.warning("⚠️ No valid rows after validation; nothing to sync")
            return SyncResult(
                entity_name=entity_name,
                total_rows=0,
                inserted=0,
                updated=0,
                skipped=0,
                bad_data=0,
                invalid_report=invalid_report,
            )

        existing_records = await self.load_existing_records()
        inserted = updated = skipped = 0

        for row in valid_rows:
            payload = self.row_to_payload(row)
            key = self.extract_key_from_payload(payload)
            record = existing_records.get(key)

            if record is None:
                self.session.add(self.create_entity(payload))
                inserted += 1
                logger.debug(f"➕ New {entity_name.lower()} scheduled for insert: {key}")
                continue

            if self.has_changes(record, payload):
                for field, value in payload.items():
                    setattr(record, field, value)
                updated += 1
                logger.debug(f"♻️ {entity_name} updated: {key}")
            else:
                skipped += 1
                logger.debug(f"⏭️ {entity_name} unchanged: {key}")

        total_rows = len(valid_rows) + len(invalid_rows)
        bad_data = total_rows - inserted - updated - skipped
        logger.info(
            f"📊 {entity_name} sync summary — total:{total_rows} inserted:{inserted} updated:{updated} skipped:{skipped} bad_data:{bad_data}"
        )

        return SyncResult(
            entity_name=entity_name,
            total_rows=total_rows,
            inserted=inserted,
            updated=updated,
            skipped=skipped,
            bad_data=bad_data,
            invalid_report=invalid_report,
        )

    def _build_invalid_report(self, invalid_rows: list[dict[str, Any]]) -> str | None:
        """Build error report for invalid rows."""
        if not invalid_rows:
            return None

        entity_name = self.get_entity_name().lower()
        lines = [f"⚠️ Обнаружены ошибки при синхронизации {entity_name}:"]

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
