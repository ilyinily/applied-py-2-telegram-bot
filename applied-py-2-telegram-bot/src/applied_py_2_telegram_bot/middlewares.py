from aiogram import BaseMiddleware
from aiogram.types import Message

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        print(f"Message received: {event.text}")
        return await handler(event.data)


