# Import models in the correct order to avoid circular imports
from app.models.user import User, UserEmotionalState
from app.models.profile import Profile
from app.models.match import Match, MatchStatus
from app.models.soul_connection import SoulConnection, ConnectionStage, ConnectionEnergyLevel
from app.models.daily_revelation import DailyRevelation, RevelationType
from app.models.message import Message, MessageType

# Photo reveal models
from app.models.photo_reveal import (
    UserPhoto, PhotoRevealRequest, PhotoRevealPermission, 
    PhotoRevealEvent, PhotoRevealStage, PhotoConsentType, PhotoPrivacyLevel
)

# AI models
from app.models.ai_models import (
    UserProfile, MLModel, CompatibilityPrediction,
    PersonalizedRecommendation, ModelPrediction, BehavioralPattern,
    ModelType, TrainingStatus
)

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

# Make all models available when importing from app.models
__all__ = [
    # Core models
    "User", "UserEmotionalState", "Profile", "Match", "MatchStatus",
    "SoulConnection", "ConnectionStage", "ConnectionEnergyLevel",
    "DailyRevelation", "RevelationType",
    "Message", "MessageType",
    
    # Photo reveal models
    "UserPhoto", "PhotoRevealRequest", "PhotoRevealPermission", 
    "PhotoRevealEvent", "PhotoRevealStage", "PhotoConsentType", "PhotoPrivacyLevel",
    
    # AI models
    "UserProfile", "MLModel", "CompatibilityPrediction",
    "PersonalizedRecommendation", "ModelPrediction", "BehavioralPattern",
    "ModelType", "TrainingStatus",
    
    # Analytics models
    "UserEngagementAnalytics", "SoulConnectionAnalytics", "EmotionalJourneyTracking",
    "SystemPerformanceMetrics", "UserRetentionMetrics", "CompatibilityAccuracyTracking",
    "AnalyticsEventType",
    
    # Real-time models
    "UserPresence", "ConnectionRealTimeState", "LiveTypingSession", 
    "RealtimeNotification", "WebSocketConnection", "AnimationEvent",
    "UserPresenceStatus"
]
