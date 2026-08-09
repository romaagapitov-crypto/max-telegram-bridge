import asyncio
import logging
import os

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv

from config import TELEGRAM_TOKEN


load_dotenv()

MAX_TOKEN = os.getenv("MAX_TOKEN")

MAX_API_URL = "https://platform-api2.max.ru"

TELEGRAM_CHAT_ID = -5471339047
MAX_CHAT_ID = -77682869790919

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    print("Получен /start")

    await message.answer(
        "Бот работает через Tor!"
    )


async def send_to_max(text):
    headers = {
        "Authorization": MAX_TOKEN,
        "Content-Type": "application/json"
    }

    data = {
        "text": text
    }

    params = {
        "chat_id": MAX_CHAT_ID
    }

    # Временно отключаем SSL-проверку,
    # как и в max_bot.py
    connector = aiohttp.TCPConnector(ssl=False)

    try:
        async with aiohttp.ClientSession(
            headers=headers,
            connector=connector
        ) as session:

            async with session.post(
                f"{MAX_API_URL}/messages",
                params=params,
                json=data
            ) as response:

                result = await response.json()

                if response.status != 200:
                    print(
                        "Ошибка отправки в MAX:",
                        response.status,
                        result
                    )
                    return

                print("Сообщение отправлено в MAX")

    except Exception as e:
        print("Ошибка подключения к MAX:", e)


@dp.message()
async def message_handler(message: Message):

    print("Получено сообщение:", message.text)
    print("CHAT ID:", message.chat.id)
    print("CHAT TYPE:", message.chat.type)

    # Обрабатываем только нашу Telegram-группу
    if message.chat.id != TELEGRAM_CHAT_ID:
        return

    if not message.text:
        return

    print("Отправляем в MAX:", message.text)

    await send_to_max(
        f"[Telegram] {message.text}"
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
    print("Telegram → MAX")

    await dp.start_polling(bot)


async def run_telegram_bot_async():
    await main()


def run_telegram_bot():
    asyncio.run(run_telegram_bot_async())