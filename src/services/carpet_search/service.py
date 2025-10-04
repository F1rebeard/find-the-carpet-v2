from typing import Any, List, Sequence

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core_settings import base_settings
from src.dao.carpets import CarpetsDAO
from src.database.models.carpets import Carpet
from src.services.carpet_search.models import CarpetFilters, FilterOption, FilterResults


# TODO Check this implementation
class CarpetSearchService:
    """Service for handling carpet search and filtering operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.carpets_dao = CarpetsDAO(
            session=session, filter_available_only=base_settings.FILTER_ONLY_AVAILABLE_CARPETS
        )

    async def get_filter_options(
        self, filter_type: str, current_filters: CarpetFilters
    ) -> FilterResults:
        """Get available filter options based on current filter state.

        Args:
            filter_type: Type of filter ('geometry', 'size', 'color', 'style', 'collection')
            current_filters: Current filter selections

        Returns:
            FilterResults with available options and counts
        """
        try:
            filters_dict = current_filters.model_dump()
            options_with_counts = await self.carpets_dao.get_filtered_unique_values(
                field_name=filter_type, existing_filters=filters_dict
            )
            current_selections = getattr(current_filters, filter_type, [])
            options = [
                FilterOption(value=value, count=count, selected=value in current_selections)
                for value, count in options_with_counts
            ]

            # Get total carpet count with current filters
            total_carpets = await self.carpets_dao.count_filtered_carpets(filters_dict)

            return FilterResults(
                options=options, total_carpets=total_carpets, filter_type=filter_type
            )

        except Exception as e:
            logger.error(f"❌ Error getting filter options for {filter_type}: {e}")
            return FilterResults(options=[], total_carpets=0, filter_type=filter_type)

    async def search_carpets(
        self, current_filters: CarpetFilters, limit: int = 50, offset: int = 0
    ) -> Sequence[Carpet] | list[Any]:
        """Search carpets with current filters.

        Args:
            current_filters: Current filter selections
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Carpet objects matching filters
        """
        try:
            filters_dict = current_filters.model_dump()
            return await self.carpets_dao.search_carpets(
                filters=filters_dict, limit=limit, offset=offset
            )

        except Exception as e:
            logger.error(f"❌ Error searching carpets: {e}")
            return []

    async def count_filtered_carpets(self, current_filters: CarpetFilters) -> int:
        """Count carpets matching current filters.

        Args:
            current_filters: Current filter selections

        Returns:
            Number of carpets matching filters
        """
        try:
            filters_dict = current_filters.model_dump()
            return await self.carpets_dao.count_filtered_carpets(filters_dict)

        except Exception as e:
            logger.error(f"❌ Error counting filtered carpets: {e}")
            return 0

    @staticmethod
    def update_filter_selection(
        current_filters: CarpetFilters, filter_type: str, selected_values: List[str]
    ) -> CarpetFilters:
        """Update filter selections for a specific filter type.

        Args:
            current_filters: Current filter state
            filter_type: Type of filter to update
            selected_values: New selected values for this filter

        Returns:
            Updated CarpetFilters object

        Raises:
            ValueError: If filter_type is not a valid filter field
        """
        valid_fields = {"geometry", "size", "color", "style", "collection"}
        if filter_type not in valid_fields:
            raise ValueError(f"Invalid filter_type '{filter_type}'. Must be one of: {valid_fields}")

        # Create a copy to avoid modifying original
        updated_filters = current_filters.model_copy()
        setattr(updated_filters, filter_type, selected_values)

        return updated_filters
