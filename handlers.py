from http.cookiejar import user_domain_match

from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import aiohttp

from config import WEATHER_TOKEN
from states import *
import requests

router = Router()
user_profiles = []


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


# FSM: ввод данных профиля
@router.message(Command("profile"))
async def profile_start(message: Message, state: FSMContext):
    await message.reply("Укажите ваш вес в килограммах")
    await state.set_state(Profile.weight)


@router.message(Profile.weight)
async def gather_weight(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.reply("А теперь ваш рост в сантиметрах")
    await state.set_state(Profile.height)


@router.message(Profile.height)
async def gather_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.reply("И возраст (в годах)")
    await state.set_state(Profile.age)


@router.message(Profile.age)
async def gather_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.reply("Сколько минут вы хотите тренироваться в день?")
    await state.set_state(Profile.activity)


@router.message(Profile.activity)
async def gather_city(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await message.reply("В каком городе вы живёте?")
    await state.set_state(Profile.city)


@router.message(Profile.city)
async def gather_activity(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    user_id = message.from_user
    data = await state.get_data()
    await message.reply(f"Спасибо! Вы предоставили следующую информацию: {data}.")
    user_profiles[f"{user_id}"] = data
    await state.clear()


async def todays_weather(user_id):
    location_query = await requests.get(url="http://api.openweathermap.org/geo/1.0/direct",
                                  params={'q': user_profiles[user_id],
                                          'appid': WEATHER_TOKEN,
                                          'limit': 5})
    user_profiles[user_id]["city_lat"] = location_query.json()[0]["lat"]
    user_profiles[user_id]["city_lon"] = location_query.json()[0]["lon"]
    location_weather = await requests.get(url="https://api.openweathermap.org/data/2.5/weather",
                                    params={"lat": user_profiles[user_id]["city_lat"],
                                            "lon": user_profiles[user_id]["city_lon"],
                                            "units": "metric",
                                            "appid": WEATHER_TOKEN
                                    })
    user_profiles[user_id]["todays_weather"] = location_weather.json()["main"]["temp"]
    print(f"For user {user_id} the weather today is {user_profiles[user_id]["todays_weather"]}")

@router.message(Command("weather"))
async def get_todays_weather(message: Message):
    user_id = message.from_user
    await todays_weather(user_id)
    await message.reply(f"В вашей локации {user_profiles[user_id]["city"]} сегодня {user_profiles[user_id]["todays_weather"]}")


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
