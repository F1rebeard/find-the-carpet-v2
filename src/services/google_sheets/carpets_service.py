from typing import Any

from sqlalchemy import select

from src.database.models.carpets import Carpet
from src.schemas.carpers_from_google_sh import CarpetRowFromGoogleSheets
from src.services.google_sheets.base_service import BaseGoogleSheetsService, SyncResult

# Backward compatibility alias
CarpetsSyncResult = SyncResult


class GoogleSheetsCarpetService(BaseGoogleSheetsService[CarpetRowFromGoogleSheets, int, Carpet]):
    """Synchronize carpets table with data from Google Sheets."""

    def get_schema_model(self) -> type[CarpetRowFromGoogleSheets]:
        return CarpetRowFromGoogleSheets

    def get_entity_name(self) -> str:
        return "Carpet"

    async def load_existing_records(self) -> dict[int, Carpet]:
        result = await self.session.execute(select(Carpet))
        carpets = {carpet.carpet_id: carpet for carpet in result.scalars()}
        return carpets

    def extract_key_from_payload(self, payload: dict[str, Any]) -> int:
        return payload["carpet_id"]

    def row_to_payload(self, row: CarpetRowFromGoogleSheets) -> dict[str, Any]:
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

    def create_entity(self, payload: dict[str, Any]) -> Carpet:
        return Carpet(**payload)

    def has_changes(self, carpet: Carpet, payload: dict[str, Any]) -> bool:
        for field, new_value in payload.items():
            current_value = getattr(carpet, field)
            if field == "price":
                # Compare floats with tolerance to avoid noisy updates
                if current_value is None and new_value is not None:
                    return True
                if new_value is None and current_value is not None:
                    return True
                if (
                    current_value is not None
                    and abs(float(current_value) - float(new_value)) > 1e-6
                ):
                    return True
            else:
                if current_value != new_value:
                    return True
        return False

    async def sync_carpets(
        self, spreadsheet_id: str, worksheet_title: str | None = None
    ) -> CarpetsSyncResult:
        """Synchronize carpets from Google Sheets (backward compatibility wrapper)."""
        result = await self.sync_data(spreadsheet_id, worksheet_title)

        # Convert SyncResult to CarpetsSyncResult for backward compatibility
        return CarpetsSyncResult(
            entity_name=result.entity_name,
            total_rows=result.total_rows,
            inserted=result.inserted,
            updated=result.updated,
            skipped=result.skipped,
            bad_data=result.bad_data,
            invalid_report=result.invalid_report,
        )
