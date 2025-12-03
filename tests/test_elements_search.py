
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
import json
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from ai_core.tools.elements import _fetch_elements_impl, _parse_time_range

class MockElement:
    def __init__(self, id, type, content, created_by, created_at, attributes=None, frames=None, canvas_id=None):
        self.id = id
        self.type = type
        self.content = content
        self.created_by = created_by
        self.created_at = created_at
        self.attributes = attributes or {}
        self.frames = frames or []
        self.canvas_id = canvas_id or "canvas1"

class TestFetchElementsSearch(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        # Common setup for time-based tests
        self.now = datetime.now(timezone.utc)
        self.today_start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.yesterday_start = self.today_start - timedelta(days=1)
        
        # Create a diverse set of elements
        self.elements = [
            MockElement(
                id="1", 
                type="message", 
                content="Hello world", 
                created_by="telegram:user:123", 
                created_at=self.now, 
                attributes={"author_name": "Alice", "source": "telegram"}
            ),
            MockElement(
                id="2", 
                type="message", 
                content="Important update", 
                created_by="telegram:user:456", 
                created_at=self.now - timedelta(minutes=30), 
                attributes={"author_nick": "Bob", "source": "telegram"}
            ),
            MockElement(
                id="3", 
                type="note", 
                content="Meeting notes about project X", 
                created_by="user:admin", 
                created_at=self.yesterday_start + timedelta(hours=12), # Yesterday noon
                attributes={}
            ),
            MockElement(
                id="4", 
                type="message", 
                content="Reply to Alice", 
                created_by="telegram:user:789", 
                created_at=self.now - timedelta(hours=2), 
                attributes={"author_name": "Charlie"}
            ),
            MockElement(
                id="5", 
                type="file", 
                content="report.pdf", 
                created_by="telegram:user:123", 
                created_at=self.yesterday_start - timedelta(hours=1), # Day before yesterday (late)
                attributes={"filename": "report.pdf"}
            ),
        ]

    def test_parse_time_range(self):
        # Test "yesterday"
        start, end = _parse_time_range("yesterday")
        self.assertEqual(start, self.yesterday_start)
        self.assertEqual(end, self.today_start)
        
        # Test "today"
        start, end = _parse_time_range("today")
        self.assertEqual(start, self.today_start)
        self.assertIsNone(end)
        
        # Test relative "X hours ago"
        start, end = _parse_time_range("2 hours ago")
        self.assertIsNone(end)
        diff = self.now - timedelta(hours=2) - start
        self.assertTrue(abs(diff.total_seconds()) < 5)

        # Test explicit range
        range_str = "2023-01-01T10:00 to 2023-01-01T12:00"
        start, end = _parse_time_range(range_str)
        self.assertEqual(start.year, 2023)
        self.assertEqual(start.hour, 10)
        self.assertEqual(end.hour, 12)

    async def test_search_created_by(self):
        with patch('ai_core.services.canvas_service.canvas_service') as mock_service:
            mock_service.get_or_create_canvas_for_chat = AsyncMock(return_value=MagicMock(id="canvas1"))
            mock_service.get_elements = AsyncMock(return_value=self.elements)
            
            # Search for "user:123" (Alice and file)
            res_json = await _fetch_elements_impl(chat_id=1, created_by="user:123")
            res = json.loads(res_json)
            self.assertEqual(len(res), 2)
            ids = sorted([r['id'] for r in res])
            self.assertEqual(ids, ["1", "5"])
            
            # Case insensitive "ADMIN"
            res_json = await _fetch_elements_impl(chat_id=1, created_by="ADMIN")
            res = json.loads(res_json)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]['id'], "3")

    async def test_search_author(self):
        with patch('ai_core.services.canvas_service.canvas_service') as mock_service:
            mock_service.get_or_create_canvas_for_chat = AsyncMock(return_value=MagicMock(id="canvas1"))
            mock_service.get_elements = AsyncMock(return_value=self.elements)
            
            # Search for "Alice" (author_name)
            res_json = await _fetch_elements_impl(chat_id=1, author="Alice")
            res = json.loads(res_json)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]['id'], "1")
            
            # Search for "Bob" (author_nick)
            res_json = await _fetch_elements_impl(chat_id=1, author="bob")
            res = json.loads(res_json)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]['id'], "2")

    async def test_search_contains(self):
        with patch('ai_core.services.canvas_service.canvas_service') as mock_service:
            mock_service.get_or_create_canvas_for_chat = AsyncMock(return_value=MagicMock(id="canvas1"))
            mock_service.get_elements = AsyncMock(return_value=self.elements)
            
            # Search for "project" (in note)
            res_json = await _fetch_elements_impl(chat_id=1, contains="project")
            res = json.loads(res_json)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]['id'], "3")
            
            # Search for "Reply"
            res_json = await _fetch_elements_impl(chat_id=1, contains="reply")
            res = json.loads(res_json)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]['id'], "4")

    async def test_search_time_range(self):
        with patch('ai_core.services.canvas_service.canvas_service') as mock_service:
            mock_service.get_or_create_canvas_for_chat = AsyncMock(return_value=MagicMock(id="canvas1"))
            
            # Mock get_elements to filter by 'since'
            def get_elements_side_effect(canvas_id, limit, since, frame_id):
                filtered = self.elements
                if since:
                    # Ensure timezone awareness
                    if since.tzinfo is None: since = since.replace(tzinfo=timezone.utc)
                    filtered = [e for e in filtered if e.created_at >= since]
                return filtered
                
            mock_service.get_elements = AsyncMock(side_effect=get_elements_side_effect)
            
            # Search "yesterday" (should find element 3 only)
            # Element 5 is day before yesterday. Elements 1,2,4 are today.
            res_json = await _fetch_elements_impl(chat_id=1, time_range="yesterday")
            res = json.loads(res_json)
            
            # Verify service was called with correct start time
            call_args = mock_service.get_elements.call_args
            _, kwargs = call_args
            self.assertEqual(kwargs['since'], self.yesterday_start)
            
            # Verify result
            # Element 3 is yesterday noon. Element 5 is day before.
            # Elements 1,2,4 are today.
            # "yesterday" range is [yesterday_start, today_start).
            # Python loop filters < end_dt (today_start).
            # Service filters >= start_dt (yesterday_start).
            # So we expect only Element 3.
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]['id'], "3")
            
            # Search "today" (should find 1, 2, 4)
            res_json = await _fetch_elements_impl(chat_id=1, time_range="today")
            res = json.loads(res_json)
            self.assertEqual(len(res), 3)
            ids = sorted([r['id'] for r in res])
            self.assertEqual(ids, ["1", "2", "4"])

    async def test_combined_filters(self):
        with patch('ai_core.services.canvas_service.canvas_service') as mock_service:
            mock_service.get_or_create_canvas_for_chat = AsyncMock(return_value=MagicMock(id="canvas1"))
            
            # Mock get_elements to filter by 'since'
            def get_elements_side_effect(canvas_id, limit, since, frame_id):
                filtered = self.elements
                if since:
                    if since.tzinfo is None: since = since.replace(tzinfo=timezone.utc)
                    filtered = [e for e in filtered if e.created_at >= since]
                return filtered
                
            mock_service.get_elements = AsyncMock(side_effect=get_elements_side_effect)
            
            # Search "today" AND created_by "user:123" -> Should be element 1 only
            # Element 5 is user:123 but not today.
            res_json = await _fetch_elements_impl(chat_id=1, time_range="today", created_by="user:123")
            res = json.loads(res_json)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]['id'], "1")

    async def test_limit(self):
        with patch('ai_core.services.canvas_service.canvas_service') as mock_service:
            mock_service.get_or_create_canvas_for_chat = AsyncMock(return_value=MagicMock(id="canvas1"))
            mock_service.get_elements = AsyncMock(return_value=self.elements)
            
            # Limit 2. Should return last 2 sorted by time.
            # Sorted order: 5 (oldest), 3, 4, 2, 1 (newest)
            # Last 2: 2, 1
            res_json = await _fetch_elements_impl(chat_id=1, limit=2)
            res = json.loads(res_json)
            self.assertEqual(len(res), 2)
            ids = [r['id'] for r in res]
            # Expect sorted by created_at ascending in output
            self.assertEqual(ids, ["2", "1"])

if __name__ == '__main__':
    unittest.main()
