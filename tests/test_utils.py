import pytest
from unittest.mock import MagicMock
from telegram import Message, User, Chat
from telegram_bot.utils import extract_author_from_message

# Mock classes for MessageOrigin (since we might not have them importable or want to mock them)
class MockMessageOriginUser:
    def __init__(self, sender_user):
        self.type = "user"
        self.sender_user = sender_user

class MockMessageOriginHiddenUser:
    def __init__(self, sender_user_name):
        self.type = "hidden_user"
        self.sender_user_name = sender_user_name

class MockMessageOriginChat:
    def __init__(self, sender_chat):
        self.type = "chat"
        self.sender_chat = sender_chat

class MockMessageOriginChannel:
    def __init__(self, chat):
        self.type = "channel"
        self.chat = chat

@pytest.fixture
def mock_message():
    message = MagicMock(spec=Message)
    message.from_user = User(id=999, first_name="Current", is_bot=False, username="current_user")
    message.forward_origin = None
    message.forward_from = None
    message.forward_sender_name = None
    message.forward_from_chat = None
    return message

def test_extract_author_normal_message(mock_message):
    author_id, author_nick, author_name = extract_author_from_message(mock_message)
    assert author_id == "999"
    assert author_nick == "current_user"
    assert author_name == "Current"

def test_extract_author_forward_origin_user(mock_message):
    origin_user = User(id=123, first_name="Andrew", is_bot=False, username="andrew_user")
    mock_message.forward_origin = MockMessageOriginUser(sender_user=origin_user)
    
    author_id, author_nick, author_name = extract_author_from_message(mock_message)
    assert author_id == "123"
    assert author_nick == "andrew_user"
    assert author_name == "Andrew"

def test_extract_author_forward_origin_hidden_user(mock_message):
    # This simulates the case where privacy settings hide the user ID
    mock_message.forward_origin = MockMessageOriginHiddenUser(sender_user_name="Andrew Hidden")
    
    author_id, author_nick, author_name = extract_author_from_message(mock_message)
    # Expectation: ID and Nick are None, Name is "Andrew Hidden"
    assert author_id is None
    assert author_nick is None
    assert author_name == "Andrew Hidden"

def test_extract_author_forward_origin_channel(mock_message):
    channel = Chat(id=555, type="channel", title="News Channel", username="news_channel")
    mock_message.forward_origin = MockMessageOriginChannel(chat=channel)
    
    author_id, author_nick, author_name = extract_author_from_message(mock_message)
    assert author_id == "555"
    assert author_nick == "news_channel"
    assert author_name == "News Channel"
