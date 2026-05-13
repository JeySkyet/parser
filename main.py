import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from bot.handlers import router
from db.database import init_db
from scheduler import check_new_items

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main():
    await init_db()

    token = os.getenv("TELEGRAM_TOKEN")

    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)

    scheduler = AsyncIOScheduler()
    # 07:30–00:00: каждые 10 минут
    scheduler.add_job(check_new_items, "cron", hour="8-23", minute="*/10", args=[bot])
    scheduler.add_job(check_new_items, "cron", hour="7", minute="30,40,50", args=[bot])
    # 00:00–02:00: раз в час
    scheduler.add_job(check_new_items, "cron", hour="0,1", minute="0", args=[bot])
    # 02:00–07:30: один раз в 02:00
    scheduler.add_job(check_new_items, "cron", hour="2", minute="0", args=[bot])
    scheduler.start()

    logger.info("Бот запущен. Расписание: 07:30-00:00 каждые 10 мин, 00:00-02:00 раз в час, 02:00-07:30 однократно.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
