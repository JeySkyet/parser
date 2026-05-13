import logging
from aiogram import Bot

from db.database import get_all_subscriptions, is_seen, mark_seen
from parsers.avito import search_avito
from parsers.vk import search_vk_group

logger = logging.getLogger(__name__)


async def check_new_items(bot: Bot):
    subscriptions = await get_all_subscriptions()
    if not subscriptions:
        logger.info("Нет активных подписок, пропускаем проверку")
        return

    logger.info(f"Начинаем проверку для {len(subscriptions)} игр: {list(subscriptions.keys())}")

    for game_name, chat_ids in subscriptions.items():
        avito_items = await search_avito(game_name)
        vk_items = await search_vk_group(game_name)
        all_items = avito_items + vk_items

        logger.info(f"'{game_name}': Авито={len(avito_items)}, VK={len(vk_items)}")

        new_count = 0
        for item in all_items:
            source = item["source"]
            item_id = item["id"]

            if await is_seen(source, item_id):
                continue

            await mark_seen(source, item_id)
            new_count += 1

            source_label = "Авито" if source == "avito" else "VK Барахолка"
            text = (
                f"🆕 {game_name}\n"
                f"📌 {source_label}\n"
                f"🔗 {item['link']}"
            )

            for chat_id in chat_ids:
                try:
                    await bot.send_message(chat_id, text)
                except Exception as e:
                    logger.error(f"Ошибка отправки в {chat_id}: {e}")

        logger.info(f"'{game_name}': отправлено {new_count} новых уведомлений")


async def check_game_now(game_name: str) -> dict:
    """Немедленная проверка без отметки как просмотренное — для тестирования."""
    avito_items = await search_avito(game_name)
    vk_items = await search_vk_group(game_name)
    return {"avito": avito_items, "vk": vk_items}
