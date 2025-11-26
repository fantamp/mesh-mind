"""Подготовка данных для eval всех агентов.

Запуск:
    PYTHONPATH=$(pwd) python tests/agents/eval/seed_eval_db.py

Что делает:
- очищает и наполняет SQLite сообщениями для разных chat_id
- очищает и наполняет векторное хранилище (Chroma) документами для QA кейсов
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlmodel import delete

from ai_core.storage.db import Message, init_db, async_session
from ai_core.rag.vector_db import VectorDB


# Chat IDs, используемые в eval-наборах
CHAT_IDS = [
    "eval_chat_observer",   # chat_observer
    "empty_chat_observer",  # пустой чат для observer
    "eval_chat_summarizer", # chat_summarizer
    "eval_orchestrator",    # orchestrator (history)
]

QA_CHAT_ID = "eval_qa_chat"


async def seed_sqlite() -> None:
    await init_db()

    async with async_session() as session:
        # Очистка
        await session.execute(delete(Message).where(Message.chat_id.in_(CHAT_IDS + [QA_CHAT_ID, "empty_chat"])))

        now = datetime.now(timezone.utc)

        # Общий набор сообщений для активных чатов
        base_messages = [
            ("Ирина", "Планируем релиз на пятницу", now - timedelta(days=2, hours=3)),
            ("Павел", "Вчера обсуждали бюджет и сроки", now - timedelta(days=1, hours=5)),
            ("Мария", "Ссылка на макеты: https://figma.com/file/demo", now - timedelta(days=1, hours=2)),
            ("Олег", "Сегодня апдейт по бэкенду, всё по плану", now - timedelta(hours=1)),
        ]

        messages = []
        for chat_id in ["eval_chat_observer", "eval_chat_summarizer", "eval_orchestrator"]:
            for author, content, ts in base_messages:
                messages.append(
                    Message(
                        chat_id=chat_id,
                        source="telegram",
                        author_name=author,
                        content=content,
                        created_at=ts,
                    )
                )

        # Пустой чат
        messages.extend(
            [
                # ничего не добавляем, просто оставляем empty_chat_observer пустым
            ]
        )

        session.add_all(messages)
        await session.commit()

    print(f"✅ SQLite seeded: chat_ids={CHAT_IDS}, empty_chat_observer оставлен пустым")


def seed_vector() -> None:
    vdb = VectorDB()
    # Очистить предыдущие документы для QA чата
    try:
        vdb.delete(where={"chat_id": QA_CHAT_ID})
    except Exception:
        pass

    docs = [
        "Проект Apollo: бюджет 50000 USD, дедлайн 1 декабря 2025, ответственный — Ольга.",
        "Отчёт по инфраструктуре: миграция БД завершена, рисков не выявлено.",
    ]
    metas = [
        {"source": "kb", "filename": "apollo.txt"},
        {"source": "kb", "filename": "infra.txt"},
    ]
    vdb.add_texts(docs, metadatas=metas, chat_id=QA_CHAT_ID)
    print(f"✅ Vector store seeded: chat_id={QA_CHAT_ID}, {len(docs)} docs")


async def main() -> None:
    await seed_sqlite()
    seed_vector()


if __name__ == "__main__":
    asyncio.run(main())
