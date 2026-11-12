from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import get_db, User, Chat, Message, Reaction
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_CHAT_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав администратора.")
        return
    
    await update.message.reply_text(
        "👋 Привет, администратор!\n\n"
        "Доступные команды:\n"
        "/stats — статистика по чатам\n"
        "/export <дата_начала> <дата_конца> — выгрузить переписку\n"
        "  Пример: /export 2024-01-01 2024-01-31\n"
        "/help — справка"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав администратора.")
        return
    
    await update.message.reply_text(
        "📖 Справка по командам:\n\n"
        "/start — приветствие\n"
        "/stats — показать статистику по чатам\n"
        "/export <дата_начала> <дата_конца> — выгрузить переписку за период\n"
        "  Формат даты: ГГГГ-ММ-ДД\n"
        "  Пример: /export 2024-01-01 2024-01-31\n"
        "/help — эта справка"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав администратора.")
        return
    
    db: Session = next(get_db())
    
    try:
        chats_count = db.query(Chat).count()
        messages_count = db.query(Message).count()
        users_count = db.query(User).count()
        reactions_count = db.query(Reaction).count()
        
        text = (
            f"📊 Статистика:\n\n"
            f"👥 Пользователей: {users_count}\n"
            f"💬 Чатов: {chats_count}\n"
            f"📝 Сообщений: {messages_count}\n"
            f"❤️ Реакций: {reactions_count}"
        )
        
        await update.message.reply_text(text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    finally:
        db.close()


async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав администратора.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Укажите даты в формате: /export ГГГГ-ММ-ДД ГГГГ-ММ-ДД\n"
            "Пример: /export 2024-01-01 2024-01-31"
        )
        return
    
    try:
        start_date = datetime.strptime(context.args[0], "%Y-%m-%d")
        end_date = datetime.strptime(context.args[1], "%Y-%m-%d") + timedelta(days=1)
        
        await update.message.reply_text(f"⏳ Выгружаю данные с {context.args[0]} по {context.args[1]}...")
        
        db: Session = next(get_db())
        
        try:
            messages = db.query(Message).filter(
                and_(
                    Message.created_at >= start_date,
                    Message.created_at < end_date
                )
            ).all()
            
            if not messages:
                await update.message.reply_text("📭 Сообщений за этот период не найдено.")
                return
            
            report = f"📋 Отчёт с {context.args[0]} по {context.args[1]}:\n\n"
            report += f"Найдено сообщений: {len(messages)}\n\n"
            
            chats_data = {}
            for msg in messages:
                chat = db.query(Chat).filter(Chat.telegram_id == msg.chat_id).first()
                user = db.query(User).filter(User.telegram_id == msg.user_id).first()
                
                chat_title = chat.title if chat else "Личный чат"
                username = user.username if user else "Неизвестно"
                
                if chat_title not in chats_data:
                    chats_data[chat_title] = []
                
                chats_data[chat_title].append(
                    f"  [{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {username}: {msg.text or '(файл/фото)'}"
                )
            
            for chat_title, msgs in chats_data.items():
                report += f"💬 {chat_title}:\n"
                for msg in msgs[:10]:
                    report += msg + "\n"
                if len(msgs) > 10:
                    report += f"  ... и ещё {len(msgs) - 10} сообщений\n"
                report += "\n"
            
            max_length = 4000
            for i in range(0, len(report), max_length):
                await update.message.reply_text(report[i:i + max_length])
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при выгрузке: {e}")
        finally:
            db.close()
            
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД\n"
            "Пример: /export 2024-01-01 2024-01-31"
        )


def run_admin_bot():
    print("Запуск бота-администратора...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("export", export_data))
    
    application.run_polling()


if __name__ == "__main__":
    run_admin_bot()