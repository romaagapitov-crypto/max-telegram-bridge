import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession

from config import TELEGRAM_TOKEN


logging.basicConfig(level=logging.INFO)


dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    print("Получен /start")

    await message.answer(
        "Бот работает через Tor!"
    )


@dp.message()
async def message_handler(message: Message):
    print("Получено сообщение:", message.text)

    await message.answer(
        f"Получил: {message.text}"
    )


async def main():

    session = AiohttpSession(
        proxy="socks5://127.0.0.1:9150"
    )

    bot = Bot(
        token=TELEGRAM_TOKEN,
        session=session
    )

    print("БОТ ЗАПУЩЕН")

    await dp.start_polling(bot)


def run_telegram_bot():
    asyncio.run(main())