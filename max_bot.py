import aiohttp
import asyncio
from config import MAX_TOKEN


API = "https://platform-api2.max.ru"


async def get_updates():

    headers = {
        "Authorization": MAX_TOKEN
    }

    marker = None

    async with aiohttp.ClientSession() as session:

        while True:

            params = {
                "timeout": 30,
                "marker": marker,
                "types": "message_created"
            }

            async with session.get(
                f"{API}/updates",
                headers=headers,
                params=params
            ) as r:

                data = await r.json()

                marker = data.get("marker")

                for update in data.get("updates", []):

                    print(update)

            await asyncio.sleep(1)