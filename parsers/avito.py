import logging
import os
import re
from urllib.parse import quote

from curl_cffi import requests as cffi_requests

logger = logging.getLogger(__name__)

_BASE_URL = (
    "https://www.avito.ru/all/sport_i_otdyh/nastolnye_i_kartochnye_igry"
    "-ASgBAgICAUTKAoZP?cd=1"
)

_ITEM_RE = re.compile(r'"id":(\d{7,}),[^{]*?"urlPath":"([^"?]+)[^{]*?"title":"([^"]+)"')


def _proxy() -> dict | None:
    user = os.getenv("PROXY_USER")
    password = os.getenv("PROXY_PASSWORD")
    if not user or not password:
        return None
    return {"https": f"socks5://{user}:{password}@pool.proxy.market:10999"}


async def search_avito(query: str) -> list[dict]:
    try:
        return _search(query)
    except Exception as e:
        logger.error(f"Авито: ошибка для '{query}': {e}")
        return []


def _search(query: str) -> list[dict]:
    proxy = _proxy()
    session = cffi_requests.Session(impersonate="chrome124")

    resp = session.get(f"{_BASE_URL}&q={quote(query)}", proxies=proxy, timeout=20)
    resp.raise_for_status()

    lq = query.lower()
    results = []
    seen = set()
    for m in _ITEM_RE.finditer(resp.text):
        item_id = m.group(1)
        if item_id in seen:
            continue
        title = m.group(3)
        if lq not in title.lower():
            continue
        seen.add(item_id)
        url_path = m.group(2)
        results.append({
            "id": item_id,
            "title": title,
            "price": "",
            "link": f"https://www.avito.ru{url_path}",
            "source": "avito",
        })

    logger.info(f"Авито: найдено {len(results)} для '{query}'")
    return results
