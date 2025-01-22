import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import router
from middlewares import LoggingMiddleware
import socket

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_routers(router)
dp.message.middleware(LoggingMiddleware())

def create_socket(host="localhost", port=12345):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host,port))
    s.listen(5)
    print(f"Socket is listening on {host}:{port}")

    while True:
        c, addr = s.accept()
        print(f"Got connection from {addr}")
        c.send(b"Thank you for connecting")
        c.close()

async def main():
    print("Бот запущен!")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    create_socket()















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