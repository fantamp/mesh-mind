"""
Unit-тесты для Summarizer Agent
"""

import pytest
from datetime import datetime, timezone
from ai_core.agents.summarizer import summarize
from ai_core.storage.db import Message


def test_summarize_with_messages():
    """Тест: агент возвращает непустую строку для списка сообщений"""
    messages = [
        Message(
            source="test",
            chat_id="test_chat",
            author_name="Alice",
            content="Привет! Как дела?",
            created_at=datetime.now(timezone.utc)
        ),
        Message(
            source="test",
            chat_id="test_chat",
            author_name="Bob",
            content="Отлично! Работаю над новым проектом.",
            created_at=datetime.now(timezone.utc)
        ),
        Message(
            source="test",
            chat_id="test_chat",
            author_name="Alice",
            content="Круто! Расскажи подробнее.",
            created_at=datetime.now(timezone.utc)
        )
    ]
    
    summary = summarize(messages)
    
    # Проверяем, что саммари не пустое
    assert summary is not None
    assert len(summary) > 0
    assert isinstance(summary, str)
    
    print(f"\nСаммари (для визуальной проверки):\n{summary}")


def test_summarize_empty_list():
    """Тест: агент выбрасывает исключение для пустого списка"""
    with pytest.raises(ValueError, match="Список сообщений не может быть пустым"):
        summarize([])


def test_summarize_multilingual():
    """Тест: агент работает с многоязычными сообщениями"""
    messages = [
        Message(
            source="test",
            chat_id="test_chat",
            author_name="John",
            content="Hello! How are you?",
            created_at=datetime.now(timezone.utc)
        ),
        Message(
            source="test",
            chat_id="test_chat",
            author_name="Юрий",
            content="Привет! Все отлично, спасибо!",
            created_at=datetime.now(timezone.utc)
        ),
        Message(
            source="test",
            chat_id="test_chat",
            author_name="Олександр",
            content="Привіт усім! Що нового?",
            created_at=datetime.now(timezone.utc)
        )
    ]
    
    summary = summarize(messages)
    
    assert summary is not None
    assert len(summary) > 0
    
    print(f"\nМногоязычное саммари:\n{summary}")
