import os
import aiohttp


VK_API_URL = "https://api.vk.com/method/wall.get"
VK_API_VERSION = "5.199"


async def search_vk_group(query: str) -> list[dict]:
    token = os.getenv("VK_ACCESS_TOKEN")
    group_id = os.getenv("VK_GROUP_ID", "baraholkanastolok")
    results = []

    params = {
        "domain": group_id,
        "count": 50,
        "access_token": token,
        "v": VK_API_VERSION,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(VK_API_URL, params=params) as resp:
                data = await resp.json()

            posts = data.get("response", {}).get("items", [])
            for post in posts:
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
        except Exception:
            pass

    return results
