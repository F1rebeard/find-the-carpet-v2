from typing import Any

from sqlalchemy import select

from src.database.models.sales import SalesData
from src.schemas.sales_from_google_sh import SalesFromGoogleSH
from src.services.google_sheets.base_service import BaseGoogleSheetsService, SyncResult

# Backward compatibility alias
SalesSyncResult = SyncResult


class GoogleSheetsSalesService(
    BaseGoogleSheetsService[SalesFromGoogleSH, tuple[int, Any, str], SalesData]
):
    """Synchronize sales table with data from Google Sheets."""

    def get_schema_model(self) -> type[SalesFromGoogleSH]:
        return SalesFromGoogleSH

    def get_entity_name(self) -> str:
        return "Sale"

    async def load_existing_records(self) -> dict[tuple[int, Any, str], SalesData]:
        """Load existing sales using composite key (carpet_id, sale_date, sold_to)."""
        result = await self.session.execute(select(SalesData))
        sales = {(sale.carpet_id, sale.sale_date, sale.sold_to): sale for sale in result.scalars()}
        return sales

    def extract_key_from_payload(self, payload: dict[str, Any]) -> tuple[int, Any, str]:
        return payload["carpet_id"], payload["sale_date"], payload["sold_to"]

    def row_to_payload(self, row: SalesFromGoogleSH) -> dict[str, Any]:
        return {
            "carpet_id": row.carpet_id,
            "sale_date": row.sale_date,
            "quantity": row.quantity,
            "payment_method": row.payment_method.value,  # Convert enum to string
            "basic_price": float(row.basic_price),
            "sale_price": float(row.sale_price),
            "discount": row.discount,
            "sold_to": row.sold_to or "Unknown",  # Handle None case
        }

    def create_entity(self, payload: dict[str, Any]) -> SalesData:
        return SalesData(**payload)

    def has_changes(self, sale: SalesData, payload: dict[str, Any]) -> bool:
        for field, new_value in payload.items():
            current_value = getattr(sale, field)
            if field in ("basic_price", "sale_price", "discount"):
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

    async def sync_sales(
        self, spreadsheet_id: str, worksheet_title: str | None = None
    ) -> SalesSyncResult:
        """Synchronize sales from Google Sheets (backward compatibility wrapper)."""
        result = await self.sync_data(spreadsheet_id, worksheet_title)
        # Convert SyncResult to SalesSyncResult for backward compatibility
        return SalesSyncResult(
            entity_name=result.entity_name,
            total_rows=result.total_rows,
            inserted=result.inserted,
            updated=result.updated,
            skipped=result.skipped,
            bad_data=result.bad_data,
            invalid_report=result.invalid_report,
        )
