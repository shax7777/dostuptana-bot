import asyncio
import time
import db
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

nest_asyncio.apply()
TOKEN = "7589335658:AAH-C9DwVUFNJKzTHa7kb2J5szXcRcIc4JI"
DAYS = 30
SECONDS = DAYS * 86400

db.init_db()

async def remove_user_after(chat_id, user_id, application, delay):
    await asyncio.sleep(delay)
    if not db.get_user(user_id):
        return
    try:
        await application.bot.ban_chat_member(chat_id, user_id)
        await application.bot.unban_chat_member(chat_id, user_id)
        await application.bot.send_message(chat_id, f"⏳ Пользователь {user_id} удалён после 30 дней.")
        db.delete_user(user_id)
    except Exception as e:
        print(f"Ошибка удаления: {e}")

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        chat_id = update.effective_chat.id
        user_id = user.id
        now = int(time.time())
        db.add_user(user_id, chat_id, now)
        await context.bot.send_message(chat_id, f"{user.first_name}, у тебя доступ на 30 дней.")
        asyncio.create_task(remove_user_after(chat_id, user_id, context.application, SECONDS))

async def schedule_existing_users(application):
    now = int(time.time())
    users = db.get_all_users()
    for user_id, chat_id, join_time in users:
        passed = now - join_time
        if passed >= SECONDS:
            await application.bot.ban_chat_member(chat_id, user_id)
            await application.bot.unban_chat_member(chat_id, user_id)
            await application.bot.send_message(chat_id, f"⏳ Пользователь {user_id} удалён после 30 дней.")
            db.delete_user(user_id)
        else:
            remaining = SECONDS - passed
            asyncio.create_task(remove_user_after(chat_id, user_id, application, remaining))

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    await schedule_existing_users(app)
    print("✅ Бот работает. Ожидает участников...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())