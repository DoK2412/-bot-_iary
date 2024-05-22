from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    note = State()
    letter = State()
    name_notepad = State()
    notepad = State()
