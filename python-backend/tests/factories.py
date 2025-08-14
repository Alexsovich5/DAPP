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
    
    # Soul Before Skin specific fields
    life_philosophy = factory.LazyAttribute(
        lambda obj: fake.paragraph(nb_sentences=3, variable_nb_sentences=True)
    )
    core_values = factory.LazyAttribute(lambda obj: {
        "relationship_values": fake.random_choices(
            elements=("commitment", "growth", "adventure", "stability", "creativity"),
            length=fake.random_int(min=2, max=4)
        ),
        "life_priorities": fake.random_choices(
            elements=("family", "career", "travel", "spirituality", "health", "learning"),
            length=fake.random_int(min=2, max=3)
        ),
        "communication_style": fake.random_element(
            elements=("deep_conversations", "playful_banter", "thoughtful_listener", "storyteller")
        )
    })
    
    interests = factory.LazyAttribute(lambda obj: fake.random_choices(
        elements=(
            "cooking", "reading", "hiking", "photography", "music", "art", "travel",
            "meditation", "yoga", "dancing", "writing", "gardening", "volunteering"
        ),
        length=fake.random_int(min=3, max=7)
    ))
    
    personality_traits = factory.LazyAttribute(lambda obj: {
        "openness": fake.random_int(min=1, max=10),
        "conscientiousness": fake.random_int(min=1, max=10),
        "extraversion": fake.random_int(min=1, max=10),
        "agreeableness": fake.random_int(min=1, max=10),
        "neuroticism": fake.random_int(min=1, max=10),
        "emotional_intelligence": fake.random_int(min=1, max=10)
    })
    
    communication_style = factory.LazyAttribute(lambda obj: {
        "preferred_depth": fake.random_element(elements=("surface", "moderate", "deep")),
        "response_style": fake.random_element(elements=("quick", "thoughtful", "detailed")),
        "conflict_resolution": fake.random_element(elements=("direct", "diplomatic", "avoidant"))
    })
    
    emotional_depth_score = factory.fuzzy.FuzzyFloat(0.0, 10.0, precision=1)
    
    responses = factory.LazyAttribute(lambda obj: {
        "onboarding_q1": "I value authenticity and deep connection above all else.",
        "onboarding_q2": "My ideal evening involves meaningful conversation over a home-cooked meal.",
        "onboarding_q3": "I feel understood when someone truly listens without judgment.",
        "relationship_goals": fake.random_element(
            elements=("long_term_partnership", "marriage", "companionship", "exploring_connection")
        ),
        "emotional_availability": fake.random_element(
            elements=("fully_available", "somewhat_available", "taking_it_slow")
        )
    })
    
    # Traditional profile fields
    bio = factory.LazyAttribute(lambda obj: fake.paragraph(nb_sentences=2))
    location = factory.LazyAttribute(lambda obj: fake.city())
    created_at = factory.LazyAttribute(lambda obj: fake.date_time_this_year())


class SoulConnectionFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating soul connections between users"""
    
    class Meta:
        model = SoulConnection
        sqlalchemy_session_persistence = "commit"
    
    user1_id = factory.SubFactory(UserFactory)
    user2_id = factory.SubFactory(UserFactory)
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
        RevelationType.HUMOR_SOURCE.value: "Dad jokes and wordplay never fail to make me smile.",
        RevelationType.CHALLENGE_OVERCOME.value: "Learning to trust again after heartbreak made me stronger.",
        RevelationType.IDEAL_CONNECTION.value: "A partner who challenges me to grow while accepting who I am.",
        RevelationType.PHOTO_REVEAL.value: "Ready to share my photo - excited to see the real you!"
    }.get(obj.revelation_type, "A meaningful reflection from my heart to yours."))
    
    created_at = factory.LazyAttribute(lambda obj: fake.date_time_this_week())


class MessageFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating messages between connected users"""
    
    class Meta:
        model = Message
        sqlalchemy_session_persistence = "commit"
    
    connection_id = factory.SubFactory(SoulConnectionFactory)
    sender_id = factory.SubFactory(UserFactory)
    message_text = factory.LazyAttribute(lambda obj: fake.sentence(nb_words=fake.random_int(min=5, max=20)))
    message_type = factory.fuzzy.FuzzyChoice(["text", "revelation", "photo", "emoji_reaction"])
    created_at = factory.LazyAttribute(lambda obj: fake.date_time_this_week())


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
    # Create two users with emotional profiles
    user1 = UserFactory(session=session)
    user2 = UserFactory(session=session)
    
    profile1 = ProfileFactory(user_id=user1.id, session=session)
    profile2 = ProfileFactory(user_id=user2.id, session=session)
    
    # Create soul connection
    connection = SoulConnectionFactory(
        user1_id=user1.id,
        user2_id=user2.id,
        session=session
    )
    
    # Create some revelations
    revelations = []
    for day in range(1, 4):  # First 3 days of revelations
        rev1 = DailyRevelationFactory(
            connection_id=connection.id,
            sender_id=user1.id,
            day_number=day,
            session=session
        )
        rev2 = DailyRevelationFactory(
            connection_id=connection.id,
            sender_id=user2.id,
            day_number=day,
            session=session
        )
        revelations.extend([rev1, rev2])
    
    # Create some messages
    messages = []
    for _ in range(5):
        msg = MessageFactory(
            connection_id=connection.id,
            sender_id=fake.random_element([user1.id, user2.id]),
            session=session
        )
        messages.append(msg)
    
    return {
        'users': [user1, user2],
        'profiles': [profile1, profile2],
        'connection': connection,
        'revelations': revelations,
        'messages': messages
    }