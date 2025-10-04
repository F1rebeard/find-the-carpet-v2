from aiogram.fsm.state import State, StatesGroup


class CarpetSearchStatesGroup(StatesGroup):
    """Dialog states for non-linear carpet filtering system."""

    main_menu = State()
    geometry_selection = State()
    size_selection = State()
    color_selection = State()
    style_selection = State()
    collection_selection = State()
    results = State()
