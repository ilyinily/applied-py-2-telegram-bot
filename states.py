from aiogram.fsm.state import State, StatesGroup

class Food(StatesGroup):
    proteins = State()
    fats = State()
    carbohydrates = State()


class Profile(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()
    calories_target = State()

class Train(StatesGroup):
    activity = State()
    add_water = State()

