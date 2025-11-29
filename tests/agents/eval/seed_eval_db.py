"""Подготовка данных для eval всех агентов.

Запуск:
    PYTHONPATH=$(pwd) python tests/agents/eval/seed_eval_db.py

Что делает:
- очищает и наполняет SQLite сообщениями для разных chat_id
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlmodel import delete

from ai_core.storage.db import Message, init_db, async_session


# Chat IDs, используемые в eval-наборах
CHAT_IDS = [
    "eval_main_chat",       # основной чат с сообщениями
    "eval_empty_chat",      # пустой чат для проверки edge cases
]


async def seed_sqlite() -> None:
    await init_db()

    async with async_session() as session:
        # Очистка
        await session.execute(delete(Message).where(Message.chat_id.in_(CHAT_IDS)))

        now = datetime.now(timezone.utc)

        # Общий набор сообщений для активных чатов
        # Format: (author_id, author_nick, content, time_offset)
        base_messages = [
            ("user1", "irina", "Планируем релиз на пятницу", timedelta(days=2, hours=3)),
            ("user2", "pavel", "Вчера обсуждали бюджет и сроки", timedelta(days=1, hours=5)),
            ("user3", "maria", "Ссылка на макеты: https://figma.com/file/demo", timedelta(days=1, hours=2)),
            ("user4", "oleg", "Сегодня апдейт по бэкенду, всё по плану", timedelta(hours=1)),
            ("user1", "irina", "Нужно проверить метрики", timedelta(minutes=30)),
            ("user2", "pavel", "Согласен, давайте созвонимся", timedelta(minutes=15)),
        ]

        messages = []
        # Наполняем только основной чат
        for author_id, author_nick, content, offset in base_messages:
            messages.append(
                Message(
                    chat_id="eval_main_chat",
                    source="telegram",
                    author_id=author_id,
                    author_nick=author_nick,
                    content=content,
                    created_at=now - offset,
                )
            )

        session.add_all(messages)
        await session.commit()

    print(f"✅ SQLite seeded: chat_ids={CHAT_IDS}")


async def main() -> None:
    await seed_sqlite()


if __name__ == "__main__":
    asyncio.run(main())
