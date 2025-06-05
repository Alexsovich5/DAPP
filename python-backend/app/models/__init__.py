# Import models in the correct order to avoid circular imports
from app.models.user import User
from app.models.profile import Profile
from app.models.match import Match, MatchStatus

# Make all models available when importing from app.models
__all__ = ["User", "Profile", "Match", "MatchStatus"]
