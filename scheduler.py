import logging
from aiogram import Bot

from db.database import get_all_subscriptions, is_seen, mark_seen
from parsers.avito import search_avito
from parsers.vk import search_vk_group

logger = logging.getLogger(__name__)


async def check_new_items(bot: Bot):
    subscriptions = await get_all_subscriptions()
    if not subscriptions:
        return

    for game_name, chat_ids in subscriptions.items():
        avito_items = await search_avito(game_name)
        vk_items = await search_vk_group(game_name)

        for item in avito_items + vk_items:
            source = item["source"]
            item_id = item["id"]

            if await is_seen(source, item_id):
                continue

            await mark_seen(source, item_id)

            source_label = "Авито" if source == "avito" else "VK Барахолка"
            price_line = f"\n💰 {item['price']}" if item.get("price") else ""
            text = (
                f"🆕 Новое объявление [{source_label}]\n"
                f"📌 {item['title']}{price_line}\n"
                f"🔗 {item['link']}"
            )

            for chat_id in chat_ids:
                try:
                    await bot.send_message(chat_id, text)
                except Exception as e:
                    logger.error(f"Ошибка отправки в {chat_id}: {e}")
