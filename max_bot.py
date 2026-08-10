import os
import asyncio
import aiohttp
from dotenv import load_dotenv

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from config import TELEGRAM_TOKEN
from database import get_telegram_chat_id

load_dotenv()

MAX_TOKEN = os.getenv("MAX_TOKEN")

MAX_API_URL = "https://platform-api2.max.ru"


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

    if chat_type != "chat":
        return

    if not text:
        return

    telegram_chat_id = get_telegram_chat_id(max_chat_id)

    if telegram_chat_id is None:
        print("Для этой MAX-группы мост не настроен")
        return

    print("Сообщение из MAX-группы:", text)
    print("MAX CHAT ID:", max_chat_id)
    print("TELEGRAM CHAT ID:", telegram_chat_id)

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

    connector = aiohttp.TCPConnector(ssl=False)

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

                    for update in data.get("updates", []):
                        await process_update(update)

            except Exception as e:
                print("Ошибка подключения к MAX:", e)
                await asyncio.sleep(5)


async def run_max_bot():
    if not MAX_TOKEN:
        print("ОШИБКА: MAX_TOKEN не найден в .env")
        return

    print("MAX-БОТ ЗАПУЩЕН")
    print("MAX → Telegram")

    await get_updates()


if __name__ == "__main__":
    asyncio.run(run_max_bot())