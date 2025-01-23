from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import aiohttp
import re

from config import WEATHER_TOKEN
from states import *
import requests

router = Router()
user_profiles = {}


# Надо по-хорошему сбрасывать дневные показатели по выпитой воде, активности, погоде при наступлении нового дня. Понятно, как это делать (например, можно брать время суток из API по локации).

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
        "/profile - Обновить информацию о себе\n"
        "/log_food - Записать потреблённые калории\n"
        "/log_workout - Записать информацию о тренировке\n"
        "/log_water - Записать, сколько выпито воды\n"
        "/weather - Узнать погоду на сегодня\n"
        "/water_amount - Получить рекомендацию о том, сколько нужно сегодня выпить воды\n"
        "/check_progress - Узнать состояние по целям на день"
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
    user_id = message.from_user.id
    data = await state.get_data()
    await message.reply(f"Спасибо! Вы предоставили следующую информацию: {data}.")
    user_profiles[user_id] = data
    user_profiles[user_id]['water_goal'] = int(user_profiles[user_id]['weight']) * 30
    user_profiles[user_id]['base_calories'] = int(user_profiles[user_id]['weight']) * 10 + int(
        user_profiles[user_id]['height']) * 6.25 - int(user_profiles[user_id]['age']) * 5
    user_profiles[user_id]['todays_activity'] = 0
    user_profiles[user_id]['logged_water'] = 0
    user_profiles[user_id]['logged_calories'] = 0
    user_profiles[user_id]['burned_calories'] = 0
    await state.clear()


async def todays_weather(user_id):
    location_query = requests.get(url="http://api.openweathermap.org/geo/1.0/direct",
                                  params={'q': user_profiles[user_id]['city'],
                                          'appid': WEATHER_TOKEN,
                                          'limit': 5})
    user_profiles[user_id]['city_lat'] = location_query.json()[0]['lat']
    user_profiles[user_id]['city_lon'] = location_query.json()[0]['lon']
    location_weather = requests.get(url="https://api.openweathermap.org/data/2.5/weather",
                                    params={"lat": user_profiles[user_id]['city_lat'],
                                            "lon": user_profiles[user_id]['city_lon'],
                                            "units": "metric",
                                            "appid": WEATHER_TOKEN
                                            })
    user_profiles[user_id]['todays_weather'] = location_weather.json()['main']['temp']


@router.message(Command("weather"))
async def get_todays_weather(message: Message):
    user_id = message.from_user.id
    await todays_weather(user_id)
    await message.reply(f"В вашей локации {user_profiles[user_id]['city']} сегодня {user_profiles[user_id]['todays_weather']}")


@router.message(Command("water_amount"))
async def calculate_todays_water_amount(message: Message):
    user_id = message.from_user.id
    await todays_weather(user_id)
    user_profiles[user_id]['water_goal'] = user_profiles[user_id]['water_goal'] + (
        500 if user_profiles[user_id]['todays_weather'] > 25 else 0) + 500 * (
                                                               int(user_profiles[user_id]['todays_activity']) // 30)
    await message.reply(f"Сегодня вам рекомендуется выпить {user_profiles[user_id]['water_goal']} мл воды")


@router.message(Command("log_water"))
async def log_water(message: Message):
    user_id = message.from_user.id
    number_template = re.compile(r"\d.")  # Чтобы проверить, что после ввода команды действительно подаётся число.
    check_if_number = bool(number_template.match(message.text[11:]))
    if check_if_number:
        water_to_record = int(message.text[11:])
        user_profiles[user_id]['logged_water'] += water_to_record
        if user_profiles[user_id]['logged_water'] >= user_profiles[user_id]['water_goal']:
            await message.reply(f"Записал, выпито {message.text[11:]} мл воды. Дневная норма выполнена!")
        else:
            await message.reply(
                f"Записал, выпито {message.text[11:]} мл воды. До выполнения сегодняшней нормы осталось выпить {user_profiles[user_id]['water_goal'] - user_profiles[user_id]['logged_water']} мл.")
    else:
        await message.reply(
            f"Кажется, {message.text[11:]} не очень похоже на объём воды в миллилитрах, который можно употребить. Попробуйте заново.\n(Команда: /log_water XYZ, где XYZ - объём воды в миллилитрах для записи.")


# Выберем "другой способ" подачи информации об энергетической ценности еды. Пусть это будет болезненно для пользователя (мвахаха)
@router.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext):
    await message.reply(f"Так, кажется, вы съели {message.text[10:]}. Сколько в нём белков?")
    await state.set_state(Food.proteins)


