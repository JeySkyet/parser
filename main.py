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
    interval = int(os.getenv("CHECK_INTERVAL_MINUTES", "10"))

    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_new_items, "interval", minutes=interval, args=[bot])
    scheduler.start()

    logger.info(f"Бот запущен. Проверка каждые {interval} минут.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
