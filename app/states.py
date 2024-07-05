from aiogram.fsm.state import State, StatesGroup


class Ai(StatesGroup):
    question = State()
    answer = State()