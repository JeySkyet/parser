import logging
import os

from curl_cffi import requests as cffi_requests

logger = logging.getLogger(__name__)

_ITEMS_URL = "https://www.avito.ru/web/1/js/items"
_HOME_URL = "https://www.avito.ru/"
_session: cffi_requests.Session | None = None


def _get_session() -> cffi_requests.Session:
    global _session
    if _session is None:
        _session = cffi_requests.Session(impersonate="chrome124")
    return _session


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
    session = _get_session()

    session.get(_HOME_URL, proxies=proxy, timeout=15)

    params = {
        "categoryId": 9,
        "locationId": 0,
        "query": query,
        "page": 1,
        "sort": "date",
    }
    headers = {
        "Referer": f"https://www.avito.ru/rossiya?q={query}",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json",
    }
    resp = session.get(_ITEMS_URL, params=params, headers=headers, proxies=proxy, timeout=15)
    resp.raise_for_status()

    data = resp.json()
    items = data.get("catalog", {}).get("items", [])
    lq = query.lower()

    results = []
    for item in items:
        title = item.get("title", "")
        if lq not in title.lower():
            continue
        item_id = str(item.get("id", ""))
        price = item.get("priceDetailed", {}).get("fullString", "")
        url_path = item.get("urlPath", "")
        link = f"https://www.avito.ru{url_path.split('?')[0]}" if url_path else ""
        if not item_id:
            continue
        results.append({"id": item_id, "title": title, "price": price, "link": link, "source": "avito"})

    logger.info(f"Авито: найдено {len(results)} для '{query}'")
    return results
