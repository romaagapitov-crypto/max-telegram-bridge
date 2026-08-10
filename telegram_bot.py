import asyncio
import logging
import os

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv
from database import get_max_chat_id
from config import TELEGRAM_TOKEN


load_dotenv()

MAX_TOKEN = os.getenv("MAX_TOKEN")

MAX_API_URL = "https://platform-api2.max.ru"

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    print("Получен /start")

    await message.answer(
        "Бот работает через Tor!"
    )


async def send_to_max(text, max_chat_id):
    headers = {
        "Authorization": MAX_TOKEN,
        "Content-Type": "application/json"
    }

    data = {
        "text": text
    }

    params = {
        "chat_id": max_chat_id
    }

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

    if not message.text:
        return

    max_chat_id = get_max_chat_id(message.chat.id)

    if max_chat_id is None:
        print("Для этой Telegram-группы мост не настроен")
        return

    print("MAX CHAT ID:", max_chat_id)
    print("Отправляем в MAX:", message.text)

    sender_name = message.from_user.first_name

    if message.from_user.last_name:
        sender_name += f" {message.from_user.last_name}"

    await send_to_max(
        f"{sender_name}: {message.text}",
        max_chat_id)


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