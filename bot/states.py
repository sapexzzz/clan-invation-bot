from aiogram.fsm.state import State, StatesGroup


class ApplicationStates(StatesGroup):
    waiting_for_id = State()
    waiting_for_nickname = State()
    waiting_for_rank_comp = State()
    waiting_for_rank_allies = State()
    waiting_for_rank_duels = State()
    waiting_for_hours = State()
    waiting_for_kd = State()
    confirm = State()
    edit_field_choice = State()
