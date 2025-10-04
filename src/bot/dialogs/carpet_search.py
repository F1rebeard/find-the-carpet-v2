import operator
from typing import Any, Dict

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Column, Group, Multiselect, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger

from src.database import db
from src.services.carpet_search.messages import messages
from src.services.carpet_search.models import CarpetFilters
from src.services.carpet_search.service import CarpetSearchService
from src.services.carpet_search.states import CarpetSearchStatesGroup


async def on_filter_selected(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Handle filter button click - navigate to filter selection window."""
    try:
        # Extract filter type from button id (e.g., "filter_geometry" -> "geometry")
        filter_type = button.widget_id.replace("filter_", "")
        dialog_manager.dialog_data["current_filter_type"] = filter_type
        state_map = {
            "geometry": CarpetSearchStatesGroup.geometry_selection,
            "size": CarpetSearchStatesGroup.size_selection,
            "color": CarpetSearchStatesGroup.color_selection,
            "style": CarpetSearchStatesGroup.style_selection,
            "collection": CarpetSearchStatesGroup.collection_selection,
        }

        target_state = state_map.get(filter_type)
        if target_state:
            await dialog_manager.switch_to(target_state)
            logger.info(f"🔍 User {callback.from_user.id} opened {filter_type} filter")
        else:
            logger.error(f"❌ Unknown filter type: {filter_type}")
            await callback.answer("❌ Неизвестный тип фильтра")

    except Exception as e:
        logger.error(f"❌ Error in on_filter_selected: {e}")
        await callback.answer("❌ Ошибка открытия фильтра")


async def on_apply_filter(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Apply selected filter values and return to main menu."""
    try:
        filter_type = dialog_manager.dialog_data.get("current_filter_type")
        if not filter_type:
            await callback.answer("❌ Тип фильтра не определен")
            return

        # Get selected values from multiselect widget
        multiselect_id = f"{filter_type}_multiselect"
        widget = dialog_manager.find(multiselect_id)
        if not widget:
            logger.error(f"❌ Multiselect widget not found: {multiselect_id}")
            await callback.answer("❌ Ошибка применения фильтра")
            return

        selected_ids = widget.get_checked()

        # Convert short IDs back to actual values using the mapping
        value_mapping = dialog_manager.dialog_data.get(f"{filter_type}_value_mapping", {})
        selected_values = [
            value_mapping.get(id_str) for id_str in selected_ids if id_str in value_mapping
        ]

        # Update filters in dialog data
        filters_data = dialog_manager.dialog_data.get("filters", {})
        current_filters = CarpetFilters(**filters_data)

        # Update the specific filter type with selected values
        setattr(current_filters, filter_type, selected_values)

        # Save updated filters back to dialog data
        dialog_manager.dialog_data["filters"] = current_filters.model_dump()
        logger.info(
            f"✅ User {callback.from_user.id} applied {filter_type} filter: {selected_values}"
        )

        # Navigate back to main menu
        await dialog_manager.switch_to(CarpetSearchStatesGroup.main_menu)
        await callback.answer("✅ Фильтр применен")

    except Exception as e:
        logger.error(f"❌ Error in on_apply_filter: {e}")
        await callback.answer("❌ Ошибка применения фильтра")


async def on_clear_filter(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Clear current filter and reload options."""
    try:
        filter_type = dialog_manager.dialog_data.get("current_filter_type")
        if not filter_type:
            await callback.answer("❌ Тип фильтра не определен")
            return

        # Clear the specific filter
        filters_data = dialog_manager.dialog_data.get("filters", {})
        current_filters = CarpetFilters(**filters_data)
        current_filters.clear_filter(filter_type)

        # Save updated filters
        dialog_manager.dialog_data["filters"] = current_filters.model_dump()

        logger.info(f"🗑 User {callback.from_user.id} cleared {filter_type} filter")

        # Reload the current window to reflect changes
        await callback.answer("🗑 Фильтр очищен")

    except Exception as e:
        logger.error(f"❌ Error in on_clear_filter: {e}")
        await callback.answer("❌ Ошибка очистки фильтра")


async def on_clear_all_filters(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Clear all filters and return to initial state."""
    try:
        # Reset filters to empty state
        dialog_manager.dialog_data["filters"] = CarpetFilters().model_dump()

        logger.info(f"🗑 User {callback.from_user.id} cleared all filters")

        await callback.answer("🗑 Все фильтры очищены")

    except Exception as e:
        logger.error(f"❌ Error in on_clear_all_filters: {e}")
        await callback.answer("❌ Ошибка очистки фильтров")


async def main_menu_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get data for main menu window."""
    try:
        # Get current filters from dialog data
        filters_data = dialog_manager.dialog_data.get("filters", {})
        current_filters = CarpetFilters(**filters_data)

        async with db.get_session() as session:
            service = CarpetSearchService(session)
            total_carpets = await service.count_filtered_carpets(current_filters)

        return {
            "main_menu_text": messages.get_main_menu_text(current_filters, total_carpets),
            "has_filters": not current_filters.is_empty(),
            "has_results": total_carpets > 0,
            "filters_count": current_filters.get_active_filters_count(),
        }

    except Exception as e:
        logger.error(f"❌ Error in main_menu_getter: {e}")
        return {
            "main_menu_text": f"{messages.welcome_title}\n\n{messages.error_loading_filters}",
            "has_filters": False,
            "has_results": False,
            "filters_count": 0,
        }


async def filter_selection_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get data for filter selection window with progressive filtering."""
    try:
        filter_type = dialog_manager.dialog_data.get("current_filter_type")
        if not filter_type:
            logger.error("❌ No filter_type in dialog_data")
            return {
                "filter_text": messages.error_loading_filters,
                "options": [],
                "selected_count": 0,
                "total_options": 0,
            }

        # Get current filters
        filters_data = dialog_manager.dialog_data.get("filters", {})
        current_filters = CarpetFilters(**filters_data)

        async with db.get_session() as session:
            service = CarpetSearchService(session)
            filter_results = await service.get_filter_options(
                filter_type=filter_type, current_filters=current_filters
            )

        # Get currently selected values for this filter
        current_selections = getattr(current_filters, filter_type, [])

        # Store value mapping in dialog_data to avoid long callback data
        value_mapping = {str(i): opt.value for i, opt in enumerate(filter_results.options)}
        reverse_mapping = {opt.value: str(i) for i, opt in enumerate(filter_results.options)}

        dialog_manager.dialog_data[f"{filter_type}_value_mapping"] = value_mapping
        dialog_manager.dialog_data[f"{filter_type}_reverse_mapping"] = reverse_mapping

        # Format options as tuples (display_text, short_id) with counts
        options = [
            (f"{opt.value} ({opt.count})", str(i)) for i, opt in enumerate(filter_results.options)
        ]

        # Pre-select currently selected values using short IDs
        multiselect_id = f"{filter_type}_multiselect"
        widget = dialog_manager.find(multiselect_id)
        if widget and current_selections:
            selected_ids = [
                reverse_mapping.get(val) for val in current_selections if val in reverse_mapping
            ]
            widget.set_checked(*selected_ids)

        selected_count = len(current_selections)
        total_options = len(options)

        filter_text = messages.get_filter_selection_text(
            filter_type=filter_type, selected_count=selected_count, total_options=total_options
        )

        return {
            "filter_text": filter_text,
            "options": options,
            "selected_count": selected_count,
            "total_options": total_options,
        }

    except Exception as e:
        logger.error(f"❌ Error in filter_selection_getter: {e}")
        return {
            "filter_text": messages.error_loading_filters,
            "options": [],
            "selected_count": 0,
            "total_options": 0,
        }


async def results_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get data for results window - display filtered carpets."""
    try:
        # Get current filters
        filters_data = dialog_manager.dialog_data.get("filters", {})
        current_filters = CarpetFilters(**filters_data)

        async with db.get_session() as session:
            service = CarpetSearchService(session)
            carpets = await service.search_carpets(current_filters=current_filters, limit=50)
            total_count = await service.count_filtered_carpets(current_filters=current_filters)

        if not carpets:
            return {
                "results_text": f"{messages.results_title}\n\n",
                "carpets_display": "",
                "has_carpets": False,
                "total_count": 0,
            }

        # Format carpets for display
        carpets_display_parts = []
        for i, carpet in enumerate(carpets, 1):
            carpet_text = messages.format_carpet_result(carpet)
            carpets_display_parts.append(f"━━━━━━━━━━━━━━━\n{i}. {carpet_text}")

        carpets_display = "\n\n".join(carpets_display_parts)
        results_summary = messages.results_summary_format.format(count=total_count)
        results_text = f"{messages.results_title}\n\n{results_summary}\n"

        return {
            "results_text": results_text,
            "carpets_display": carpets_display,
            "has_carpets": True,
            "total_count": total_count,
        }

    except Exception as e:
        logger.error(f"❌ Error in results_getter: {e}")
        return {
            "results_text": f"{messages.results_title}\n\n{messages.error_searching_carpets}",
            "carpets_display": "",
            "has_carpets": False,
            "total_count": 0,
        }


# Create filter selection windows dynamically
def create_filter_window(filter_type: str) -> Window:
    """Create a filter selection window for a specific filter type."""
    return Window(
        Format("{filter_text}"),
        Group(
            Multiselect(
                Format("✅️ {item[0]}"),
                Format("☐ {item[0]}"),
                id=f"{filter_type}_multiselect",
                item_id_getter=operator.itemgetter(1),
                items="options",
            ),
            width=2,
        ),
        Column(
            Button(
                Const(messages.apply_and_back_button),
                id="apply_filter",
                on_click=on_apply_filter,
            ),
            Button(
                Const(messages.clear_this_filter_button),
                id="clear_filter",
                on_click=on_clear_filter,
            ),
        ),
        SwitchTo(
            Const(messages.back_to_menu_button),
            id="back_to_main",
            state=CarpetSearchStatesGroup.main_menu,
        ),
        state=getattr(CarpetSearchStatesGroup, f"{filter_type}_selection"),
        getter=filter_selection_getter,
    )


# Main menu window
main_menu_window = Window(
    Format("{main_menu_text}"),
    # Filter buttons
    Column(
        Button(
            Const(messages.filter_titles["geometry"]),
            id="filter_geometry",
            on_click=on_filter_selected,
        ),
        Button(
            Const(messages.filter_titles["size"]),
            id="filter_size",
            on_click=on_filter_selected,
        ),
        Button(
            Const(messages.filter_titles["color"]),
            id="filter_color",
            on_click=on_filter_selected,
        ),
        Button(
            Const(messages.filter_titles["style"]),
            id="filter_style",
            on_click=on_filter_selected,
        ),
        Button(
            Const(messages.filter_titles["collection"]),
            id="filter_collection",
            on_click=on_filter_selected,
        ),
    ),
    # Action buttons
    Row(
        SwitchTo(
            Const(messages.show_results_button),
            id="show_results",
            state=CarpetSearchStatesGroup.results,
            when="has_results",
        ),
        Button(
            Const(messages.clear_all_filters_button),
            id="clear_all",
            on_click=on_clear_all_filters,
            when="has_filters",
        ),
    ),
    state=CarpetSearchStatesGroup.main_menu,
    getter=main_menu_getter,
)

# Results window - displays formatted carpet list
results_window = Window(
    Format("{results_text}"),
    Format("{carpets_display}", when="has_carpets"),
    Format(
        messages.no_results_text, when=lambda data, widget, manager: not data.get("has_carpets")
    ),
    SwitchTo(
        Const(messages.back_to_menu_button),
        id="back_to_filters",
        state=CarpetSearchStatesGroup.main_menu,
    ),
    state=CarpetSearchStatesGroup.results,
    getter=results_getter,
)

# Create filter windows for each filter type
geometry_window = create_filter_window("geometry")
size_window = create_filter_window("size")
color_window = create_filter_window("color")
style_window = create_filter_window("style")
collection_window = create_filter_window("collection")

# Create the dialog
carpet_search_dialog = Dialog(
    main_menu_window,
    geometry_window,
    size_window,
    color_window,
    style_window,
    collection_window,
    results_window,
)
