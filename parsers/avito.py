import asyncio
import json
import logging
import os
import random
import re

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

ITEMS_ENDPOINT = "/web/1/js/items"
_PROXY_HOST = "pool.proxy.market"
_PROXY_PORTS = range(10000, 11000)
_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US'] });
window.chrome = { runtime: {} };
"""


async def search_avito(query: str) -> list[dict]:
    try:
        return await _playwright_search(query)
    except Exception as e:
        logger.error(f"Авито (Playwright): ошибка для '{query}': {e}")
        return []


def _proxy_config() -> dict | None:
    user = os.getenv("PROXY_USER")
    password = os.getenv("PROXY_PASSWORD")
    if not user or not password:
        return None
    port = random.choice(list(_PROXY_PORTS))
    return {"server": f"http://{_PROXY_HOST}:{port}", "username": user, "password": password}


async def _playwright_search(query: str) -> list[dict]:
    proxy = _proxy_config()
    if not proxy:
        logger.warning("Авито: PROXY_USER/PROXY_PASSWORD не заданы, работаем без прокси")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
            proxy=proxy,
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.6367.208 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            extra_http_headers={"Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8"},
        )
        await context.add_init_script(_STEALTH_SCRIPT)

        captured: list[dict] = []
        ready = asyncio.Event()

        async def on_response(response):
            if ITEMS_ENDPOINT in response.url and not ready.is_set():
                try:
                    data = await response.json()
                    captured.extend(_parse_items_json(data, query))
                except Exception as e:
                    logger.debug(f"Авито: не удалось распарсить /items: {e}")
                finally:
                    ready.set()

        page = await context.new_page()
        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type in ("image", "media", "font", "stylesheet")
            else route.continue_())
        page.on("response", on_response)

        await page.goto(
            f"https://www.avito.ru/rossiya?q={query}&s=104",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await asyncio.sleep(random.uniform(1.5, 3.0))

        try:
            await asyncio.wait_for(ready.wait(), timeout=12.0)
        except asyncio.TimeoutError:
            logger.warning(f"Авито: XHR /items не перехвачен для '{query}', парсим HTML")
            captured.extend(_parse_items_html(await page.content(), query))

        await browser.close()
        logger.info(f"Авито (Playwright): найдено {len(captured)} для '{query}'")
        return captured


def _parse_items_json(data: dict, query: str) -> list[dict]:
    results = []
    lq = query.lower()
    raw = data.get("items") or data.get("result", {}).get("items") or []
    for item in raw:
        val = item.get("value", item) if isinstance(item, dict) else item
        title = val.get("title") or val.get("name") or ""
        if not title or lq not in title.lower():
            continue
        item_id = str(val.get("id") or "")
        price_val = (val.get("priceDetailed") or {}).get("value") or val.get("price") or ""
        price = f"{price_val} ₽" if price_val else ""
        url_path = val.get("urlPath") or val.get("url") or ""
        link = f"https://www.avito.ru{url_path}" if url_path.startswith("/") else url_path
        if not item_id:
            continue
        results.append({"id": item_id, "title": title, "price": price, "link": link, "source": "avito"})
    return results


def _parse_items_html(html: str, query: str) -> list[dict]:
    results = []
    lq = query.lower()
    for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', html):
        try:
            data = json.loads(m.group(1))
            items = data if isinstance(data, list) else data.get("itemListElement", [])
            for item in items:
                thing = item.get("item", item)
                name = thing.get("name", "")
                url = thing.get("url", "")
                if not url or lq not in name.lower():
                    continue
                price_raw = thing.get("offers", {}).get("price", "")
                price = f"{price_raw} ₽" if price_raw else ""
                id_m = re.search(r"_(\d+)$", url)
                results.append({
                    "id": id_m.group(1) if id_m else url,
                    "title": name,
                    "price": price,
                    "link": url,
                    "source": "avito",
                })
        except Exception:
            continue
    return results
