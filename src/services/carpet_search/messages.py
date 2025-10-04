import dataclasses

from src.services.carpet_search.models import CarpetFilters


@dataclasses.dataclass
class CarpetSearchMessages:
    """Centralized messages for carpet search functionality."""

    welcome_title: str = "🔍 <b>Поиск ковров</b>"
    welcome_text: str = (
        "Добро пожаловать в систему поиска ковров!\n\n"
        "Выберите любой фильтр для начала поиска. "
        "После выбора параметров в одном фильтре, остальные фильтры "
        "будут показывать c учётом применённых фильтров.\n\n"
        "Вы можете выбирать фильтры в любом порядке."
    )

    # Filter titles
    filter_titles = {
        "geometry": "📐 Геометрия",
        "size": "📏 Размер",
        "color": "🎨 Цвет",
        "style": "✨ Стиль",
        "collection": "📚 Коллекция",
    }

    # Filter selection texts
    filter_selection_texts = {
        "geometry": "📐 <b>Выберите геометрию</b>\n\nВыберите одну или несколько форм:",
        "size": "📏 <b>Выберите размер</b>\n\nВыберите один или несколько размеров:",
        "color": "🎨 <b>Выберите цвет</b>\n\nВыберите один или несколько цветов:",
        "style": "✨ <b>Выберите стиль</b>\n\nВыберите один или несколько стилей:",
        "collection": "📚 <b>Выберите</b>\n\nВыберите одну или несколько коллекций:",
    }

    # Button texts
    show_results_button: str = "📋 Показать результаты"
    clear_all_filters_button: str = "🗑 Очистить все фильтры"
    clear_this_filter_button: str = "🗑 Очистить этот фильтр"
    apply_and_back_button: str = "✅ Применить и вернуться"
    back_to_menu_button: str = "⬅️ К фильтрам"

    # Results texts
    results_title: str = "📋 <b>Результаты поиска</b>"
    no_results_text: str = "😔 По вашим критериям ковры не найдены. Попробуйте изменить фильтры."
    results_summary_format: str = "Найдено ковров: <b>{count}</b>"

    # Error messages
    error_loading_filters: str = "❌ Ошибка загрузки фильтров"
    error_searching_carpets: str = "❌ Ошибка поиска ковров"

    def get_main_menu_text(self, current_filters: CarpetFilters, total_carpets: int) -> str:
        """Get main menu text with current filter state."""
        text = f"{self.welcome_title}\n\n"

        if current_filters.is_empty():
            text += self.welcome_text
            text += f"\n\n📊 Всего ковров в каталоге: <b>{total_carpets}</b>"
        else:
            text += "🎯 <b>Активные фильтры:</b>\n"
            filter_summary = current_filters.get_filter_summary()
            for filter_name, values in filter_summary.items():
                values_text = ", ".join(values[:3])  # Show first 3 values
                if len(values) > 3:
                    values_text += f" и еще {len(values) - 3}"
                text += f"• {filter_name}: {values_text}\n"

            text += f"\n📊 Найдено ковров: <b>{total_carpets}</b>"

        return text

    def get_filter_selection_text(
        self, filter_type: str, selected_count: int, total_options: int
    ) -> str:
        """Get filter selection text with selection info."""
        base_text = self.filter_selection_texts.get(filter_type, "Выберите опции:")

        if selected_count > 0:
            base_text += f"\n\n✅ Выбрано: <b>{selected_count}</b> из {total_options}"
        else:
            base_text += f"\n\n📊 Доступно опций: <b>{total_options}</b>"

        return base_text

    def format_carpet_result(self, carpet) -> str:
        """Format carpet information for results display."""
        colors = []
        if carpet.color_1:
            colors.append(carpet.color_1)
        if carpet.color_2:
            colors.append(carpet.color_2)
        if carpet.color_3:
            colors.append(carpet.color_3)

        colors_text = ", ".join(colors) if colors else "не указан"

        return (
            f"🆔 <b>ID:</b> {carpet.carpet_id}\n"
            f"📚 <b>Коллекция:</b> {carpet.collection}\n"
            f"📐 <b>Геометрия:</b> {carpet.geometry}\n"
            f"📏 <b>Размер:</b> {carpet.size}\n"
            f"🎨 <b>Цвета:</b> {colors_text}\n"
            f"✨ <b>Стиль:</b> {carpet.style}\n"
            f"💰 <b>Цена:</b> {carpet.price} руб.\n"
            f"📦 <b>Количество:</b> {carpet.quantity} шт."
        )


messages = CarpetSearchMessages()
