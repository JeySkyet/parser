import aiosqlite

DB_PATH = "parser.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                game_name TEXT NOT NULL,
                UNIQUE(chat_id, game_name)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS seen_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                item_id TEXT NOT NULL,
                UNIQUE(source, item_id)
            )
        """)
        await db.commit()


async def add_subscription(chat_id: int, game_name: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO subscriptions (chat_id, game_name) VALUES (?, ?)",
                (chat_id, game_name.lower().strip())
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def remove_subscription(chat_id: int, game_name: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM subscriptions WHERE chat_id = ? AND game_name = ?",
            (chat_id, game_name.lower().strip())
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_subscriptions(chat_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT game_name FROM subscriptions WHERE chat_id = ?", (chat_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_all_subscriptions() -> dict[str, list[int]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT chat_id, game_name FROM subscriptions")
        rows = await cursor.fetchall()
    result: dict[str, list[int]] = {}
    for chat_id, game_name in rows:
        result.setdefault(game_name, []).append(chat_id)
    return result


async def is_seen(source: str, item_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM seen_items WHERE source = ? AND item_id = ?",
            (source, item_id)
        )
        return await cursor.fetchone() is not None


async def mark_seen(source: str, item_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO seen_items (source, item_id) VALUES (?, ?)",
                (source, item_id)
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            pass
