# Import models in the correct order to avoid circular imports
from app.models.user import User, UserEmotionalState
from app.models.profile import Profile
from app.models.match import Match, MatchStatus
from app.models.soul_connection import SoulConnection, ConnectionStage, ConnectionEnergyLevel
from app.models.daily_revelation import DailyRevelation, RevelationType
from app.models.message import Message, MessageType

# Phase 4 Enhanced Models
from app.models.soul_analytics import (
    UserEngagementAnalytics, SoulConnectionAnalytics, EmotionalJourneyTracking,
    SystemPerformanceMetrics, UserRetentionMetrics, CompatibilityAccuracyTracking,
    AnalyticsEventType
)
from app.models.realtime_state import (
    UserPresence, ConnectionRealTimeState, LiveTypingSession,
    RealtimeNotification, WebSocketConnection, AnimationEvent,
    UserPresenceStatus, ConnectionEnergyLevel
)

# Photo reveal models
from app.models.photo_reveal import (
    UserPhoto, PhotoRevealTimeline, PhotoRevealRequest, PhotoRevealPermission,
    PhotoRevealEvent, PhotoModerationLog, PhotoRevealStage, PhotoConsentType,
    PhotoPrivacyLevel, RevealStatus, PhotoReveal
)

# AI and personalization models
from app.models.ai_models import UserProfile
from app.models.personalization_models import UserPersonalizationProfile
from app.models.ui_personalization_models import UserUIProfile

# AB Testing models
from app.models.ab_experiment import ABExperiment, ExperimentVariant, UserExperiment

# Make all models available when importing from app.models
__all__ = [
    # Core models
    "User", "UserEmotionalState", "Profile", "Match", "MatchStatus",
    "SoulConnection", "ConnectionStage", "ConnectionEnergyLevel",
    "DailyRevelation", "RevelationType",
    "Message", "MessageType",
    
    # Analytics models
    "UserEngagementAnalytics", "SoulConnectionAnalytics", "EmotionalJourneyTracking",
    "SystemPerformanceMetrics", "UserRetentionMetrics", "CompatibilityAccuracyTracking",
    "AnalyticsEventType",
    
    # Real-time models
    "UserPresence", "ConnectionRealTimeState", "LiveTypingSession", 
    "RealtimeNotification", "WebSocketConnection", "AnimationEvent",
    "UserPresenceStatus",
    
    # Photo reveal models
    "UserPhoto", "PhotoRevealTimeline", "PhotoRevealRequest", "PhotoRevealPermission",
    "PhotoRevealEvent", "PhotoModerationLog", "PhotoRevealStage", "PhotoConsentType",
    "PhotoPrivacyLevel", "RevealStatus", "PhotoReveal",
    
    # AI and personalization models
    "UserProfile", "UserPersonalizationProfile", "UserUIProfile",
    
    # AB Testing models
    "ABExperiment", "ExperimentVariant", "UserExperiment"
]
