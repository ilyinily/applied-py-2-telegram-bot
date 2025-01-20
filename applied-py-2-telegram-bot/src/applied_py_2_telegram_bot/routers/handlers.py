from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import aiohttp
from ..states import Form


router = Router()


# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")


# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/form - Пример диалога\n"
        "/keyboard - Пример кнопок\n"
        "/joke - Получить случайную шутку\n"
    )


# Обработчик команды /keyboard с инлайн-кнопками
@router.message(Command("keyboard"))
async def show_keyboard(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Button One", callback_data="btn1")],
            [InlineKeyboardButton(text="Button Two", callback_data="btn2")],
        ]
    )
    await message.reply("Pick an option:", reply_markup=keyboard)


@router.callback_query()
async def handle_callbacks(callback_query):
    if callback_query.data == "btn1":
        await callback_query.message.reply("Button 1 Pressed")
    if callback_query.data == "btn2":
        await callback_query.message.reply("Button 2 Pressed")


# FSM: диалог с пользователем
@router.message(Command("form"))
async def start_form(message: Message, state: FSMContext):
    await message.reply("What is your name?")
    await state.set_state(Form.name)


@router.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("How old are you?")
    await state.set_state(Form.age)


@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    age = message.text
    await message.reply(f"Hello {name}, you are {age} years old.")
    await state.clear()


@router.message(Command("joke"))
async def get_joke(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.chucknorris.io/jokes/random") as response:
            joke = await response.json()
            await message.reply(joke["value"])




