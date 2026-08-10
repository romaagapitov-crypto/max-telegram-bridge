import asyncio
import logging
import os

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

from database import get_max_chat_id, add_bridge
from config import TELEGRAM_TOKEN


load_dotenv()

MAX_TOKEN = os.getenv("MAX_TOKEN")

MAX_API_URL = "https://platform-api2.max.ru"

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()


class ConnectState(StatesGroup):
    waiting_for_max_chat_id = State()


@dp.message(CommandStart())
async def start_handler(message: Message):
    print("Получен /start")

    await message.answer(
        "Привет!\n\n"
        "Я бот для подключения моста между Telegram и MAX.\n\n"
        "Добавь меня в Telegram-группу, "
        "которую хочешь подключить, "
        "и используй /connect."
    )


@dp.message(Command("connect"))
async def connect_handler(message: Message, state: FSMContext):
    if message.chat.type not in ("group", "supergroup"):
        await message.answer(
            "Команду /connect нужно использовать внутри Telegram-группы."
        )
        return

    existing_max_chat_id = get_max_chat_id(message.chat.id)

    if existing_max_chat_id is not None:
        await message.answer(
            "Эта Telegram-группа уже подключена.\n\n"
            f"Telegram: {message.chat.id}\n"
            f"MAX: {existing_max_chat_id}"
        )
        return

    await state.set_state(
        ConnectState.waiting_for_max_chat_id
    )

    await message.answer(
        "Telegram-группа определена.\n\n"
        f"Telegram chat id: {message.chat.id}\n\n"
        "Теперь отправь сюда ID группы MAX."
    )


@dp.message(ConnectState.waiting_for_max_chat_id)
async def receive_max_chat_id(
    message: Message,
    state: FSMContext
):
    if not message.text:
        return

    try:
        max_chat_id = int(message.text.strip())

    except ValueError:
        await message.answer(
            "ID группы MAX должен быть числом.\n"
            "Попробуй ещё раз."
        )
        return

    try:
        add_bridge(
            message.from_user.id,
            message.chat.id,
            max_chat_id
        )

        await state.clear()

        await message.answer(
            "Мост успешно подключён.\n\n"
            f"Telegram: {message.chat.id}\n"
            f"MAX: {max_chat_id}"
        )

        print(
            "Новый мост:",
            message.from_user.id,
            message.chat.id,
            max_chat_id
        )

    except Exception as e:
        print("Ошибка создания моста:", e)

        await state.clear()

        await message.answer(
            "Не удалось подключить мост.\n"
            "Возможно, эта группа уже подключена."
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
        max_chat_id
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