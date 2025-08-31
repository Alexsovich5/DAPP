# Import models in the correct order to avoid circular imports
# A/B Testing models
from app.models.ab_testing import (
    Experiment,
    ExperimentEvent,
    ExperimentResults,
    ExperimentStatus,
    ExperimentVariant,
    MetricType,
    UserAssignment,
    VariantType,
)

# Personalization models (before user model to avoid circular imports)
# AI models
from app.models.ai_models import (
    BehavioralPattern,
    CompatibilityPrediction,
    MLModel,
    ModelPrediction,
    ModelType,
    PersonalizedRecommendation,
    TrainingStatus,
    UserProfile,
)
from app.models.daily_revelation import DailyRevelation, RevelationType
from app.models.match import Match, MatchStatus
from app.models.message import Message, MessageType
from app.models.personalization_models import (
    AlgorithmOptimization,
    ContentFeedback,
    ContentType,
    ConversationFlowAnalytics,
    PersonalizationStrategy,
    PersonalizedContent,
    UserPersonalizationProfile,
)

# Photo reveal models
from app.models.photo_reveal import (
    PhotoConsentType,
    PhotoPrivacyLevel,
    PhotoRevealEvent,
    PhotoRevealPermission,
    PhotoRevealRequest,
    PhotoRevealStage,
    UserPhoto,
)
from app.models.profile import Profile
from app.models.realtime_state import (
    AnimationEvent,
    ConnectionEnergyLevel,
    ConnectionRealTimeState,
    LiveTypingSession,
    RealtimeNotification,
    UserPresence,
    UserPresenceStatus,
    WebSocketConnection,
)

# Phase 4 Enhanced Models
from app.models.soul_analytics import (
    AnalyticsEventType,
    CompatibilityAccuracyTracking,
    EmotionalJourneyTracking,
    SoulConnectionAnalytics,
    SystemPerformanceMetrics,
    UserEngagementAnalytics,
    UserRetentionMetrics,
)
from app.models.soul_connection import (
    ConnectionStage,
    SoulConnection,
)
from app.models.ui_personalization_models import UserUIProfile
from app.models.user import User, UserEmotionalState

# Make all models available when importing from app.models
__all__ = [
    # Core models
    "User",
    "UserEmotionalState",
    # A/B Testing models
    "Experiment",
    "ExperimentVariant",
    "UserAssignment",
    "ExperimentEvent",
    "ExperimentResults",
    "ExperimentStatus",
    "VariantType",
    "MetricType",
    # Personalization models
    "UserPersonalizationProfile",
    "PersonalizedContent",
    "ContentFeedback",
    "AlgorithmOptimization",
    "ConversationFlowAnalytics",
    "PersonalizationStrategy",
    "ContentType",
    "UserUIProfile",
    "Profile",
    "Match",
    "MatchStatus",
    "SoulConnection",
    "ConnectionStage",
    "ConnectionEnergyLevel",
    "DailyRevelation",
    "RevelationType",
    "Message",
    "MessageType",
    # Photo reveal models
    "UserPhoto",
    "PhotoRevealRequest",
    "PhotoRevealPermission",
    "PhotoRevealEvent",
    "PhotoRevealStage",
    "PhotoConsentType",
    "PhotoPrivacyLevel",
    # AI models
    "UserProfile",
    "MLModel",
    "CompatibilityPrediction",
    "PersonalizedRecommendation",
    "ModelPrediction",
    "BehavioralPattern",
    "ModelType",
    "TrainingStatus",
    # Analytics models
    "UserEngagementAnalytics",
    "SoulConnectionAnalytics",
    "EmotionalJourneyTracking",
    "SystemPerformanceMetrics",
    "UserRetentionMetrics",
    "CompatibilityAccuracyTracking",
    "AnalyticsEventType",
    # Real-time models
    "UserPresence",
    "ConnectionRealTimeState",
    "LiveTypingSession",
    "RealtimeNotification",
    "WebSocketConnection",
    "AnimationEvent",
    "UserPresenceStatus",
]
