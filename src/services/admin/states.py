# src/services/admin/users_managment/states.py
from aiogram.fsm.state import State, StatesGroup


class PendingUsersStatesGroup(StatesGroup):
    """States for pending users management dialog."""

    users_list = State()
    user_details = State()
    approve_role = State()
    decline_reason = State()


class AddUserStatesGroup(StatesGroup):
    """States for adding user manually dialog."""

    telegram_id = State()
    username = State()
    first_name = State()
    last_name = State()
    email = State()
    role = State()
    confirmation = State()


class BanUserStatesGroup(StatesGroup):
    """States for banning user dialog."""

    telegram_id = State()
    reason = State()
    confirmation = State()


class BroadcastStatesGroup(StatesGroup):
    """States for broadcasting message dialog."""

    message = State()
    confirmation = State()
