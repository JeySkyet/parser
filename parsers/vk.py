import os
import time
import logging
import aiohttp

logger = logging.getLogger(__name__)

VK_API_URL = "https://api.vk.com/method/wall.get"
VK_API_VERSION = "5.199"
DAYS_BACK = 2


async def search_vk_group(query: str) -> list[dict]:
    token = os.getenv("VK_ACCESS_TOKEN")
    group_id = os.getenv("VK_GROUP_ID", "baraholkanastolok")
    cutoff = time.time() - DAYS_BACK * 24 * 3600
    results = []

    params = {
        "domain": group_id,
        "count": 100,
        "access_token": token,
        "v": VK_API_VERSION,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(VK_API_URL, params=params) as resp:
                data = await resp.json()
        except Exception as e:
            logger.error(f"VK запрос не удался: {e}")
            return results

    error = data.get("error")
    if error:
        logger.error(f"VK API ошибка: {error}")
        return results

    posts = data.get("response", {}).get("items", [])
    logger.info(f"VK: получено {len(posts)} постов для запроса '{query}'")

    for post in posts:
        post_date = post.get("date", 0)
        if post_date < cutoff:
            continue

        text = post.get("text", "")
        if query.lower() not in text.lower():
            continue

        post_id = str(post.get("id", ""))
        owner_id = str(post.get("owner_id", ""))
        link = f"https://vk.com/wall{owner_id}_{post_id}"
        short_text = text[:200] + "..." if len(text) > 200 else text

        results.append({
            "id": post_id,
            "title": short_text,
            "price": "",
            "link": link,
            "source": "vk",
        })

    logger.info(f"VK: найдено {len(results)} совпадений для '{query}'")
    return results
