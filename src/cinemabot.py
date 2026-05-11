import asyncio
import aiohttp
import logging
import sys

from os import getenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.sql import func

from database import create_tables, async_session, MessageHistory, FilmStats
from web import find_film_info, Film, ZonaScraper, RutubeScraper


TOKEN = getenv("BOT_TOKEN")
dp = Dispatcher()


def format_film_response(film: Film, zona_url: str, rutube_url: str) -> str:
    return f"""
        🎬 <b>{film.name} ({film.year})</b>

        ⭐ Рейтинг: <b>{film.rating}</b>

        📌 <b>Ссылки для просмотра:</b>

        • <a href="{film.url}">🎥 Основная ссылка (Кинопоиск)</a>
        • <a href="{zona_url}">🌐 Zona</a>
        • <a href="{rutube_url}">📺 Rutube</a>

        ✨ <i>Приятного просмотра!</i>
    """.strip()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    assert message.from_user is not None
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message(Command("history"))
async def get_history(message: Message) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(MessageHistory).where(
                MessageHistory.chat_id == message.chat.id
            ).order_by(
                MessageHistory.created_at.asc()
            )
        )

        history = result.scalars().all()

        if not history:
            await message.answer("История чата пуста")

        text = "<b>🕘 История запросов:</b>\n\n"

        for i, msg in enumerate(history, start=1):
            text += (
                f"<b>{i}.</b> "
                f"{msg.text}\n"
                f"<i>{msg.created_at:%d.%m.%Y %H:%M}</i>\n"
            )

        await message.answer(text)


@dp.message(Command("stats"))
async def get_stats(message: Message) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(
                FilmStats.text,
                func.count(FilmStats.id).label("count")
            ).where(
                FilmStats.chat_id == message.chat.id
            ).group_by(
                FilmStats.text
            ).order_by(
                func.count(FilmStats.id).desc()
            )
        )

        stats = result.all()

        if not stats:
            await message.answer("Статистика пока пуста.")
            return

        response = "Статистика предложенных фильмов:\n\n"
        for text, count in stats:
            response += f"• {text}: {count} \n"

        await message.answer(response)


@dp.message(Command("help"))
async def help_command(message: Message) -> None:
    help_text = """
    🎬 <b>CinemaBot - Помощь по командам</b>

    <b>Основные команды:</b>
    /start - Приветствие и начало работы
    /help - Данная справка
    /stats - Статистика предложенных фильмов
    /history - История запросов

    <b>Работа с фильмами:</b>
    Отправьте название фильма, чтобы получить информацию о нем

    Поддержка: @art_smirnofff
    """
    await message.answer(help_text)


@dp.message()
async def echo_handler(message: Message) -> None:
    found = False

    async with aiohttp.ClientSession() as session:
        film_info = await find_film_info(session, message.text)
        zs = ZonaScraper()
        rs = RutubeScraper()
        zona_url = await zs.search_film(session, message.text)
        rutube_url = await rs.search_film(session, message.text)
        if film_info:
            found = True
            await message.answer(format_film_response(film_info, zona_url, rutube_url))
        else:
            await message.answer("По Вашему запросу ничего не найдено.")

    async with async_session() as session:
        db_message = MessageHistory(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=message.text
        )
        session.add(db_message)
        if found:
            db_film_stats = FilmStats(
                chat_id=message.chat.id,
                text=film_info.name
            )
            session.add(db_film_stats)

        await session.commit()


async def main() -> None:
    await create_tables()
    assert TOKEN is not None, "Token cannot be None"
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