@router.message(Food.proteins)
async def gather_proteins(message: Message, state: FSMContext):
    await state.update_data(proteins=int(message.text))
    await message.reply(f"Записал, значит, белков {message.text}. А жиров?")
    await state.set_state(Food.fats)


@ router.message(Food.fats)
async def gather_fats(message: Message, state: FSMContext):
    await state.update_data(fats=int(message.text))
    await message.reply(f"Записал, значит, жиров {message.text}. И углеводов, пожалуйста:")
    await state.set_state(Food.carbohydrates)


@router.message(Food.carbohydrates)
async def gather_carbohydrates(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(carbohydrates=int(message.text))
    data = await state.get_data()
    calories = data['proteins'] * 4 + data['fats'] * 9 + data['carbohydrates'] * 4
    user_profiles[user_id]['logged_calories'] += calories
    await message.reply(f"Углеводов, получается, {message.text}. Тогда калорийность выходит {calories} ккал. Добавил к употреблённому объёму (сейчас {user_profiles[user_id]['logged_calories']}) ккал.")
    if user_profiles[user_id]['logged_calories'] <= user_profiles[user_id]['base_calories']:
        await message.reply(f"До запланированного объёма потребления калорий осталось {user_profiles[user_id]['base_calories'] - user_profiles[user_id]['logged_calories']}.")
    else:
        await message.reply(f"Запланированный объём потребления калорий превышен на {abs(user_profiles[user_id]['base_calories'] - user_profiles[user_id]['logged_calories'])}.")
    await state.clear()


# Для записи тренировок тоже выберем способ "в лоб". Честно говоря, не хочется искать какие-то API, конвертирующие тренировки в условные калории, я в прошлом глубоко разочаровался в таких инструментах, поэтому для меня это болезненный опыт.
@router.message(Command("log_workout"))
async def log_workout(message: Message, state: FSMContext):
    await message.reply(f"Значит, вы выполнили тренировку {message.text[12:]}. Каков расход ккал за минуту тренировки?")
    await state.set_state(Train.activity)


@router.message(Train.activity)
async def gather_activity(message: Message, state: FSMContext):
    await state.update_data(calories_per_minute=int(message.text))
    await message.reply(f"Хорошо, спасибо. А как долго вы занимались, говорите?")
    await state.set_state(Train.add_water)


@ router.message(Train.add_water)
async def gather_add_water(message: Message, state: FSMContext):
    await state.update_data(train_length=int(message.text))
    user_id = message.from_user.id
    data = await state.get_data()
    add_water = 200 * (data['train_length'] // 30)
    await message.reply(f"За тренировку удалось сжечь {data['calories_per_minute'] * data['train_length']} ккал. Рекомендуется дополнительно выпить {add_water} мл воды.\nЧтобы не забыть, я скорректирую планы по тратам калорий и потреблению воды на день.")
    user_profiles[user_id]['burned_calories'] += (data['calories_per_minute'] * data['train_length'])
    user_profiles[user_id]['base_calories'] += user_profiles[user_id]['burned_calories']
    user_profiles[user_id]['water_goal'] += add_water
    await state.clear()


@router.message(Command("check_progress"))
async def check_progress(message: Message):
    user_id = message.from_user.id
    await message.reply(f"Прогресс:\n"
                        f"Вода:\n"
                        f"- Выпито: {user_profiles[user_id]['logged_water']} мл\n"
                        f"- Осталось: {user_profiles[user_id]['water_goal'] - user_profiles[user_id]['logged_water']} мл\n"
                        f"Калории:\n"
                        f"- Потреблено: {user_profiles[user_id]['logged_calories']} из {user_profiles[user_id]['base_calories']} ккал\n"
                        f"- Сожжено: {user_profiles[user_id]['burned_calories']} ккал\n"
                        f"- Баланс: {user_profiles[user_id]['logged_calories'] - user_profiles[user_id]['burned_calories']} ккал")


