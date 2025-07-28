from aiogram.fsm.state import State, StatesGroup


class RegistrationStatesGroup(StatesGroup):
    """The registration dialog states for new user registration process."""

    first_name = State()
    last_name = State()
    email = State()
    phone = State()
    from_whom = State()
    confirmation = State()
