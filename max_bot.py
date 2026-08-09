import os
import asyncio
import aiohttp
from dotenv import load_dotenv

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from config import TELEGRAM_TOKEN


load_dotenv()

MAX_TOKEN = os.getenv("MAX_TOKEN")

MAX_API_URL = "https://platform-api2.max.ru"

TELEGRAM_CHAT_ID = -5471339047
MAX_CHAT_ID = -77682869790919

async def send_to_telegram(text):
    session = AiohttpSession(
        proxy="socks5://127.0.0.1:9150"
    )

    bot = Bot(
        token=TELEGRAM_TOKEN,
        session=session
    )

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f"[MAX] {text}"
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
    chat_id = recipient.get("chat_id")
    chat_type = recipient.get("chat_type")

    body = message.get("body", {})
    text = body.get("text")

    # Обрабатываем только нашу группу MAX
    if chat_type != "chat":
        return

    if chat_id != MAX_CHAT_ID:
        return

    if not text:
        return

    print("Сообщение из MAX-группы:", text)

    await send_to_telegram(text)


async def get_updates():
    marker = None

    headers = {
        "Authorization": MAX_TOKEN
    }

    # Пока оставляем SSL отключённым,
    # поскольку с проверкой сертификата MAX API не подключается
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