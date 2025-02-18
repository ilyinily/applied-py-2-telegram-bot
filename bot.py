import asyncio
from aiogram import Bot, Dispatcher
from config import *
from handlers import router
from middlewares import LoggingMiddleware
import socket

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_routers(router)
dp.message.middleware(LoggingMiddleware())


async def main():
    print("Бот запущен!")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())















# Всё ниже взято из документации

# , types)
# from aiogram.filters.command import Command
#
# from constants import *
#
# # Включаем логирование, чтобы не пропустить важные сообщения
# logging.basicConfig(level=logging.INFO)
# # Создаём объект бота
# bot = Bot(token=TOKEN)
#
# # Хэндлер на команду /start
# @dp.message(Command("start"))
# async def cmd_start(message: types.Message):
#     await message.answer("Hello!")
#
# # Запуск процесса поллинга новых апдейтов
# async def main():
#     await dp.start_polling(bot)
#
# if __name__ == "__main__":
#     asyncio.run(main())