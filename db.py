import aiosqlite
from datetime import datetime

DB_PATH = "expenses.db"

DEFAULT_CATEGORIES = [
    ("🍔 Еда", "Еда"),
    ("🚗 Транспорт", "Транспорт"),
    ("🏠 Жильё", "Жильё"),
    ("💊 Здоровье", "Здоровье"),
    ("🎮 Развлечения", "Развлечения"),
    ("👕 Одежда", "Одежда"),
    ("📱 Связь", "Связь"),
    ("💪 Спорт", "Спорт"),
    ("🛒 Покупки", "Покупки"),
    ("📚 Образование", "Образование"),
]


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                name TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def ensure_default_categories(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM categories WHERE user_id = ?", (user_id,)
        )
        count = (await cursor.fetchone())[0]
        if count == 0:
            await db.executemany(
                "INSERT INTO categories (user_id, label, name) VALUES (?, ?, ?)",
                [(user_id, label, name) for label, name in DEFAULT_CATEGORIES],
            )
            await db.commit()


async def get_categories(user_id: int) -> list[tuple[int, str, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, label, name FROM categories WHERE user_id = ? ORDER BY id",
            (user_id,),
        )
        return await cursor.fetchall()


async def add_category(user_id: int, emoji: str, name: str):
    label = f"{emoji} {name}"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO categories (user_id, label, name) VALUES (?, ?, ?)",
            (user_id, label, name),
        )
        await db.commit()


async def delete_category(cat_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM categories WHERE id = ? AND user_id = ?", (cat_id, user_id)
        )
        await db.commit()


async def add_expense(user_id: int, description: str, amount: float, category: str):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO expenses (user_id, description, amount, category, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, description, amount, category, created_at),
        )
        await db.commit()


async def get_stats(user_id: int, period: str) -> list[tuple[str, float]]:
    if period == "today":
        date_filter = "DATE(created_at) = DATE('now', 'localtime')"
    elif period == "week":
        date_filter = "DATE(created_at) >= DATE('now', '-6 days', 'localtime')"
    elif period == "month":
        date_filter = "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', 'localtime')"
    else:
        date_filter = "1=1"

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE user_id = ? AND {date_filter}
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def get_history(user_id: int, limit: int = 10) -> list[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT description, amount, category, created_at
            FROM expenses
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return await cursor.fetchall()


async def delete_last_expense(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return False
        await db.execute("DELETE FROM expenses WHERE id = ?", (row[0],))
        await db.commit()
        return True
