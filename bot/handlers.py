from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from db.database import add_subscription, remove_subscription, get_subscriptions
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
    if added:
        await message.answer(f'Подписка на "{game}" добавлена. Буду слать уведомления при новых объявлениях.')
    else:
        await message.answer(f'Ты уже подписан на "{game}".')


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
    await message.answer(f'Ищу "{game}" на Авито и в VK... (может занять до минуты)')

    results = await check_game_now(game)
    avito = results["avito"]
    vk = results["vk"]
    total = len(avito) + len(vk)

    if total == 0:
        await message.answer(f'По запросу "{game}" ничего не найдено.')
        return

    await message.answer(f'Найдено: Авито — {len(avito)}, VK — {len(vk)}')

    for item in (avito + vk)[:5]:
        source_label = "Авито" if item["source"] == "avito" else "VK Барахолка"
        price_line = f"\n💰 {item['price']}" if item.get("price") else ""
        text = (
            f"[{source_label}]\n"
            f"📌 {item['title']}{price_line}\n"
            f"🔗 {item['link']}"
        )
        await message.answer(text)
