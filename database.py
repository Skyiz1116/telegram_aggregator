from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    messages = relationship("Message", back_populates="user")
    reactions = relationship("Reaction", back_populates="user")


class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    title = Column(String, nullable=True)
    chat_type = Column(String)
    
    messages = relationship("Message", back_populates="chat")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    chat_id = Column(BigInteger, ForeignKey("chats.telegram_id"))
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    text = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", back_populates="messages")
    reactions = relationship("Reaction", back_populates="message")


class Reaction(Base):
    __tablename__ = "reactions"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(BigInteger, ForeignKey("messages.telegram_id"))
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    emoji = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    message = relationship("Message", back_populates="reactions")
    user = relationship("User", back_populates="reactions")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()