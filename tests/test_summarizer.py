"""
Unit-тесты для Summarizer Agent
"""

import pytest
from datetime import datetime, timezone
from ai_core.agents.summarizer import summarize
from ai_core.common.models import DomainMessage


def test_summarize_with_messages():
    """Тест: агент возвращает непустую строку для списка сообщений"""
    messages = [
        DomainMessage(
            source="test",
            author_id="user1",
            author_name="Alice",
            content="Привет! Как дела?",
            timestamp=datetime.now(timezone.utc)
        ),
        DomainMessage(
            source="test",
            author_id="user2",
            author_name="Bob",
            content="Отлично! Работаю над новым проектом.",
            timestamp=datetime.now(timezone.utc)
        ),
        DomainMessage(
            source="test",
            author_id="user1",
            author_name="Alice",
            content="Круто! Расскажи подробнее.",
            timestamp=datetime.now(timezone.utc)
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
        DomainMessage(
            source="test",
            author_id="user1",
            author_name="John",
            content="Hello! How are you?",
            timestamp=datetime.now(timezone.utc)
        ),
        DomainMessage(
            source="test",
            author_id="user2",
            author_name="Юрий",
            content="Привет! Все отлично, спасибо!",
            timestamp=datetime.now(timezone.utc)
        ),
        DomainMessage(
            source="test",
            author_id="user3",
            author_name="Олександр",
            content="Привіт усім! Що нового?",
            timestamp=datetime.now(timezone.utc)
        )
    ]
    
    summary = summarize(messages)
    
    assert summary is not None
    assert len(summary) > 0
    
    print(f"\nМногоязычное саммари:\n{summary}")
