"""
Unit tests for message service functionality
Tests message operations, validation, and service methods without external dependencies
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.message_service import MessageService, MessageResult, ConversationSummary
from app.models.message import Message
from app.models.user import User
from app.models.soul_connection import SoulConnection


@pytest.mark.unit
class TestMessageService:
    """Test suite for MessageService class"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def message_service(self, mock_db):
        """Create MessageService instance with mock database"""
        return MessageService(mock_db)
    
    def test_message_service_initialization(self, message_service, mock_db):
        """Test MessageService initialization"""
        assert message_service.db == mock_db
        assert message_service.max_message_length == 5000
        assert message_service.min_message_length == 1
    
    def test_validate_message_content_valid(self, message_service):
        """Test message content validation with valid content"""
        assert message_service.validate_message_content("Hello world") is True
        assert message_service.validate_message_content("A") is True
        assert message_service.validate_message_content("   Valid message   ") is True
        assert message_service.validate_message_content("x" * 1000) is True
    
    def test_validate_message_content_invalid(self, message_service):
        """Test message content validation with invalid content"""
        # Empty or whitespace only
        assert message_service.validate_message_content("") is False
        assert message_service.validate_message_content("   ") is False
        assert message_service.validate_message_content(None) is False
        
        # Too long
        too_long = "x" * (message_service.max_message_length + 1)
        assert message_service.validate_message_content(too_long) is False
    
    def test_filter_message_content_email_filtering(self, message_service):
        """Test message content filtering removes emails"""
        content = "Contact me at user@example.com for details"
        filtered = message_service.filter_message_content(content)
        assert "[email hidden]" in filtered
        assert "user@example.com" not in filtered
    
    def test_filter_message_content_phone_filtering(self, message_service):
        """Test message content filtering removes phone numbers"""
        content = "Call me at 123-456-7890 tonight"
        filtered = message_service.filter_message_content(content)
        assert "[phone hidden]" in filtered
        assert "123-456-7890" not in filtered
    
    def test_filter_message_content_empty_input(self, message_service):
        """Test message content filtering with empty input"""
        assert message_service.filter_message_content("") == ""
        assert message_service.filter_message_content(None) == ""
        assert message_service.filter_message_content("   ") == ""
    
    def test_filter_message_content_whitespace_trimming(self, message_service):
        """Test message content filtering trims whitespace"""
        content = "   Hello world   "
        filtered = message_service.filter_message_content(content)
        assert filtered == "Hello world"
    
    def test_create_message_success(self, message_service, mock_db):
        """Test successful message creation"""
        # Mock database objects
        mock_connection = Mock()
        mock_connection.id = 123
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        mock_message = Mock(spec=Message)
        mock_message.id = 456
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with patch.object(Message, '__new__', return_value=mock_message):
            result = message_service.create_message(1, 2, "Test message")
        
        assert result == mock_message
        mock_db.add.assert_called_once_with(mock_message)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_message)
    
    def test_create_message_invalid_content(self, message_service, mock_db):
        """Test message creation with invalid content"""
        result = message_service.create_message(1, 2, "")
        assert result is None
        
        result = message_service.create_message(1, 2, "   ")
        assert result is None
        
        too_long = "x" * (message_service.max_message_length + 1)
        result = message_service.create_message(1, 2, too_long)
        assert result is None
    
    def test_create_message_no_connection_fallback(self, message_service, mock_db):
        """Test message creation when no connection exists (fallback to ID 1)"""
        # Mock no connection found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        mock_message = Mock(spec=Message)
        mock_message.id = 456
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with patch.object(Message, '__new__', return_value=mock_message):
            result = message_service.create_message(1, 2, "Test message")
        
        assert result == mock_message
    
    def test_create_message_database_error(self, message_service, mock_db):
        """Test message creation handles database errors"""
        mock_db.query.side_effect = Exception("Database error")
        mock_db.rollback = Mock()
        
        result = message_service.create_message(1, 2, "Test message")
        
        assert result is None
        mock_db.rollback.assert_called_once()
    
    def test_get_conversation_success(self, message_service, mock_db):
        """Test successful conversation retrieval"""
        mock_messages = [Mock(spec=Message) for _ in range(3)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_messages
        
        result = message_service.get_conversation(1, 2, limit=10)
        
        assert result == mock_messages
        assert len(result) == 3
    
    def test_get_conversation_database_error(self, message_service, mock_db):
        """Test conversation retrieval handles database errors"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = message_service.get_conversation(1, 2)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_send_message_empty_content(self, message_service, mock_db):
        """Test send_message with empty content"""
        result = await message_service.send_message(1, 1, "", db=mock_db)
        
        assert result.success is False
        assert result.error == "empty_content"
        assert "empty" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_send_message_content_too_long(self, message_service, mock_db):
        """Test send_message with content too long"""
        long_content = "x" * (message_service.max_message_length + 1)
        result = await message_service.send_message(1, 1, long_content, db=mock_db)
        
        assert result.success is False
        assert result.error == "content_too_long"
        assert "too long" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_send_message_invalid_connection(self, message_service, mock_db):
        """Test send_message with invalid connection"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await message_service.send_message(1, 999, "Test message", db=mock_db)
        
        assert result.success is False
        assert result.error == "invalid_connection"
        assert "not found" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_send_message_rate_limited(self, message_service, mock_db):
        """Test send_message when rate limited"""
        # Mock connection exists
        mock_connection = Mock()
        mock_connection.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Mock rate limit check
        with patch.object(message_service, '_check_rate_limit', new_callable=AsyncMock) as mock_rate_check:
            mock_rate_check.return_value = {
                "allowed": False,
                "message": "Rate limit exceeded"
            }
            
            result = await message_service.send_message(1, 1, "Test message", db=mock_db)
        
        assert result.success is False
        assert result.error == "rate_limited"
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, message_service, mock_db):
        """Test successful message sending"""
        # Mock connection
        mock_connection = Mock()
        mock_connection.id = 1
        mock_connection.total_messages_exchanged = 5
        mock_connection.get_partner_id.return_value = 2
        
        # Mock sender user
        mock_sender = Mock()
        mock_sender.id = 1
        mock_sender.current_emotional_state = "happy"
        mock_sender.total_messages_sent = 10
        
        # Mock queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_connection, mock_sender]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock rate limit check
        with patch.object(message_service, '_check_rate_limit', new_callable=AsyncMock) as mock_rate_check:
            mock_rate_check.return_value = {"allowed": True}
            
            # Mock real-time delivery
            with patch.object(message_service, '_deliver_message_realtime', new_callable=AsyncMock) as mock_deliver:
                mock_deliver.return_value = True
                
                # Mock analytics
                with patch('app.services.message_service.analytics_service.track_user_event', new_callable=AsyncMock):
                    with patch.object(Message, '__new__') as mock_message_new:
                        mock_message = Mock()
                        mock_message.id = 123
                        mock_message.emotional_state = "happy"
                        mock_message.is_soul_revelation = False
                        mock_message_new.return_value = mock_message
                        
                        result = await message_service.send_message(1, 1, "Test message", db=mock_db)
        
        assert result.success is True
        assert result.message_id == 123
        assert result.delivered is True
    
    @pytest.mark.asyncio
    async def test_get_conversation_messages_success(self, message_service, mock_db):
        """Test successful conversation messages retrieval"""
        # Mock connection
        mock_connection = Mock()
        mock_connection.id = 1
        mock_connection.get_partner_id.return_value = 2
        mock_connection.current_energy_level = "high"
        mock_connection.stage = "deep_connection"
        
        # Mock partner user
        mock_partner = Mock()
        mock_partner.first_name = "Jane"
        mock_partner.last_name = "Doe"
        
        # Mock messages
        mock_message = Mock()
        mock_message.id = 1
        mock_message.sender_id = 2
        mock_message.content = "Hello"
        mock_message.emotional_state = "happy"
        mock_message.message_energy = "medium"
        mock_message.is_soul_revelation = False
        mock_message.is_read = False
        mock_message.created_at = datetime.utcnow()
        mock_message.read_at = None
        
        # Setup database query chain more carefully
        connection_query = Mock()
        connection_query.filter.return_value.first.return_value = mock_connection
        
        message_query = Mock()
        message_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_message]
        
        partner_query = Mock()  
        partner_query.filter.return_value.first.return_value = mock_partner
        
        # Mock the query method to return different objects for different queries
        def mock_query_side_effect(model):
            if hasattr(model, '__name__') and model.__name__ == 'SoulConnection':
                return connection_query
            elif hasattr(model, '__name__') and model.__name__ == 'Message':
                return message_query
            elif hasattr(model, '__name__') and model.__name__ == 'User':
                return partner_query
            else:
                return Mock()
        
        mock_db.query.side_effect = mock_query_side_effect
        mock_db.commit = Mock()
        
        result = await message_service.get_conversation_messages(1, 1, db=mock_db)
        
        assert result["success"] is True
        assert len(result["messages"]) == 1
        assert result["connection"]["partner_name"] == "Jane Doe"
    
    @pytest.mark.asyncio
    async def test_get_conversation_messages_no_access(self, message_service, mock_db):
        """Test conversation messages retrieval with no access"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await message_service.get_conversation_messages(1, 999, db=mock_db)
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_get_user_conversations_success(self, message_service, mock_db):
        """Test successful user conversations retrieval"""
        # Mock connection
        mock_connection = Mock()
        mock_connection.id = 1
        mock_connection.total_messages_exchanged = 10
        mock_connection.last_message_at = datetime.utcnow()
        mock_connection.current_energy_level = "high"
        mock_connection.stage = "deep_connection"
        mock_connection.get_partner_id.return_value = 2
        
        # Mock partner user
        mock_partner = Mock()
        mock_partner.first_name = "Jane"
        mock_partner.last_name = "Doe"
        mock_partner.current_emotional_state = "happy"
        
        # Mock last message
        mock_last_message = Mock()
        mock_last_message.content = "Last message"
        
        # Setup queries
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_connection]
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_partner, mock_last_message]
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        
        result = await message_service.get_user_conversations(1, db=mock_db)
        
        assert result["success"] is True
        assert len(result["conversations"]) == 1
        assert result["conversations"][0]["partner"]["name"] == "Jane Doe"
        assert result["conversations"][0]["metrics"]["unread_count"] == 3
    
    @pytest.mark.asyncio
    async def test_update_typing_status_success(self, message_service, mock_db):
        """Test successful typing status update"""
        # Mock connection
        mock_connection = Mock()
        mock_connection.id = 1
        mock_connection.get_partner_id.return_value = 2
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Mock the realtime_manager module and method
        with patch('app.services.message_service.realtime_manager') as mock_realtime_manager:
            mock_realtime_manager.handle_typing_indicator = AsyncMock()
            result = await message_service.update_typing_status(1, 1, True, db=mock_db)
        
        assert result is True
        mock_realtime_manager.handle_typing_indicator.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_typing_status_no_connection(self, message_service, mock_db):
        """Test typing status update with no connection"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await message_service.update_typing_status(1, 999, True, db=mock_db)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mark_messages_as_read_success(self, message_service, mock_db):
        """Test successful marking messages as read"""
        # Mock connection
        mock_connection = Mock()
        mock_connection.get_partner_id.return_value = 2
        
        # Setup the query chains differently for update vs first
        message_query = Mock()
        message_query.filter.return_value.update.return_value = 3  # 3 messages updated
        
        connection_query = Mock()
        connection_query.filter.return_value.first.return_value = mock_connection
        
        # Mock db.query to return appropriate mock for each call
        mock_db.query.side_effect = [message_query, connection_query]
        mock_db.commit = Mock()
        
        with patch('app.services.message_service.realtime_manager') as mock_realtime_manager:
            mock_realtime_manager.send_to_user = AsyncMock()
            result = await message_service.mark_messages_as_read(1, 1, db=mock_db)
        
        assert result is True
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_messages_as_read_no_updates(self, message_service, mock_db):
        """Test marking messages as read when no updates needed"""
        mock_db.query.return_value.filter.return_value.update.return_value = 0  # No messages updated
        mock_db.commit = Mock()
        
        result = await message_service.mark_messages_as_read(1, 1, db=mock_db)
        
        assert result is True
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self, message_service, mock_db):
        """Test rate limit check when within limits"""
        message_service.rate_limit_messages_per_minute = 10
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        result = await message_service._check_rate_limit(1, 1, mock_db)
        
        assert result["allowed"] is True
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, message_service, mock_db):
        """Test rate limit check when limit exceeded"""
        message_service.rate_limit_messages_per_minute = 10
        mock_db.query.return_value.filter.return_value.count.return_value = 15
        
        result = await message_service._check_rate_limit(1, 1, mock_db)
        
        assert result["allowed"] is False
        assert "rate limit" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_database_error(self, message_service, mock_db):
        """Test rate limit check handles database errors gracefully"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = await message_service._check_rate_limit(1, 1, mock_db)
        
        assert result["allowed"] is True  # Allow on error
    
    @pytest.mark.asyncio
    async def test_deliver_message_realtime_success(self, message_service, mock_db):
        """Test successful real-time message delivery"""
        # Mock message and sender
        mock_message = Mock()
        mock_message.id = 1
        mock_message.connection_id = 1
        mock_message.content = "Test message"
        mock_message.emotional_state = "happy"
        mock_message.message_energy = "medium"
        mock_message.is_soul_revelation = False
        mock_message.created_at = datetime.utcnow()
        
        mock_sender = Mock()
        mock_sender.id = 1
        mock_sender.first_name = "John"
        mock_sender.last_name = "Doe"
        
        with patch('app.services.message_service.realtime_manager.send_to_user', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            result = await message_service._deliver_message_realtime(mock_message, 2, mock_sender, mock_db)
        
        assert result is True
        mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deliver_message_realtime_failure(self, message_service, mock_db):
        """Test real-time message delivery failure"""
        mock_message = Mock()
        mock_message.id = 1
        mock_message.connection_id = 1
        mock_message.content = "Test message"
        mock_message.emotional_state = "happy"
        mock_message.message_energy = "medium"
        mock_message.is_soul_revelation = False
        mock_message.created_at = datetime.utcnow()
        
        mock_sender = Mock()
        mock_sender.id = 1
        mock_sender.first_name = "John"
        mock_sender.last_name = "Doe"
        
        with patch('app.services.message_service.realtime_manager.send_to_user', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("WebSocket error")
            
            result = await message_service._deliver_message_realtime(mock_message, 2, mock_sender, mock_db)
        
        assert result is False


@pytest.mark.unit
class TestMessageResult:
    """Test suite for MessageResult dataclass"""
    
    def test_message_result_creation(self):
        """Test MessageResult creation with all fields"""
        result = MessageResult(
            success=True,
            message_id=123,
            message="Success",
            delivered=True,
            error=None
        )
        
        assert result.success is True
        assert result.message_id == 123
        assert result.message == "Success"
        assert result.delivered is True
        assert result.error is None
    
    def test_message_result_with_error(self):
        """Test MessageResult creation with error"""
        result = MessageResult(
            success=False,
            message_id=None,
            message="Failed to send",
            delivered=False,
            error="rate_limited"
        )
        
        assert result.success is False
        assert result.message_id is None
        assert result.error == "rate_limited"


@pytest.mark.unit
class TestConversationSummary:
    """Test suite for ConversationSummary dataclass"""
    
    def test_conversation_summary_creation(self):
        """Test ConversationSummary creation"""
        summary = ConversationSummary(
            connection_id=1,
            partner_id=2,
            partner_name="Jane Doe",
            total_messages=50,
            last_message_at=datetime.utcnow(),
            last_message_content="Hello there",
            unread_count=3,
            emotional_energy="high",
            conversation_stage="deep_connection"
        )
        
        assert summary.connection_id == 1
        assert summary.partner_id == 2
        assert summary.partner_name == "Jane Doe"
        assert summary.total_messages == 50
        assert summary.unread_count == 3
        assert summary.emotional_energy == "high"
        assert summary.conversation_stage == "deep_connection"


@pytest.mark.unit
class TestServiceFactory:
    """Test suite for service factory functions"""
    
    def test_get_message_service_with_session(self):
        """Test get_message_service with database session"""
        mock_session = Mock(spec=Session)
        service = message_service.get_message_service(mock_session)
        
        assert isinstance(service, MessageService)
        assert service.db == mock_session
    
    def test_get_message_service_without_session(self):
        """Test get_message_service without database session returns mock"""
        service = message_service.get_message_service()
        
        # Should return mock service with basic methods
        assert hasattr(service, 'send_message')
        assert hasattr(service, 'get_conversations')
        assert hasattr(service, 'validate_message_content')
    
    def test_mock_service_validate_method(self):
        """Test mock service validation method"""
        service = message_service.get_message_service()
        
        # Test the lambda function directly
        validate_func = service.validate_message_content
        assert validate_func("test") is True
        assert validate_func("") is False
        assert validate_func("  ") is False


# Import the module for factory function testing
from app.services import message_service