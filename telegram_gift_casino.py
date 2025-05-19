import sqlite3
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes
from telegram.ext.filters import StatusUpdate


# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('gifts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        market_price INTEGER
    )''')
    conn.commit()
    conn.close()


# Получить инвентарь
def get_inventory(user_id):
    conn = sqlite3.connect('gifts.db')
    c = conn.cursor()
    c.execute("SELECT name, market_price FROM gifts WHERE user_id = ?", (user_id,))
    gifts = c.fetchall()
    conn.close()
    return gifts


# Старт бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Открыть Mini App", web_app={'url': 'https://unique-cobbler-59f2c8.netlify.app/'})],
        [InlineKeyboardButton("Инвентарь", callback_data='inventory')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать в GiftCrash! 🎁 Открой Mini App для игры:",
                                    reply_markup=reply_markup)


# Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'inventory':
        gifts = get_inventory(user_id)
        if gifts:
            inventory_text = "Твой инвентарь:\n" + "\n".join([f"{name}: {price} Stars" for name, price in gifts])
        else:
            inventory_text = "Инвентарь пуст. Сделай депозит в Mini App!"
        await query.message.reply_text(inventory_text)


# Обработка данных от Mini App
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = json.loads(update.message.web_app_data.data)
    conn = sqlite3.connect('gifts.db')
    c = conn.cursor()

    if data['action'] == 'deposit':
        c.execute("INSERT INTO gifts (user_id, name, market_price) VALUES (?, ?, ?)",
                  (user_id, data['name'], data['price']))
        await update.message.reply_text(f"Подарок '{data['name']}' ({data['price']} Stars) добавлен!")
    elif data['action'] == 'bet':
        c.execute("DELETE FROM gifts WHERE user_id = ? AND name = ? LIMIT 1",
                  (user_id, data['name']))
        await update.message.reply_text(f"Ставка: {data['name']} ({data['price']} Stars)")
    elif data['action'] == 'cashout':
        c.execute("INSERT INTO gifts (user_id, name, market_price) VALUES (?, ?, ?)",
                  (user_id, f"Win_{data['value']}", data['value']))
        await update.message.reply_text(f"Кэшаут! Выигрыш: ${data['value']} Stars")
    elif data['action'] == 'withdraw':
        total_value = sum(p for _, p in get_inventory(user_id))
        if total_value >= data['price']:
            c.execute("DELETE FROM gifts WHERE user_id = ? LIMIT 1", (user_id,))
            await update.message.reply_text(f"Подарок '{data['name']}' ({data['price']} Stars) отправлен!")
        else:
            await update.message.reply_text("Недостаточно баланса!")

    conn.commit()
    conn.close()


# Главная функция
def main():
    init_db()
    app = Application.builder().token("8145247003:AAGajFOZxNGnmBfR3HPLQNS3mk1AbP2DhiI").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern='^inventory$'))
    app.add_handler(MessageHandler(StatusUpdate.WEB_APP_DATA, web_app_data))

    app.run_polling()


if __name__ == '__main__':
    main()