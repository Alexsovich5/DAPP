"""
Comprehensive Model Tests - High-impact coverage for models and schemas
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile, VerificationStatus
from app.models.match import Match, MatchStatus
from app.models.message import Message, MessageType
from app.models.daily_revelation import DailyRevelation, RevelationStatus
from app.models.soul_connection import SoulConnection, ConnectionStage
from app.core.security import get_password_hash


class TestUserModel:
    """Test User model functionality"""

    def test_user_creation(self, db_session):
        """Test basic user creation"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_profile_relationship(self, db_session):
        """Test user-profile relationship"""
        user = User(
            email="profile_test@example.com",
            username="profileuser",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        profile = Profile(
            user_id=user.id,
            full_name="Profile User",
            bio="Test bio",
            location="Test City"
        )
        db_session.add(profile)
        db_session.commit()
        
        # Test relationship
        assert user.profile is not None
        assert user.profile.full_name == "Profile User"
        assert profile.user_id == user.id

    def test_user_string_representation(self, db_session):
        """Test user string representation"""
        user = User(
            email="repr@test.com",
            username="repruser",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        user_str = str(user)
        assert "repruser" in user_str or "repr@test.com" in user_str

    def test_user_with_all_optional_fields(self, db_session):
        """Test user creation with all optional fields"""
        user = User(
            email="full@test.com",
            username="fulluser",
            hashed_password=get_password_hash("password"),
            first_name="Full",
            last_name="User",
            date_of_birth=datetime.now().date() - timedelta(days=10000),  # ~27 years old
            gender="other",
            location="Full City, State",
            bio="Full user bio",
            interests=["coding", "testing", "databases"],
            dietary_preferences=["vegetarian"],
            is_active=True,
            is_profile_complete=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.first_name == "Full"
        assert user.last_name == "User"
        assert user.gender == "other"
        assert user.location == "Full City, State"
        assert len(user.interests) == 3
        assert "vegetarian" in user.dietary_preferences


class TestProfileModel:
    """Test Profile model functionality"""

    def test_profile_creation(self, db_session):
        """Test basic profile creation"""
        user = User(
            email="profile@test.com",
            username="profiletest",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        profile = Profile(
            user_id=user.id,
            full_name="Profile Test",
            bio="Test profile bio",
            location="Profile City",
            cuisine_preferences="Italian, Mexican",
            dietary_restrictions="None",
            is_verified=False,
            verification_status=VerificationStatus.UNVERIFIED
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        
        assert profile.id is not None
        assert profile.user_id == user.id
        assert profile.full_name == "Profile Test"
        assert profile.verification_status == VerificationStatus.UNVERIFIED

    def test_profile_with_photos(self, db_session):
        """Test profile with photo URLs"""
        user = User(
            email="photos@test.com",
            username="photosuser",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        profile = Profile(
            user_id=user.id,
            full_name="Photos User",
            profile_photos=["photo1.jpg", "photo2.jpg", "photo3.jpg"]
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        
        assert len(profile.profile_photos) == 3
        assert "photo1.jpg" in profile.profile_photos

    def test_profile_verification_statuses(self, db_session):
        """Test all verification status values"""
        user = User(
            email="verification@test.com",
            username="verifyuser",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Test all verification statuses
        statuses_to_test = [
            VerificationStatus.UNVERIFIED,
            VerificationStatus.PENDING,
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED
        ]
        
        for status in statuses_to_test:
            profile = Profile(
                user_id=user.id,
                full_name=f"User {status.value}",
                verification_status=status
            )
            db_session.add(profile)
        
        db_session.commit()
        
        # Verify all statuses were saved
        profiles = db_session.query(Profile).filter(Profile.user_id == user.id).all()
        saved_statuses = [p.verification_status for p in profiles]
        
        for status in statuses_to_test:
            assert status in saved_statuses


class TestMatchModel:
    """Test Match model functionality"""

    def test_match_creation(self, db_session):
        """Test basic match creation"""
        # Create users
        sender = User(
            email="sender@test.com",
            username="sender",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        receiver = User(
            email="receiver@test.com", 
            username="receiver",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add_all([sender, receiver])
        db_session.commit()
        
        match = Match(
            sender_id=sender.id,
            receiver_id=receiver.id,
            status=MatchStatus.PENDING,
            restaurant_preference="Italian"
        )
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)
        
        assert match.id is not None
        assert match.sender_id == sender.id
        assert match.receiver_id == receiver.id
        assert match.status == MatchStatus.PENDING
        assert match.created_at is not None

    def test_match_status_transitions(self, db_session):
        """Test match status transitions"""
        sender = User(
            email="status_sender@test.com",
            username="statussender", 
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        receiver = User(
            email="status_receiver@test.com",
            username="statusreceiver",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add_all([sender, receiver])
        db_session.commit()
        
        match = Match(
            sender_id=sender.id,
            receiver_id=receiver.id,
            status=MatchStatus.PENDING
        )
        db_session.add(match)
        db_session.commit()
        
        # Test status transitions
        statuses_to_test = [
            MatchStatus.PENDING,
            MatchStatus.ACCEPTED,
            MatchStatus.REJECTED,
            MatchStatus.EXPIRED
        ]
        
        for status in statuses_to_test:
            match.status = status
            db_session.commit()
            db_session.refresh(match)
            assert match.status == status

    def test_match_relationships(self, db_session):
        """Test match user relationships"""
        sender = User(
            email="rel_sender@test.com",
            username="relsender",
            hashed_password=get_password_hash("password"),
            first_name="Sender",
            is_active=True
        )
        receiver = User(
            email="rel_receiver@test.com",
            username="relreceiver", 
            hashed_password=get_password_hash("password"),
            first_name="Receiver",
            is_active=True
        )
        db_session.add_all([sender, receiver])
        db_session.commit()
        
        match = Match(
            sender_id=sender.id,
            receiver_id=receiver.id,
            status=MatchStatus.ACCEPTED
        )
        db_session.add(match)
        db_session.commit()
        
        # Test relationships work
        assert match.sender.first_name == "Sender"
        assert match.receiver.first_name == "Receiver"


class TestMessageModel:
    """Test Message model functionality"""

    def test_message_creation(self, db_session):
        """Test basic message creation"""
        sender = User(
            email="msg_sender@test.com",
            username="msgsender",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        receiver = User(
            email="msg_receiver@test.com",
            username="msgreceiver",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add_all([sender, receiver])
        db_session.commit()
        
        message = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            content="Hello, this is a test message!",
            message_type=MessageType.TEXT
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        assert message.id is not None
        assert message.content == "Hello, this is a test message!"
        assert message.message_type == MessageType.TEXT
        assert message.is_read is False
        assert message.created_at is not None

    def test_message_types(self, db_session):
        """Test different message types"""
        sender = User(
            email="types_sender@test.com",
            username="typessender",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        receiver = User(
            email="types_receiver@test.com",
            username="typesreceiver",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add_all([sender, receiver])
        db_session.commit()
        
        message_types_to_test = [
            (MessageType.TEXT, "Text message"),
            (MessageType.IMAGE, "Image message"),
            (MessageType.REVELATION, "Revelation message"),
            (MessageType.SYSTEM, "System message")
        ]
        
        for msg_type, content in message_types_to_test:
            message = Message(
                sender_id=sender.id,
                receiver_id=receiver.id,
                content=content,
                message_type=msg_type
            )
            db_session.add(message)
        
        db_session.commit()
        
        # Verify all message types were saved
        messages = db_session.query(Message).filter(Message.sender_id == sender.id).all()
        saved_types = [m.message_type for m in messages]
        
        for msg_type, _ in message_types_to_test:
            assert msg_type in saved_types

    def test_message_read_status(self, db_session):
        """Test message read status functionality"""
        sender = User(
            email="read_sender@test.com",
            username="readsender",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        receiver = User(
            email="read_receiver@test.com",
            username="readreceiver",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add_all([sender, receiver])
        db_session.commit()
        
        message = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            content="Unread message",
            message_type=MessageType.TEXT,
            is_read=False
        )
        db_session.add(message)
        db_session.commit()
        
        assert message.is_read is False
        assert message.read_at is None
        
        # Mark as read
        message.is_read = True
        message.read_at = datetime.utcnow()
        db_session.commit()
        
        assert message.is_read is True
        assert message.read_at is not None


class TestDailyRevelationModel:
    """Test Daily Revelation model functionality"""

    def test_revelation_creation(self, db_session):
        """Test basic revelation creation"""
        user = User(
            email="revelation@test.com",
            username="revelationuser",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        revelation = DailyRevelation(
            user_id=user.id,
            day_number=1,
            prompt="What is your greatest aspiration?",
            response="To make a positive impact on the world",
            status=RevelationStatus.DRAFT
        )
        db_session.add(revelation)
        db_session.commit()
        db_session.refresh(revelation)
        
        assert revelation.id is not None
        assert revelation.user_id == user.id
        assert revelation.day_number == 1
        assert revelation.status == RevelationStatus.DRAFT

    def test_revelation_statuses(self, db_session):
        """Test all revelation status values"""
        user = User(
            email="rev_status@test.com",
            username="revstatus",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        statuses_to_test = [
            RevelationStatus.DRAFT,
            RevelationStatus.SHARED,
            RevelationStatus.PRIVATE
        ]
        
        for i, status in enumerate(statuses_to_test):
            revelation = DailyRevelation(
                user_id=user.id,
                day_number=i + 1,
                prompt=f"Prompt for day {i + 1}",
                response=f"Response for day {i + 1}",
                status=status
            )
            db_session.add(revelation)
        
        db_session.commit()
        
        # Verify all statuses were saved
        revelations = db_session.query(DailyRevelation).filter(DailyRevelation.user_id == user.id).all()
        saved_statuses = [r.status for r in revelations]
        
        for status in statuses_to_test:
            assert status in saved_statuses


class TestSoulConnectionModel:
    """Test Soul Connection model functionality"""

    def test_soul_connection_creation(self, db_session):
        """Test basic soul connection creation"""
        user1 = User(
            email="soul1@test.com",
            username="soul1",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        user2 = User(
            email="soul2@test.com",
            username="soul2",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        connection = SoulConnection(
            user1_id=user1.id,
            user2_id=user2.id,
            stage=ConnectionStage.SOUL_DISCOVERY,
            compatibility_score=85.5,
            current_day=1
        )
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)
        
        assert connection.id is not None
        assert connection.user1_id == user1.id
        assert connection.user2_id == user2.id
        assert connection.stage == ConnectionStage.SOUL_DISCOVERY
        assert connection.compatibility_score == 85.5

    def test_connection_stages(self, db_session):
        """Test all connection stage values"""
        user1 = User(
            email="stage1@test.com",
            username="stage1",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        user2 = User(
            email="stage2@test.com",
            username="stage2", 
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        stages_to_test = [
            ConnectionStage.SOUL_DISCOVERY,
            ConnectionStage.REVELATION_SHARING,
            ConnectionStage.PHOTO_REVEAL,
            ConnectionStage.DINNER_PLANNING,
            ConnectionStage.COMPLETED
        ]
        
        for i, stage in enumerate(stages_to_test):
            connection = SoulConnection(
                user1_id=user1.id,
                user2_id=user2.id,
                stage=stage,
                current_day=i + 1
            )
            db_session.add(connection)
        
        db_session.commit()
        
        # Verify all stages were saved
        connections = db_session.query(SoulConnection).filter(SoulConnection.user1_id == user1.id).all()
        saved_stages = [c.stage for c in connections]
        
        for stage in stages_to_test:
            assert stage in saved_stages

    def test_connection_relationships(self, db_session):
        """Test soul connection user relationships"""
        user1 = User(
            email="rel1@test.com",
            username="rel1",
            hashed_password=get_password_hash("password"),
            first_name="User1",
            is_active=True
        )
        user2 = User(
            email="rel2@test.com",
            username="rel2",
            hashed_password=get_password_hash("password"), 
            first_name="User2",
            is_active=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        connection = SoulConnection(
            user1_id=user1.id,
            user2_id=user2.id,
            stage=ConnectionStage.REVELATION_SHARING
        )
        db_session.add(connection)
        db_session.commit()
        
        # Test relationships work
        assert connection.user1.first_name == "User1"
        assert connection.user2.first_name == "User2"


class TestModelIntegration:
    """Test model integration and complex relationships"""

    def test_complete_user_ecosystem(self, db_session):
        """Test creating a complete user ecosystem"""
        # Create users
        user1 = User(
            email="eco1@test.com",
            username="eco1",
            hashed_password=get_password_hash("password"),
            first_name="Eco",
            last_name="One",
            is_active=True
        )
        user2 = User(
            email="eco2@test.com",
            username="eco2",
            hashed_password=get_password_hash("password"),
            first_name="Eco",
            last_name="Two", 
            is_active=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Create profiles
        profile1 = Profile(
            user_id=user1.id,
            full_name="Eco One",
            bio="First user in ecosystem test"
        )
        profile2 = Profile(
            user_id=user2.id,
            full_name="Eco Two",
            bio="Second user in ecosystem test"
        )
        db_session.add_all([profile1, profile2])
        
        # Create match
        match = Match(
            sender_id=user1.id,
            receiver_id=user2.id,
            status=MatchStatus.ACCEPTED
        )
        db_session.add(match)
        
        # Create messages
        message1 = Message(
            sender_id=user1.id,
            receiver_id=user2.id,
            content="Hello from user 1",
            message_type=MessageType.TEXT
        )
        message2 = Message(
            sender_id=user2.id,
            receiver_id=user1.id,
            content="Hello back from user 2",
            message_type=MessageType.TEXT
        )
        db_session.add_all([message1, message2])
        
        # Create soul connection
        connection = SoulConnection(
            user1_id=user1.id,
            user2_id=user2.id,
            stage=ConnectionStage.REVELATION_SHARING,
            compatibility_score=92.0
        )
        db_session.add(connection)
        
        # Create revelations
        revelation1 = DailyRevelation(
            user_id=user1.id,
            day_number=1,
            prompt="Test prompt 1",
            response="Test response 1",
            status=RevelationStatus.SHARED
        )
        revelation2 = DailyRevelation(
            user_id=user2.id,
            day_number=1,
            prompt="Test prompt 1",
            response="Test response 2",
            status=RevelationStatus.SHARED
        )
        db_session.add_all([revelation1, revelation2])
        
        db_session.commit()
        
        # Verify ecosystem is connected
        assert user1.profile.full_name == "Eco One"
        assert user2.profile.full_name == "Eco Two"
        
        # Check match exists
        matches = db_session.query(Match).filter(
            ((Match.sender_id == user1.id) & (Match.receiver_id == user2.id)) |
            ((Match.sender_id == user2.id) & (Match.receiver_id == user1.id))
        ).all()
        assert len(matches) >= 1
        
        # Check messages exist
        messages = db_session.query(Message).filter(
            ((Message.sender_id == user1.id) & (Message.receiver_id == user2.id)) |
            ((Message.sender_id == user2.id) & (Message.receiver_id == user1.id))
        ).all()
        assert len(messages) >= 2
        
        # Check soul connection exists
        connections = db_session.query(SoulConnection).filter(
            ((SoulConnection.user1_id == user1.id) & (SoulConnection.user2_id == user2.id)) |
            ((SoulConnection.user1_id == user2.id) & (SoulConnection.user2_id == user1.id))
        ).all()
        assert len(connections) >= 1
        
        # Check revelations exist
        user1_revelations = db_session.query(DailyRevelation).filter(DailyRevelation.user_id == user1.id).all()
        user2_revelations = db_session.query(DailyRevelation).filter(DailyRevelation.user_id == user2.id).all()
        assert len(user1_revelations) >= 1
        assert len(user2_revelations) >= 1