import asyncio
from typing import Dict, List, Sequence, Tuple

from loguru import logger
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.carpets import Carpet


class CarpetsDAO:

    def __init__(self, session: AsyncSession, filter_available_only: bool = True):
        self.session = session
        self.filter_available_only = filter_available_only
        self._valid_fields = ["collection", "geometry", "size", "style", "color"]

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
        if field_name not in self._valid_fields:
            raise ValueError(f"Invalid field_name. Must be one of: {self._valid_fields}")

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

    async def get_filtered_unique_values(
        self, field_name: str, existing_filters: Dict[str, List[str]]
    ) -> List[Tuple[str, int]]:
        """Get unique values for a field based on existing filters with counts.

        Args:
            field_name: Filter field name ('collection', 'geometry', 'size', 'style', 'color')
            existing_filters: Dict of currently applied filters

        Returns:
            List of tuples (value, count) for the specified field

        Raises:
            ValueError: If field_name is not a valid filter field
            SQLAlchemyError: If database query fails
        """
        if field_name not in self._valid_fields:
            raise ValueError(f"Invalid field_name. Must be one of: {self._valid_fields}")

        try:
            filters_without_current = {k: v for k, v in existing_filters.items() if k != field_name}
            conditions = self._build_filter_conditions(filters_without_current)
            if field_name == "color":
                values_with_counts = await self._get_color_counts(conditions)
            else:
                values_with_counts = await self._get_field_counts(field_name, conditions)
            return sorted(values_with_counts, key=lambda x: x[0])

        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to get filtered values for field '{field_name}': {e}")
            raise

    async def search_carpets(
        self, filters: Dict[str, List[str]], limit: int = 50, offset: int = 0
    ) -> Sequence[Carpet]:
        """Search carpets with applied filters.

        Args:
            filters: Dict of filter criteria
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of Carpet objects matching the filters

        Raises:
            SQLAlchemyError: If database query fails
        """
        try:
            conditions = self._build_filter_conditions(filters)
            if self.filter_available_only:
                conditions.append(Carpet.quantity > 0)
            query = select(Carpet).where(and_(*conditions)).limit(limit).offset(offset)
            result = await self.session.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to search carpets with filters: {e}")
            raise

    async def count_filtered_carpets(self, filters: Dict[str, List[str]]) -> int:
        """Count carpets matching the applied filters.

        Args:
            filters: Dict of filter criteria

        Returns:
            Number of carpets matching the filters

        Raises:
            SQLAlchemyError: If database query fails
        """
        try:
            conditions = self._build_filter_conditions(filters)
            if self.filter_available_only:
                conditions.append(Carpet.quantity > 0)
            query = select(func.count(Carpet.carpet_id)).where(and_(*conditions))
            result = await self.session.execute(query)
            return result.scalar() or 0

        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to count filtered carpets: {e}")
            raise

    @staticmethod
    def _build_filter_conditions(filters: Dict[str, List[str]]) -> List:
        """Build SQLAlchemy filter conditions from filters dict."""
        conditions = []

        # Colors checked separately
        filtered_fields = {
            "geometry": Carpet.geometry,
            "size": Carpet.size,
            "style": Carpet.style,
            "collection": Carpet.collection,
        }
        for field_name, field_value in filtered_fields.items():
            if filtered_values := filters.get(field_name):
                conditions.append(field_value.in_(filtered_values))

        if filtered_colors := filters.get("color"):
            color_conditions = [
                or_(
                    Carpet.color_1 == color,
                    Carpet.color_2 == color,
                    Carpet.color_3 == color,
                )
                for color in filtered_colors
            ]
            conditions.append(or_(*color_conditions))
        return conditions

    async def _get_color_counts(self, conditions: list) -> list[tuple[str, int]]:
        """Get aggregated counts across all three color columns."""
        color_fields = [Carpet.color_1, Carpet.color_2, Carpet.color_3]
        base_conditions = list(conditions)
        if self.filter_available_only:
            base_conditions.append(Carpet.quantity > 0)
        queries = [
            select(field.label("color"), func.count().label("count"))
            .where(and_(field.is_not(None), *base_conditions))
            .group_by(field)
            for field in color_fields
        ]
        results = await asyncio.gather(*[self.session.execute(query) for query in queries])
        color_counts = {}
        logger.debug(f"Color results: {results}")
        for result in results:
            for row in result.fetchall():
                logger.debug(f"Row: {row}")
                color_value = row.color
                count = row.count
                color_counts[color_value] = color_counts.get(color_value, 0) + count
        return list(color_counts.items())

    async def _get_field_counts(self, field_name: str, conditions: list) -> list[tuple[str, int]]:
        """Get value counts for a single field."""
        field_attr = getattr(Carpet, field_name)
        base_conditions = list(conditions)
        if self.filter_available_only:
            base_conditions.append(Carpet.quantity > 0)
        query = (
            select(field_attr, func.count().label("count"))
            .where(and_(field_attr.is_not(None), *base_conditions))
            .group_by(field_attr)
        )
        result = await self.session.execute(query)
        return [(row[0], row[1]) for row in result.fetchall()]
