from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from db.database import add_subscription, remove_subscription, get_subscriptions, mark_seen
from scheduler import check_game_now

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я слежу за объявлениями на Авито и в VK-группе Барахолка Настолок.\n\n"
        "Команды:\n"
        "/subscribe <название игры> — подписаться на поиск\n"
        "/unsubscribe <название игры> — отписаться\n"
        "/list — мои подписки\n"
        "/check <название игры> — немедленно проверить объявления"
    )


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Укажи название игры: /subscribe Каркассон")
        return

    game = parts[1].strip()
    added = await add_subscription(message.chat.id, game)
    if not added:
        await message.answer(f'Ты уже подписан на "{game}".')
        return

    await message.answer(f'Подписка на "{game}" добавлена. Собираю текущие объявления...')

    results = await check_game_now(game)
    all_items = results["avito"] + results["vk"]

    for item in all_items:
        await mark_seen(item["source"], item["id"])

    await message.answer(
        f'Готово! Нашёл {len(all_items)} текущих объявлений — они сохранены.\n'
        f'Буду присылать только новые.'
    )


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Укажи название игры: /unsubscribe Каркассон")
        return

    game = parts[1].strip()
    removed = await remove_subscription(message.chat.id, game)
    if removed:
        await message.answer(f'Подписка на "{game}" удалена.')
    else:
        await message.answer(f'Подписки на "{game}" не найдено.')


@router.message(Command("list"))
async def cmd_list(message: Message):
    subs = await get_subscriptions(message.chat.id)
    if not subs:
        await message.answer("У тебя нет активных подписок.")
    else:
        text = "Твои подписки:\n" + "\n".join(f"• {s}" for s in subs)
        await message.answer(text)


@router.message(Command("check"))
async def cmd_check(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Укажи название игры: /check Каркассон")
        return

    game = parts[1].strip()
    await message.answer(f'Ищу "{game}" на Авито и в VK...')

    results = await check_game_now(game)
    avito = results["avito"]
    vk = results["vk"]
    total = len(avito) + len(vk)

    if total == 0:
        await message.answer(f'По запросу "{game}" ничего не найдено.')
        return

    await message.answer(f'Найдено: Авито — {len(avito)}, VK — {len(vk)}. Показываю первые 5:')

    for item in (avito + vk)[:5]:
        source_label = "Авито" if item["source"] == "avito" else "VK Барахолка"
        await message.answer(
            f'🔍 {game}\n'
            f'📌 {source_label}\n'
            f'🔗 {item["link"]}'
        )
