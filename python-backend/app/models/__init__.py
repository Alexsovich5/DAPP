# Import models in the correct order to avoid circular imports
from app.models.user import User
from app.models.profile import Profile
from app.models.match import Match, MatchStatus
from app.models.soul_connection import SoulConnection, ConnectionStage
from app.models.daily_revelation import DailyRevelation, RevelationType
from app.models.message import Message, MessageType

# Make all models available when importing from app.models
__all__ = [
    "User", "Profile", "Match", "MatchStatus",
    "SoulConnection", "ConnectionStage", 
    "DailyRevelation", "RevelationType",
    "Message", "MessageType"
]
