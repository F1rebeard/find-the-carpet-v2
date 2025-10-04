from typing import Dict, List

from pydantic import BaseModel, Field


class CarpetFilters(BaseModel):
    """Model for tracking user's carpet filter selections."""

    geometry: List[str] = Field(default_factory=list)
    size: List[str] = Field(default_factory=list)
    color: List[str] = Field(default_factory=list)
    style: List[str] = Field(default_factory=list)
    collection: List[str] = Field(default_factory=list)

    _filter_labels: Dict[str, str] = {
        "geometry": "Геометрия",
        "size": "Размер",
        "color": "Цвет",
        "style": "Стиль",
        "collection": "Коллекция",
    }

    def is_empty(self) -> bool:
        """Check if no filters are applied."""
        return not any(getattr(self, field) for field in self._filter_labels)

    def get_active_filters_count(self) -> int:
        """Get count of active filter categories."""
        return sum(1 for field in self._filter_labels if getattr(self, field))

    def get_filter_summary(self) -> Dict[str, List[str]]:
        """Get summary of applied filters."""
        return {
            self._filter_labels[field]: getattr(self, field)
            for field in self._filter_labels
            if getattr(self, field)
        }

    def clear_filter(self, filter_type: str) -> None:
        """Clear specific filter type."""
        if filter_type in self._filter_labels:
            setattr(self, filter_type, [])

    def clear_all(self) -> None:
        """Clear all filters."""
        for field in self._filter_labels:
            setattr(self, field, [])


class FilterOption(BaseModel):
    """Model for filter option with count."""

    value: str
    count: int
    selected: bool = False


class FilterResults(BaseModel):
    """Model for filter results."""

    options: List[FilterOption]
    total_carpets: int
    filter_type: str
