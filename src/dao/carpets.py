import asyncio

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import db
from src.database.models.carpets import Carpet


class CarpetsDAO:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_unique_filter_values(self, field_name: str) -> list[str]:
        """Get unique values for carpet filter attributes.

        Will be used to display all unique values for filtering users choice for carpets.

        Args:
            field_name: Filter field name ('collection', 'geometry', 'size', 'style', 'colors')

        Returns:
            Sorted list of unique string values for the specified field

        Raises:
            ValueError: If field_name is not a valid filter field
            SQLAlchemyError: If database query fails
        """
        valid_fields = ["collection", "geometry", "size", "style", "colors"]
        if field_name not in valid_fields:
            raise ValueError(f"Invalid field_name. Must be one of: {valid_fields}")

        try:
            if field_name == "colors":
                # Get all color values from three columns in parallel
                color_fields = [Carpet.color_1, Carpet.color_2, Carpet.color_3]
                color_queries = [
                    select(field).distinct().where(field.is_not(None)) for field in color_fields
                ]
                results = await asyncio.gather(
                    *[self.session.execute(query) for query in color_queries]
                )

                # Combine all unique colors
                all_unique_colors = set()
                for result in results:
                    all_unique_colors.update(row[0] for row in result.fetchall())
                values = list(all_unique_colors)
            else:

                # Get unique values for single field
                field_attr = getattr(Carpet, field_name)
                query = select(field_attr).distinct().where(field_attr.is_not(None))
                result = await self.session.execute(query)
                values = [row[0] for row in result.fetchall()]

            return sorted(values)

        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to get unique values for field '{field_name}': {e}")
            raise


async def main():
    await db.connect()
    async with db.get_session() as session:
        carpets = CarpetsDAO(session=session)
        result = await carpets.get_unique_filter_values("colors")
        logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
