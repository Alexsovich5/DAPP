"""
Test data factories for Dinner First dating platform
Creates realistic test data for soul connections, revelations, and user interactions
"""

import factory
import factory.fuzzy
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.models.soul_connection import SoulConnection, ConnectionStage
from app.models.daily_revelation import DailyRevelation, RevelationType
from app.models.message import Message
from app.models.photo_reveal import UserPhoto, PhotoRevealStage
from app.core.security import get_password_hash

fake = Faker()


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating test users with emotional profiles"""
    
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    email = factory.LazyAttribute(lambda obj: fake.unique.email())
    username = factory.LazyAttribute(lambda obj: fake.unique.user_name())
    hashed_password = factory.LazyAttribute(lambda obj: get_password_hash("testpass123"))
    first_name = factory.LazyAttribute(lambda obj: fake.first_name())
    last_name = factory.LazyAttribute(lambda obj: fake.last_name())
    date_of_birth = factory.LazyAttribute(
        lambda obj: fake.date_of_birth(minimum_age=18, maximum_age=65)
    )
    gender = factory.fuzzy.FuzzyChoice(["male", "female", "non-binary", "prefer_not_to_say"])
    is_active = True
    emotional_onboarding_completed = True
    soul_profile_visibility = factory.fuzzy.FuzzyChoice(["hidden", "visible", "connections_only"])
    emotional_depth_score = factory.fuzzy.FuzzyFloat(0.0, 10.0, precision=1)
    created_at = factory.LazyAttribute(lambda obj: fake.date_time_this_year())


class ProfileFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating emotional profiles with soul-focused data"""
    
    class Meta:
        model = Profile
        sqlalchemy_session_persistence = "commit"
    
    user_id = factory.SubFactory(UserFactory)
    full_name = factory.LazyAttribute(lambda obj: f"{fake.first_name()} {fake.last_name()}")
    
    # Basic profile fields that exist in Profile model
    bio = factory.LazyAttribute(
        lambda obj: fake.paragraph(nb_sentences=2, variable_nb_sentences=True)
    )
    cuisine_preferences = factory.LazyAttribute(
        lambda obj: ", ".join(fake.random_choices(
            elements=("Italian", "Asian", "Mediterranean", "Mexican", "American", "French"),
            length=fake.random_int(min=1, max=3)
        ))
    )
    location = factory.LazyAttribute(lambda obj: f"{fake.city()}, {fake.state()}")
    cooking_level = factory.fuzzy.FuzzyChoice(["beginner", "intermediate", "expert"])
    preferred_dining_time = factory.fuzzy.FuzzyChoice(["morning", "afternoon", "evening"])
    
    # Additional valid Profile fields
    dietary_restrictions = factory.LazyAttribute(
        lambda obj: fake.random_element(elements=("None", "Vegetarian", "Vegan", "Gluten-free", "Lactose intolerant"))
    )
    preferred_group_size = factory.fuzzy.FuzzyInteger(2, 8)
    price_range = factory.fuzzy.FuzzyChoice(["budget", "mid-range", "high-end"])
    
    favorite_cuisines = factory.LazyAttribute(lambda obj: [
        fake.random_element(elements=("Italian", "Mexican", "Asian", "Mediterranean", "American"))
    ])


class SoulConnectionFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating soul connections between users"""
    
    class Meta:
        model = SoulConnection
        sqlalchemy_session_persistence = "commit"
    
    user1_id = factory.SubFactory(UserFactory)
    user2_id = factory.SubFactory(UserFactory)
    initiated_by = factory.SelfAttribute('user1_id')
    connection_stage = factory.fuzzy.FuzzyChoice([stage.value for stage in ConnectionStage])
    compatibility_score = factory.fuzzy.FuzzyFloat(50.0, 95.0, precision=1)
    
    compatibility_breakdown = factory.LazyAttribute(lambda obj: {
        "interests": fake.random_int(min=40, max=90),
        "values": fake.random_int(min=45, max=95),
        "demographics": fake.random_int(min=60, max=85),
        "communication": fake.random_int(min=50, max=88),
        "personality": fake.random_int(min=45, max=80),
        "overall_chemistry": fake.random_int(min=55, max=92)
    })
    
    reveal_day = factory.fuzzy.FuzzyInteger(1, 7)
    mutual_reveal_consent = factory.fuzzy.FuzzyChoice([True, False, None])
    first_dinner_completed = False
    created_at = factory.LazyAttribute(lambda obj: fake.date_time_this_month())


class DailyRevelationFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating daily revelations in the 7-day cycle"""
    
    class Meta:
        model = DailyRevelation
        sqlalchemy_session_persistence = "commit"
    
    connection_id = factory.SubFactory(SoulConnectionFactory)
    sender_id = factory.SubFactory(UserFactory)
    day_number = factory.fuzzy.FuzzyInteger(1, 7)
    revelation_type = factory.fuzzy.FuzzyChoice([rtype.value for rtype in RevelationType])
    
    content = factory.LazyAttribute(lambda obj: {
        RevelationType.PERSONAL_VALUE.value: "Family and loyalty are the foundations of my life.",
        RevelationType.MEANINGFUL_EXPERIENCE.value: "Volunteering at the shelter taught me about compassion.",
        RevelationType.HOPE_OR_DREAM.value: "I dream of building a sustainable community garden.",
        RevelationType.WHAT_MAKES_LAUGH.value: "Dad jokes and wordplay never fail to make me smile.",
        RevelationType.CHALLENGE_OVERCOME.value: "Learning to trust again after heartbreak made me stronger.",
        RevelationType.IDEAL_CONNECTION.value: "A partner who challenges me to grow while accepting who I am.",
        RevelationType.PHOTO_REVEAL.value: "Ready to share my photo - excited to see the real you!"
    }.get(obj.revelation_type, "A meaningful reflection from my heart to yours."))
    
    created_at = factory.LazyAttribute(lambda obj: fake.date_time_this_month())


class MessageFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating messages between connected users"""
    
    class Meta:
        model = Message
        sqlalchemy_session_persistence = "commit"
    
    connection_id = factory.SubFactory(SoulConnectionFactory)
    sender_id = factory.SubFactory(UserFactory)
    message_text = factory.LazyAttribute(lambda obj: fake.sentence(nb_words=fake.random_int(min=5, max=20)))
    message_type = factory.fuzzy.FuzzyChoice(["text", "revelation", "photo", "emoji_reaction"])
    created_at = factory.LazyAttribute(lambda obj: fake.date_time_this_month())


class UserPhotoFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating user photo records"""
    
    class Meta:
        model = UserPhoto
        sqlalchemy_session_persistence = "commit"
    
    user_id = factory.SubFactory(UserFactory)
    photo_uuid = factory.LazyAttribute(lambda obj: fake.uuid4())
    original_filename = factory.LazyAttribute(lambda obj: f"{fake.word()}.jpg")
    file_path = factory.LazyAttribute(lambda obj: f"/encrypted/photos/{fake.uuid4()}.enc")
    file_size = factory.fuzzy.FuzzyInteger(100000, 5000000)  # 100KB to 5MB
    mime_type = "image/jpeg"
    encryption_key_hash = factory.LazyAttribute(lambda obj: fake.sha256())
    upload_timestamp = factory.LazyAttribute(lambda obj: fake.date_time_this_week())


# Backwards-compatible alias used by some fixtures/tests
PhotoRevealFactory = UserPhotoFactory

def setup_factories(session: Session):
    """Setup factories with database session"""
    UserFactory._meta.sqlalchemy_session = session
    ProfileFactory._meta.sqlalchemy_session = session
    SoulConnectionFactory._meta.sqlalchemy_session = session
    DailyRevelationFactory._meta.sqlalchemy_session = session
    MessageFactory._meta.sqlalchemy_session = session
    PhotoRevealFactory._meta.sqlalchemy_session = session


def create_complete_soul_connection(session: Session):
    """Create a complete soul connection with users, profiles, and revelations"""
    # Setup factories with session
    setup_factories(session)
    
    # Create two users with emotional profiles
    user1 = UserFactory()
    user2 = UserFactory()
    
    profile1 = ProfileFactory(user_id=user1.id)
    profile2 = ProfileFactory(user_id=user2.id)
    
    # Create soul connection
    connection = SoulConnectionFactory(
        user1_id=user1.id,
        user2_id=user2.id
    )
    
    # Create some revelations
    revelations = []
    for day in range(1, 4):  # First 3 days of revelations
        rev1 = DailyRevelationFactory(
            connection_id=connection.id,
            sender_id=user1.id,
            day_number=day
        )
        rev2 = DailyRevelationFactory(
            connection_id=connection.id,
            sender_id=user2.id,
            day_number=day
        )
        revelations.extend([rev1, rev2])
    
    # Create some messages
    messages = []
    for _ in range(5):
        msg = MessageFactory(
            connection_id=connection.id,
            sender_id=fake.random_element([user1.id, user2.id])
        )
        messages.append(msg)
    
    return {
        'users': [user1, user2],
        'profiles': [profile1, profile2],
        'connection': connection,
        'revelations': revelations,
        'messages': messages
    }