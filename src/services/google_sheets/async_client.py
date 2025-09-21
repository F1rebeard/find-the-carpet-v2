from pathlib import Path

import gspread_asyncio
from google.oauth2.service_account import Credentials
from loguru import logger

from src.core_settings import GOOGLE_SCOPES, base_settings


class AsyncSheetClient:
    def __init__(self):
        self._manager = gspread_asyncio.AsyncioGspreadClientManager(self._create_creds)

    @staticmethod
    def _create_creds():
        file_path = Path(base_settings.GOOGLE_SERVICE_ACCOUNT_FILE).expanduser().resolve()
        if not file_path.exists():
            logger.error(f"❌ Google creds file not found: {file_path}")
            raise FileNotFoundError("❌ Google creds file not found")
        return Credentials.from_service_account_file(str(file_path), scopes=GOOGLE_SCOPES)

    async def fetch_all(
        self, spreadsheet_id: str, worksheet_title: str | None = None
    ) -> list[list[str]]:
        """Fetch all rows and columns from a worksheet."""

        logger.info(f"📑 Fetching ALL values from sheet {worksheet_title or 'default[0]'}")
        try:
            gc = await self._manager.authorize()
            spreadsheet = await gc.open_by_key(spreadsheet_id)
            worksheet = (
                await spreadsheet.worksheet(worksheet_title)
                if worksheet_title
                else await spreadsheet.get_worksheet(0)
            )
            values = await worksheet.get_all_values()
            logger.info(
                f"✅ Fetched full sheet: rows={len(values)} cols={len(values[0]) if values else 0}"
            )
            return values
        except Exception as e:
            logger.error(f"💥 Failed to fetch all values: {e!r}")
            raise


# TODO REMOVE THIS TESTING SCRIPT
async def main():
    client = AsyncSheetClient()
    values = await client.fetch_all(
        spreadsheet_id="1i9C46L666ecwJKU1J5u9L-mB0d5T5mgBPVL9rz1jJ1g",
        worksheet_title="Ковры",
    )
    print("Fetched rows:", len(values))
    print("First row:", values[0] if values else "Empty")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
