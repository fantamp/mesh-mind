"""
Ручной тест для проверки качества саммари Summarizer Agent

Запуск: python tests/manual/test_summarizer.py
"""

import sys
import os

# Добавляем корень проекта в sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(project_root)

from datetime import datetime, timezone, timedelta
from ai_core.agents.summarizer import summarize
from ai_core.common.models import Message


def create_test_messages():
    """Создает 10 тестовых сообщений на разных языках"""
    base_time = datetime.now(timezone.utc)
    
    messages = [
        Message(
            source="telegram",
            author_id="user1",
            author_name="Сергій",
            content="Привіт всім! Сьогодні хочу обговорити наш новий проект.",
            timestamp=base_time
        ),
        Message(
            source="telegram",
            author_id="user2",
            author_name="Алексей",
            content="Привет! Да, давай обсудим. Какие основные задачи?",
            timestamp=base_time + timedelta(minutes=1)
        ),
        Message(
            source="telegram",
            author_id="user3",
            author_name="Kate",
            content="Hi everyone! I think we should focus on the AI summarization feature first.",
            timestamp=base_time + timedelta(minutes=2)
        ),
        Message(
            source="telegram",
            author_id="user1",
            author_name="Сергій",
            content="Так, згоден. Це пріоритет номер один. Нам потрібно використовувати Gemini API.",
            timestamp=base_time + timedelta(minutes=3)
        ),
        Message(
            source="telegram",
            author_id="user2",
            author_name="Алексей",
            content="Отлично! Я могу взять на себя интеграцию с API. Какие еще задачи?",
            timestamp=base_time + timedelta(minutes=5)
        ),
        Message(
            source="telegram",
            author_id="user3",
            author_name="Kate",
            content="We also need to handle errors and implement retry logic. That's critical.",
            timestamp=base_time + timedelta(minutes=7)
        ),
        Message(
            source="telegram",
            author_id="user1",
            author_name="Сергій",
            content="Добре, давайте розділимо завдання: API інтеграція - Олексій, retry логіка - Kate, тести - я.",
            timestamp=base_time + timedelta(minutes=10)
        ),
        Message(
            source="telegram",
            author_id="user2",
            author_name="Алексей",
            content="Договорились! Когда дедлайн?",
            timestamp=base_time + timedelta(minutes=12)
        ),
        Message(
            source="telegram",
            author_id="user3",
            author_name="Kate",
            content="I suggest we complete this by Friday. That gives us 3 days.",
            timestamp=base_time + timedelta(minutes=13)
        ),
        Message(
            source="telegram",
            author_id="user1",
            author_name="Сергій",
            content="Чудово! П'ятниця - це дедлайн. Всім успіхів!",
            timestamp=base_time + timedelta(minutes=15)
        )
    ]
    
    return messages


def main():
    print("=" * 80)
    print("РУЧНОЙ ТЕСТ: Summarizer Agent")
    print("=" * 80)
    
    print("\n1. Создаю 10 тестовых сообщений...")
    messages = create_test_messages()
    print(f"   Создано {len(messages)} сообщений\n")
    
    print("2. Вывожу исходные сообщения:")
    print("-" * 80)
    for i, msg in enumerate(messages, 1):
        print(f"   [{i}] [{msg.timestamp.strftime('%H:%M')}] {msg.author_name}: {msg.content}")
    print("-" * 80)
    
    print("\n3. Генерирую саммари через Summarizer Agent...")
    try:
        summary = summarize(messages)
        
        print("\n4. РЕЗУЛЬТАТ - Саммари:")
        print("=" * 80)
        print(summary)
        print("=" * 80)
        
        print("\n✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print(f"\nСтатистика:")
        print(f"  - Количество сообщений: {len(messages)}")
        print(f"  - Длина саммари: {len(summary)} символов")
        print(f"  - Язык сообщений: украинский, русский, английский")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
