import os
import asyncio
import aiohttp
from dotenv import load_dotenv

from config import TELEGRAM_TOKEN
from database import get_telegram_chat_id, add_bridge

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession


load_dotenv()

MAX_TOKEN = os.getenv("MAX_TOKEN")

MAX_API_URL = "https://platform-api2.max.ru"

connect_states = set()


async def send_to_telegram(text, telegram_chat_id):
    session = AiohttpSession(
        proxy="socks5://127.0.0.1:9150"
    )

    bot = Bot(
        token=TELEGRAM_TOKEN,
        session=session
    )

    try:
        await bot.send_message(
            chat_id=telegram_chat_id,
            text=text
        )

        print("Сообщение отправлено в Telegram")

    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

    finally:
        await bot.session.close()


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


async def process_update(update):
    message = update.get("message")

    if not message:
        return

    recipient = message.get("recipient", {})
    max_chat_id = recipient.get("chat_id")
    chat_type = recipient.get("chat_type")

    body = message.get("body", {})
    text = body.get("text")

    sender = message.get("sender", {})
    sender_name = sender.get("name")
    sender_id = sender.get("user_id")

    if chat_type != "chat":
        return

    if not text:
        return

    text = text.strip()

    print("Сообщение из MAX-группы:", text)
    print("MAX CHAT ID:", max_chat_id)

    # /start
    if text == "/start":
        await send_to_max(
            "Привет!\n\n"
            "Я бот для подключения моста между Telegram и MAX.\n\n"
            "Команды:\n"
            "/start — информация о боте\n"
            "/connect — подключить группы",
            max_chat_id
        )

        return

    # /connect
    if text == "/connect":

        # Сначала проверяем существующий мост
        existing_telegram_chat_id = get_telegram_chat_id(
            max_chat_id
        )

        if existing_telegram_chat_id is not None:

            connect_states.discard(max_chat_id)

            await send_to_max(
                "Эта MAX-группа уже подключена.\n\n"
                f"MAX: {max_chat_id}\n"
                f"Telegram: {existing_telegram_chat_id}",
                max_chat_id
            )

            print(
                "MAX-группа уже подключена:",
                max_chat_id,
                existing_telegram_chat_id
            )

            return

        connect_states.add(max_chat_id)

        await send_to_max(
            "MAX-группа определена.\n\n"
            f"MAX chat id: {max_chat_id}\n\n"
            "Теперь отправь сюда ID Telegram-группы.",
            max_chat_id
        )

        print(
            "Начато подключение MAX-группы:",
            max_chat_id
        )

        return

    # Ожидаем Telegram chat id
    if max_chat_id in connect_states:

        try:
            telegram_chat_id = int(text)

        except ValueError:

            await send_to_max(
                "ID Telegram-группы должен быть числом.\n"
                "Попробуй ещё раз.",
                max_chat_id
            )

            return

        try:

            existing_telegram_chat_id = get_telegram_chat_id(
                max_chat_id
            )

            if existing_telegram_chat_id is not None:

                connect_states.discard(max_chat_id)

                await send_to_max(
                    "Эта MAX-группа уже подключена.",
                    max_chat_id
                )

                return

            add_bridge(
                sender_id,
                telegram_chat_id,
                max_chat_id
            )

            connect_states.discard(max_chat_id)

            await send_to_max(
                "Мост успешно подключён.\n\n"
                f"MAX: {max_chat_id}\n"
                f"Telegram: {telegram_chat_id}",
                max_chat_id
            )

            print(
                "Новый мост:",
                sender_id,
                telegram_chat_id,
                max_chat_id
            )

        except Exception as e:

            print(
                "Ошибка создания моста:",
                e
            )

            connect_states.discard(max_chat_id)

            await send_to_max(
                "Не удалось подключить мост.\n"
                "Возможно, эта группа уже подключена.",
                max_chat_id
            )

        return

    # Обычные сообщения MAX → Telegram

    telegram_chat_id = get_telegram_chat_id(
        max_chat_id
    )

    if telegram_chat_id is None:

        print(
            "Для этой MAX-группы мост не настроен"
        )

        return

    print(
        "TELEGRAM CHAT ID:",
        telegram_chat_id
    )

    if sender_name:
        text = f"{sender_name}: {text}"

    await send_to_telegram(
        text,
        telegram_chat_id
    )


async def get_updates():
    marker = None

    headers = {
        "Authorization": MAX_TOKEN
    }

    connector = aiohttp.TCPConnector(
        ssl=False
    )

    async with aiohttp.ClientSession(
        headers=headers,
        connector=connector
    ) as session:

        while True:

            params = {
                "timeout": 30,
                "limit": 100,
                "types": "message_created"
            }

            if marker is not None:
                params["marker"] = marker

            try:

                async with session.get(
                    f"{MAX_API_URL}/updates",
                    params=params
                ) as response:

                    data = await response.json()

                    if response.status != 200:

                        print(
                            "Ошибка MAX API:",
                            response.status,
                            data
                        )

                        await asyncio.sleep(5)
                        continue

                    marker = data.get("marker")

                    for update in data.get(
                        "updates",
                        []
                    ):
                        await process_update(
                            update
                        )

            except Exception as e:

                print(
                    "Ошибка подключения к MAX:",
                    e
                )

                await asyncio.sleep(5)


async def run_max_bot():

    if not MAX_TOKEN:

        print(
            "ОШИБКА: MAX_TOKEN не найден в .env"
        )

        return

    print("MAX-БОТ ЗАПУЩЕН")
    print("MAX → Telegram")

    await get_updates()


if __name__ == "__main__":
    asyncio.run(
        run_max_bot()
    )
