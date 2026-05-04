import re
from playwright.async_api import async_playwright


async def search_avito(query: str) -> list[dict]:
    url = f"https://www.avito.ru/rossiya?q={query.replace(' ', '+')}"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_selector("[data-marker='item']", timeout=15000)

            items = await page.query_selector_all("[data-marker='item']")
            for item in items[:20]:
                try:
                    item_id_attr = await item.get_attribute("data-item-id")
                    if not item_id_attr:
                        continue

                    title_el = await item.query_selector("[data-marker='item-title']")
                    title = await title_el.inner_text() if title_el else ""

                    if query.lower() not in title.lower():
                        continue

                    price_el = await item.query_selector("[data-marker='item-price']")
                    price = await price_el.inner_text() if price_el else "Цена не указана"
                    price = re.sub(r'\s+', ' ', price).strip()

                    link_el = await item.query_selector("a[data-marker='item-title']")
                    href = await link_el.get_attribute("href") if link_el else ""
                    link = f"https://www.avito.ru{href}" if href else ""

                    results.append({
                        "id": item_id_attr,
                        "title": title.strip(),
                        "price": price,
                        "link": link,
                        "source": "avito",
                    })
                except Exception:
                    continue
        except Exception:
            pass
        finally:
            await browser.close()

    return results
