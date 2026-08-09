import asyncio

from telegram_bot import run_telegram_bot_async
from max_bot import run_max_bot


async def main():
    print("MAX ↔ TELEGRAM МОСТ ЗАПУЩЕН")

    await asyncio.gather(
        run_telegram_bot_async(),
        run_max_bot()
    )


if __name__ == "__main__":
    asyncio.run(main())