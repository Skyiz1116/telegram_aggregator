from telegram import Update
from telegram.ext import Application, MessageHandler, MessageReactionHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from database import get_db, User, Chat, Message, Reaction
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
    
    chat = message.chat
    user = message.from_user
    
    if not user:
        return
    
    db: Session = next(get_db())
    
    try:
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        if not db_user:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db.add(db_user)
            db.commit()
        
        db_chat = db.query(Chat).filter(Chat.telegram_id == chat.id).first()
        if not db_chat:
            db_chat = Chat(
                telegram_id=chat.id,
                title=chat.title,
                chat_type=chat.type
            )
            db.add(db_chat)
            db.commit()
        
        file_path = None
        if message.document:
            file_path = message.document.file_id
        elif message.photo:
            file_path = message.photo[-1].file_id
        
        db_message = Message(
            telegram_id=message.message_id,
            chat_id=chat.id,
            user_id=user.id,
            text=message.text or message.caption,
            file_path=file_path
        )
        db.add(db_message)
        db.commit()
        
        print(f"Сохранено сообщение от {user.username} в чате {chat.title}")
        
    except Exception as e:
        print(f"Ошибка при сохранении: {e}")
        db.rollback()
    finally:
        db.close()


async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reaction = update.message_reaction
    if not reaction:
        return
    
    user = reaction.user
    if not user:
        return
    
    if not reaction.new_reaction:
        return
    
    db: Session = next(get_db())
    
    try:
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        
        if not db_user:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db.add(db_user)
            db.commit()
        
        emoji = reaction.new_reaction[0].emoji if reaction.new_reaction else "unknown"
        
        db_reaction = Reaction(
            message_id=reaction.message_id,
            user_id=user.id,
            emoji=emoji
        )
        db.add(db_reaction)
        db.commit()
        
        print(f"Сохранена реакция от {user.username}: {emoji}")
        
    except Exception as e:
        print(f"Ошибка при сохранении реакции: {e}")
        db.rollback()
    finally:
        db.close()


def run_collector():
    print("Запуск бота-сборщика...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, handle_message)
    )
    
    application.add_handler(
        MessageReactionHandler(handle_reaction)
    )
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_collector()