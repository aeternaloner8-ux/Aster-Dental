import asyncio
import re
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import db


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class AddCategory(StatesGroup):
    waiting_emoji = State()
    waiting_name = State()


# ─── helpers ──────────────────────────────────────────────────────────────────

def categories_keyboard(categories: list, expense_key: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for cat_id, label, _ in categories:
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=f"cat:{cat_id}:{expense_key}",
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="stats:today"),
            InlineKeyboardButton(text="📆 Неделя", callback_data="stats:week"),
            InlineKeyboardButton(text="🗓 Месяц", callback_data="stats:month"),
        ]
    ])


def manage_categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    buttons = []
    for cat_id, label, _ in categories:
        buttons.append([
            InlineKeyboardButton(text=label, callback_data="noop"),
            InlineKeyboardButton(text="🗑", callback_data=f"delcat:{cat_id}"),
        ])
    buttons.append([InlineKeyboardButton(text="➕ Добавить категорию", callback_data="addcat")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# pending expenses: key -> (description, amount)
pending: dict[str, tuple[str, float]] = {}


def make_key(user_id: int, description: str, amount: float) -> str:
    return f"{user_id}_{description}_{amount}"


# ─── /start ───────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await db.ensure_default_categories(message.from_user.id)
    await message.answer(
        "👋 Привет! Я бот для учёта расходов.\n\n"
        "Просто напиши расход в формате:\n"
        "<b>название сумма</b>\n\n"
        "Например: <code>кофе 300</code> или <code>такси 1000</code>\n\n"
        "Команды:\n"
        "/stats — статистика\n"
        "/history — последние 10 расходов\n"
        "/categories — управление категориями\n"
        "/undo — удалить последний расход",
        parse_mode="HTML",
    )


# ─── expense input ────────────────────────────────────────────────────────────

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_expense(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == AddCategory.waiting_emoji:
        await process_emoji(message, state)
        return
    if current_state == AddCategory.waiting_name:
        await process_name(message, state)
        return

    text = message.text.strip()
    match = re.match(r"^(.+?)\s+(\d+(?:[.,]\d+)?)$", text)
    if not match:
        await message.answer(
            "Не понял 🤔 Напиши в формате: <b>название сумма</b>\n"
            "Например: <code>кофе 300</code>",
            parse_mode="HTML",
        )
        return

    description = match.group(1).strip()
    amount = float(match.group(2).replace(",", "."))
    user_id = message.from_user.id

    await db.ensure_default_categories(user_id)
    categories = await db.get_categories(user_id)

    key = make_key(user_id, description, amount)
    pending[key] = (description, amount)

    await message.answer(
        f"💸 <b>{description}</b> — {amount:,.0f} руб.\n\nВыбери категорию:".replace(",", " "),
        reply_markup=categories_keyboard(categories, key),
        parse_mode="HTML",
    )


# ─── category chosen ──────────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("cat:"))
async def category_chosen(call: CallbackQuery):
    _, cat_id_str, *key_parts = call.data.split(":")
    expense_key = ":".join(key_parts)

    if expense_key not in pending:
        await call.answer("Расход устарел, введи заново.", show_alert=True)
        await call.message.delete()
        return

    description, amount = pending.pop(expense_key)
    user_id = call.from_user.id

    categories = await db.get_categories(user_id)
    cat_map = {str(c[0]): c for c in categories}
    cat = cat_map.get(cat_id_str)
    if not cat:
        await call.answer("Категория не найдена.", show_alert=True)
        return

    category_label = cat[1]
    await db.add_expense(user_id, description, amount, category_label)

    await call.message.edit_text(
        f"✅ Записано!\n\n"
        f"📝 {description}\n"
        f"💰 {amount:,.0f} руб.\n"
        f"🏷 {category_label}".replace(",", " "),
        parse_mode="HTML",
    )
    await call.answer()


@dp.callback_query(F.data == "cancel")
async def cancel_expense(call: CallbackQuery):
    await call.message.delete()
    await call.answer("Отменено")


@dp.callback_query(F.data == "back")
async def go_back(call: CallbackQuery):
    await call.message.delete()
    await call.answer()


@dp.callback_query(F.data == "noop")
async def noop(call: CallbackQuery):
    await call.answer()


# ─── /stats ───────────────────────────────────────────────────────────────────

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    await message.answer("📊 Выбери период:", reply_markup=stats_keyboard())


@dp.callback_query(F.data.startswith("stats:"))
async def show_stats(call: CallbackQuery):
    period = call.data.split(":")[1]
    user_id = call.from_user.id
    rows = await db.get_stats(user_id, period)

    period_names = {"today": "сегодня", "week": "за 7 дней", "month": "за месяц"}
    title = period_names.get(period, "")

    if not rows:
        await call.message.edit_text(f"Расходов {title} нет.")
        await call.answer()
        return

    total = sum(r[1] for r in rows)
    lines = [f"📊 <b>Расходы {title}:</b>\n"]
    for category, amount in rows:
        lines.append(f"{category} — <b>{amount:,.0f}</b> руб.".replace(",", " "))
    lines.append(f"\n💰 Итого: <b>{total:,.0f}</b> руб.".replace(",", " "))

    await call.message.edit_text("\n".join(lines), parse_mode="HTML")
    await call.answer()


# ─── /history ─────────────────────────────────────────────────────────────────

@dp.message(Command("history"))
async def cmd_history(message: Message):
    rows = await db.get_history(message.from_user.id)
    if not rows:
        await message.answer("Расходов пока нет.")
        return

    lines = ["📋 <b>Последние расходы:</b>\n"]
    for desc, amount, category, created_at in rows:
        lines.append(f"• {desc} — {amount:,.0f} руб. {category} <i>{created_at}</i>".replace(",", " "))

    await message.answer("\n".join(lines), parse_mode="HTML")


# ─── /undo ────────────────────────────────────────────────────────────────────

@dp.message(Command("undo"))
async def cmd_undo(message: Message):
    deleted = await db.delete_last_expense(message.from_user.id)
    if deleted:
        await message.answer("✅ Последний расход удалён.")
    else:
        await message.answer("Нет расходов для удаления.")


# ─── /categories ──────────────────────────────────────────────────────────────

@dp.message(Command("categories"))
async def cmd_categories(message: Message):
    user_id = message.from_user.id
    await db.ensure_default_categories(user_id)
    categories = await db.get_categories(user_id)
    await message.answer(
        "🏷 <b>Категории:</b>\nНажми 🗑 чтобы удалить.",
        reply_markup=manage_categories_keyboard(categories),
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("delcat:"))
async def delete_category(call: CallbackQuery):
    cat_id = int(call.data.split(":")[1])
    await db.delete_category(cat_id, call.from_user.id)
    categories = await db.get_categories(call.from_user.id)
    await call.message.edit_text(
        "🏷 <b>Категории:</b>\nНажми 🗑 чтобы удалить.",
        reply_markup=manage_categories_keyboard(categories),
        parse_mode="HTML",
    )
    await call.answer("Удалено")


@dp.callback_query(F.data == "addcat")
async def start_add_category(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.set_state(AddCategory.waiting_emoji)
    await call.message.answer("Введи эмодзи для новой категории (один символ):")
    await call.answer()


async def process_emoji(message: Message, state: FSMContext):
    emoji = message.text.strip()
    await state.update_data(emoji=emoji)
    await state.set_state(AddCategory.waiting_name)
    await message.answer("Теперь введи название категории:")


async def process_name(message: Message, state: FSMContext):
    data = await state.get_data()
    emoji = data.get("emoji", "📌")
    name = message.text.strip()
    await db.add_category(message.from_user.id, emoji, name)
    await state.clear()
    await message.answer(f"✅ Категория «{emoji} {name}» добавлена!")


# ─── main ─────────────────────────────────────────────────────────────────────

async def main():
    await db.init_db()
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
