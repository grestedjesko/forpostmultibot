from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import DateTime, ForeignKey
from datetime import datetime
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import sessionmaker, Session
import uuid
import hashlib
import base64
import requests
from dotenv import load_dotenv
from fastapi import Request
import os

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_LINK")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # добавьте это
    pool_recycle=3600,   # пересоздавать соединения раз в час (рекомендуется)
    connect_args={"init_command": "SET time_zone = '+03:00'"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()


class ShortenedURL(Base):
    __tablename__ = "shortened_url"
    id = Column(Integer, primary_key=True)
    post_id = Column(String(50), nullable=False)
    bot_id = Column(String(50), nullable=False)
    original_url = Column(String(2048), nullable=False)
    short_hash = Column(String(16), unique=True, nullable=False)
    visits = Column(Integer, default=0)


class BotInfo(Base):
    __tablename__ = "bot_info"
    id = Column(Integer, primary_key=True)
    bot_id = Column(String(50), unique=True, nullable=False)
    chat_id = Column(String(50), nullable=False)

class VisitLog(Base):
    __tablename__ = "visit_log"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))  # IPv6-compatible
    post_id = Column(String(50), nullable=False)
    short_hash = Column(String(16), ForeignKey("shortened_url.short_hash"), nullable=False)


class ShortenRequest(BaseModel):
    post_id: str
    bot_id: str
    urls: List[str]


Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_unique_hash(post_id: str, bot_id: str, db: Session):
    while True:
        raw_data = f"{uuid.uuid4().hex}{post_id}{bot_id}"
        short_hash = base64.urlsafe_b64encode(hashlib.sha256(raw_data.encode()).digest())[:10].decode()
        if not db.query(ShortenedURL).filter_by(short_hash=short_hash).first():
            return short_hash


def send_telegram_message(chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(e)



@app.get("/stats")
def get_post_stats(post_id: int = None, short_link: str = None, db: Session = Depends(get_db)):
    print('123')
    if not post_id and not short_link:
        raise HTTPException(status_code=400, detail="Either post_id or short_link must be provided")

    query = db.query(ShortenedURL)

    if post_id:
        query = query.filter(ShortenedURL.post_id == post_id)
    elif short_link:
        short_hash = short_link.split("/")[-1]  # Получаем hash из короткой ссылки
        query = query.filter(ShortenedURL.short_hash == short_hash)

    urls = query.all()
    if not urls:
        raise HTTPException(status_code=404, detail="No data found")

    result = [
        {
            "post_id": url.post_id,
            "short_link": f"http://s.forpost.me/{url.short_hash}",
            "original_url": url.original_url,
            "visits": url.visits
        }
        for url in urls
    ]

    return result


@app.post("/shorten")
def shorten_url(request: ShortenRequest, db: Session = Depends(get_db)):
    post_id = request.post_id
    bot_id = request.bot_id
    urls = request.urls

    if not post_id or not bot_id:
        raise HTTPException(status_code=400, detail="post_id and bot_id are required")

    result = []
    for url in urls:
        existing_entry = db.query(ShortenedURL).filter_by(post_id=post_id, bot_id=bot_id, original_url=url).first()
        if existing_entry:
            short_hash = existing_entry.short_hash
        else:
            while True:
                try:
                    short_hash = generate_unique_hash(post_id, bot_id, db)
                    new_url = ShortenedURL(original_url=url, short_hash=short_hash, post_id=post_id, bot_id=bot_id)
                    db.add(new_url)
                    db.commit()
                    break
                except:
                    db.rollback()

        result.append({"original": url, "short": f"http://s.forpost.me/{short_hash}"})

    return result

@app.get("/{short_hash}")
def redirect_to_original(short_hash: str, request: Request, db: Session = Depends(get_db)):
    entry = db.query(ShortenedURL).filter_by(short_hash=short_hash).first()
    if entry:
        # Получаем IP-адрес
        client_ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()


        # Логируем переход
        log = VisitLog(
            ip_address=client_ip,
            post_id=entry.post_id,
            short_hash=short_hash
        )
        db.add(log)
        db.commit()

        bot_info = db.query(BotInfo).filter_by(bot_id=entry.bot_id).first()
        if bot_info:
            message = f"Переход по посту {entry.post_id}"
            send_telegram_message(bot_info.chat_id, message)

        return RedirectResponse(url=entry.original_url)

    raise HTTPException(status_code=404, detail="URL not found")


