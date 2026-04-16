"""
Multi-Modal Sentiment Analysis System for Sprint 8 - Advanced Microservices Architecture
Real-time sentiment analysis with behavioral, temporal, and contextual intelligence
"""

import re
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import structlog
from app.ai.ml_model_registry import MLModelRegistry
from app.core.event_publisher import EventPublisher, EventType

# Import our Redis cluster manager and event publisher
from app.core.redis_cluster_manager import DatabaseType, RedisClusterManager
from prometheus_client import Counter, Gauge, Histogram
from textblob import TextBlob
from transformers import pipeline

logger = structlog.get_logger(__name__)

# Prometheus metrics
SENTIMENT_REQUESTS = Counter(
    "sentiment_analysis_requests_total",
    "Total sentiment analysis requests",
    ["analysis_type", "status"],
)
SENTIMENT_DURATION = Histogram(
    "sentiment_analysis_duration_seconds", "Sentiment analysis processing time"
)
EMOTION_DETECTIONS = Counter(
    "emotion_detections_total", "Total emotion detections", ["emotion_type"]
)
MOOD_CHANGES = Counter(
    "mood_changes_total",
    "Total mood changes detected",
    ["from_mood", "to_mood"],
)
SENTIMENT_ACCURACY = Gauge(
    "sentiment_analysis_accuracy",
    "Sentiment analysis accuracy",
    ["model_version"],
)


class EmotionalState(Enum):
    """Emotional states for classification"""

    EXCITED = "excited"
    HAPPY = "happy"
    CONTENT = "content"
    NEUTRAL = "neutral"
    MELANCHOLY = "melancholy"
    ANXIOUS = "anxious"
    STRESSED = "stressed"
    FRUSTRATED = "frustrated"
    LONELY = "lonely"
    OPTIMISTIC = "optimistic"
    ROMANTIC = "romantic"
    PLAYFUL = "playful"


class SentimentIntensity(Enum):
    """Sentiment intensity levels"""

    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    SLIGHTLY_NEGATIVE = "slightly_negative"
    NEUTRAL = "neutral"
    SLIGHTLY_POSITIVE = "slightly_positive"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class AnalysisModality(Enum):
    """Different modalities for sentiment analysis"""

    TEXT = "text"
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    CONTEXTUAL = "contextual"
    INTERACTION = "interaction"


class SentimentResult:
    """Comprehensive sentiment analysis result"""

    def __init__(self):
        self.overall_sentiment_score: float = 0.0  # -1.0 to 1.0
        self.confidence: float = 0.0  # 0.0 to 1.0
        self.emotional_state: EmotionalState = EmotionalState.NEUTRAL
        self.sentiment_intensity: SentimentIntensity = SentimentIntensity.NEUTRAL

        # Component scores
        self.text_sentiment: Optional[Dict[str, Any]] = None
        self.behavioral_sentiment: Optional[Dict[str, Any]] = None
        self.temporal_sentiment: Optional[Dict[str, Any]] = None
        self.contextual_sentiment: Optional[Dict[str, Any]] = None

        # Detected emotions
        self.emotions: List[str] = []
        self.emotion_scores: Dict[str, float] = {}

        # Metadata
        self.analysis_timestamp: datetime = datetime.utcnow()
        self.analysis_id: str = str(uuid.uuid4())
        self.modalities_used: List[AnalysisModality] = []

        # Context
        self.user_context: Optional[Dict[str, Any]] = None
        self.conversation_context: Optional[Dict[str, Any]] = None

        # Personalization insights
        self.personality_traits: Dict[str, float] = {}
        self.communication_style: Dict[str, float] = {}
        self.relationship_compatibility_indicators: Dict[str, float] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "analysis_id": self.analysis_id,
            "overall_sentiment_score": round(self.overall_sentiment_score, 3),
            "confidence": round(self.confidence, 3),
            "emotional_state": self.emotional_state.value,
            "sentiment_intensity": self.sentiment_intensity.value,
            "component_scores": {
                "text_sentiment": self.text_sentiment,
                "behavioral_sentiment": self.behavioral_sentiment,
                "temporal_sentiment": self.temporal_sentiment,
                "contextual_sentiment": self.contextual_sentiment,
            },
            "emotions": self.emotions,
            "emotion_scores": {k: round(v, 3) for k, v in self.emotion_scores.items()},
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "modalities_used": [m.value for m in self.modalities_used],
            "user_context": self.user_context,
            "conversation_context": self.conversation_context,
            "personality_traits": {
                k: round(v, 3) for k, v in self.personality_traits.items()
            },
            "communication_style": {
                k: round(v, 3) for k, v in self.communication_style.items()
            },
            "relationship_compatibility_indicators": {
                k: round(v, 3)
                for k, v in self.relationship_compatibility_indicators.items()
            },
        }


class BERTSentimentAnalyzer:
    """BERT-based text sentiment analyzer"""

    def __init__(self):
        self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.tokenizer = None
        self.model = None
        self.pipeline = None

        # Initialize lazily to avoid startup delays
        self._initialized = False

    async def initialize(self):
        """Initialize BERT model and tokenizer"""
        if self._initialized:
            return

        try:
            # Load pre-trained sentiment analysis pipeline
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                tokenizer=self.model_name,
                device=-1,  # Use CPU for now, can be changed to GPU
            )

            self._initialized = True
            logger.info("BERT sentiment analyzer initialized")

        except Exception as e:
            logger.error(f"Failed to initialize BERT analyzer: {e}")
            # Fallback to TextBlob
            self.pipeline = None

    async def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text sentiment using BERT"""
        if not self._initialized:
            await self.initialize()

        try:
            if self.pipeline:
                # Use BERT pipeline
                result = self.pipeline(text[:512])  # Truncate to max length

                # Map BERT labels to our scale
                label = result[0]["label"].lower()
                score = result[0]["score"]

                if label == "positive":
                    sentiment_score = score
                elif label == "negative":
                    sentiment_score = -score
                else:  # neutral
                    sentiment_score = 0.0

            else:
                # Fallback to TextBlob
                blob = TextBlob(text)
                sentiment_score = blob.sentiment.polarity
                score = abs(sentiment_score)

            # Extract additional features
            features = await self._extract_text_features(text)

            return {
                "sentiment_score": sentiment_score,
                "confidence": score,
                "features": features,
                "model_used": "bert" if self.pipeline else "textblob",
            }

        except Exception as e:
            logger.error(f"Text sentiment analysis failed: {e}")
            return {
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "features": {},
                "error": str(e),
            }

    async def _extract_text_features(self, text: str) -> Dict[str, Any]:
        """Extract additional text features for sentiment analysis"""
        features = {}

        # Basic text statistics
        features["word_count"] = len(text.split())
        features["char_count"] = len(text)
        features["sentence_count"] = len(re.split(r"[.!?]+", text))

        # Emotional indicators
        positive_words = [
            "love",
            "amazing",
            "wonderful",
            "excited",
            "happy",
            "joy",
            "fantastic",
        ]
        negative_words = [
            "hate",
            "terrible",
            "awful",
            "sad",
            "angry",
            "frustrated",
            "disappointed",
        ]

        text_lower = text.lower()
        features["positive_word_count"] = sum(
            1 for word in positive_words if word in text_lower
        )
        features["negative_word_count"] = sum(
            1 for word in negative_words if word in text_lower
        )

        # Punctuation analysis
        features["exclamation_count"] = text.count("!")
        features["question_count"] = text.count("?")
        features["emoji_count"] = len(re.findall(r"[😀-🙏]", text))

        # Communication style indicators
        features["uses_all_caps"] = any(
            word.isupper() and len(word) > 2 for word in text.split()
        )
        features["uses_ellipsis"] = "..." in text
        features["formal_language"] = any(
            word in text_lower for word in ["furthermore", "however", "therefore"]
        )
        features["casual_language"] = any(
            word in text_lower for word in ["lol", "haha", "awesome", "cool"]
        )

        return features


class BehavioralSentimentAnalyzer:
    """Behavioral sentiment inference from user actions"""

    def __init__(self, redis_manager: RedisClusterManager):
        self.redis_manager = redis_manager

    async def infer_sentiment(self, behavioral_data: Dict[str, Any]) -> Dict[str, Any]:
        """Infer sentiment from behavioral patterns"""
        try:
            sentiment_score = 0.0
            confidence = 0.0

            # Session activity patterns
            if "session_duration" in behavioral_data:
                # Longer sessions might indicate engagement (positive)
                duration_score = min(
                    behavioral_data["session_duration"] / 1800, 1.0
                )  # Normalize to 30 min
                sentiment_score += duration_score * 0.3

            # Interaction patterns
            if "swipe_velocity" in behavioral_data:
                # Very fast swiping might indicate frustration (negative)
                # Very slow might indicate careful consideration (positive)
                velocity = behavioral_data["swipe_velocity"]
                if velocity > 10:  # Too fast
                    sentiment_score -= 0.2
                elif velocity < 3:  # Thoughtful
                    sentiment_score += 0.2

            # Response patterns
            if "response_rate" in behavioral_data:
                # Higher response rate indicates engagement
                response_rate = behavioral_data["response_rate"]
                sentiment_score += response_rate * 0.4

            # Feature usage diversity
            if "feature_usage_diversity" in behavioral_data:
                # Using more features indicates positive engagement
                diversity = behavioral_data["feature_usage_diversity"]
                sentiment_score += diversity * 0.3

            # Photo upload behavior
            if "photo_uploads" in behavioral_data:
                uploads = behavioral_data["photo_uploads"]
                if uploads > 0:
                    sentiment_score += 0.2  # Sharing photos is positive

            # Time spent on profiles
            if "avg_profile_view_time" in behavioral_data:
                view_time = behavioral_data["avg_profile_view_time"]
                if view_time > 60:  # More than 1 minute
                    sentiment_score += 0.3

            # Normalize sentiment score
            sentiment_score = max(-1.0, min(1.0, sentiment_score))

            # Calculate confidence based on data richness
            data_points = len([k for k, v in behavioral_data.items() if v is not None])
            confidence = min(
                data_points / 10.0, 1.0
            )  # Max confidence with 10+ data points

            return {
                "sentiment_score": sentiment_score,
                "confidence": confidence,
                "behavioral_indicators": self._categorize_behavior(behavioral_data),
                "engagement_level": self._calculate_engagement_level(behavioral_data),
            }

        except Exception as e:
            logger.error(f"Behavioral sentiment analysis failed: {e}")
            return {"sentiment_score": 0.0, "confidence": 0.0, "error": str(e)}

    def _categorize_behavior(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Categorize behavioral patterns"""
        categories = {}

        # Engagement level
        if data.get("session_duration", 0) > 1800:  # 30 minutes
            categories["engagement"] = "high"
        elif data.get("session_duration", 0) > 600:  # 10 minutes
            categories["engagement"] = "medium"
        else:
            categories["engagement"] = "low"

        # Decision making style
        if data.get("swipe_velocity", 5) > 10:
            categories["decision_style"] = "impulsive"
        elif data.get("swipe_velocity", 5) < 3:
            categories["decision_style"] = "deliberate"
        else:
            categories["decision_style"] = "balanced"

        # Social openness
        if data.get("response_rate", 0) > 0.8:
            categories["social_openness"] = "very_open"
        elif data.get("response_rate", 0) > 0.5:
            categories["social_openness"] = "open"
        else:
            categories["social_openness"] = "selective"

        return categories

    def _calculate_engagement_level(self, data: Dict[str, Any]) -> float:
        """Calculate overall engagement level"""
        engagement_score = 0.0

        # Session duration
        if "session_duration" in data:
            engagement_score += min(data["session_duration"] / 3600, 1.0) * 0.3

        # Feature usage
        if "feature_usage_diversity" in data:
            engagement_score += data["feature_usage_diversity"] * 0.3

        # Response activity
        if "response_rate" in data:
            engagement_score += data["response_rate"] * 0.4

        return min(engagement_score, 1.0)


class TemporalSentimentAnalyzer:
    """Temporal sentiment pattern analysis"""

    def __init__(self, redis_manager: RedisClusterManager):
        self.redis_manager = redis_manager

    async def analyze_patterns(
        self, user_id: int, time_window: str = "24h"
    ) -> Dict[str, Any]:
        """Analyze temporal sentiment patterns"""
        try:
            # Get historical sentiment data
            historical_data = await self._get_historical_sentiment(user_id, time_window)

            if not historical_data:
                return {
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "trend": "stable",
                }

            # Analyze trends
            trend_analysis = await self._analyze_sentiment_trend(historical_data)

            # Time-of-day patterns
            time_patterns = await self._analyze_time_patterns(historical_data)

            # Activity rhythm analysis
            rhythm_analysis = await self._analyze_activity_rhythm(historical_data)

            return {
                "sentiment_score": trend_analysis["current_sentiment"],
                "confidence": trend_analysis["trend_confidence"],
                "trend": trend_analysis["trend_direction"],
                "time_patterns": time_patterns,
                "activity_rhythm": rhythm_analysis,
                "historical_average": trend_analysis["historical_average"],
            }

        except Exception as e:
            logger.error(f"Temporal sentiment analysis failed: {e}")
            return {"sentiment_score": 0.0, "confidence": 0.0, "error": str(e)}

    async def _get_historical_sentiment(
        self, user_id: int, time_window: str
    ) -> List[Dict[str, Any]]:
        """Get historical sentiment data for user"""
        # This would query actual historical data from Redis or database
        # For now, return mock data
        return [
            {
                "timestamp": datetime.utcnow() - timedelta(hours=i),
                "sentiment": 0.1 * i,
            }
            for i in range(24)
        ]

    async def _analyze_sentiment_trend(
        self, data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze sentiment trend from historical data"""
        if len(data) < 2:
            return {
                "current_sentiment": 0.0,
                "trend_direction": "stable",
                "trend_confidence": 0.0,
                "historical_average": 0.0,
            }

        # Sort by timestamp
        sorted_data = sorted(data, key=lambda x: x["timestamp"])

        # Calculate trend
        sentiments = [d["sentiment"] for d in sorted_data]
        current_sentiment = sentiments[-1]
        historical_average = np.mean(sentiments)

        # Simple trend calculation
        if len(sentiments) >= 3:
            recent_trend = np.mean(sentiments[-3:]) - np.mean(sentiments[:-3])
            if recent_trend > 0.1:
                trend = "improving"
            elif recent_trend < -0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "current_sentiment": current_sentiment,
            "trend_direction": trend,
            "trend_confidence": min(len(sentiments) / 10.0, 1.0),
            "historical_average": historical_average,
        }

    async def _analyze_time_patterns(
        self, data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze time-of-day sentiment patterns"""
        hour_sentiments = {}

        for record in data:
            hour = record["timestamp"].hour
            if hour not in hour_sentiments:
                hour_sentiments[hour] = []
            hour_sentiments[hour].append(record["sentiment"])

        # Calculate average sentiment by hour
        hour_averages = {
            hour: np.mean(sentiments) for hour, sentiments in hour_sentiments.items()
        }

        # Find peak and low hours
        if hour_averages:
            peak_hour = max(hour_averages.keys(), key=lambda k: hour_averages[k])
            low_hour = min(hour_averages.keys(), key=lambda k: hour_averages[k])
        else:
            peak_hour = 12
            low_hour = 6

        return {
            "hour_averages": hour_averages,
            "peak_sentiment_hour": peak_hour,
            "low_sentiment_hour": low_hour,
            "sentiment_variation": (
                max(hour_averages.values()) - min(hour_averages.values())
                if hour_averages
                else 0
            ),
        }

    async def _analyze_activity_rhythm(
        self, data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze activity rhythm patterns"""
        # Simple analysis of activity patterns
        activity_hours = [record["timestamp"].hour for record in data]

        if activity_hours:
            most_active_hour = max(set(activity_hours), key=activity_hours.count)
            activity_span = max(activity_hours) - min(activity_hours)

            return {
                "most_active_hour": most_active_hour,
                "activity_span_hours": activity_span,
                "total_activities": len(data),
                "rhythm_consistency": 1.0
                - (len(set(activity_hours)) / 24.0),  # 0-1, higher = more consistent
            }

        return {
            "most_active_hour": 12,
            "activity_span_hours": 0,
            "total_activities": 0,
            "rhythm_consistency": 0.0,
        }


class ContextualSentimentAnalyzer:
    """Contextual sentiment analysis considering external factors"""

    def __init__(self):
        pass

    async def analyze_context(
        self, user_id: int, current_time: datetime
    ) -> Dict[str, Any]:
        """Analyze contextual factors affecting sentiment"""
        try:
            context_factors = {}

            # Time of day context
            hour = current_time.hour
            if 6 <= hour < 12:
                time_context = "morning"
                expected_sentiment = 0.1  # Slightly positive
            elif 12 <= hour < 18:
                time_context = "afternoon"
                expected_sentiment = 0.2  # More positive
            elif 18 <= hour < 22:
                time_context = "evening"
                expected_sentiment = 0.3  # Peak positive
            else:
                time_context = "night"
                expected_sentiment = -0.1  # Slightly negative (tired)

            context_factors["time_of_day"] = {
                "context": time_context,
                "expected_sentiment": expected_sentiment,
            }

            # Day of week context
            day_of_week = current_time.weekday()  # 0 = Monday
            if day_of_week < 4:  # Monday - Thursday
                day_context = "weekday"
                work_stress_factor = -0.1
            elif day_of_week == 4:  # Friday
                day_context = "friday"
                work_stress_factor = 0.1  # TGIF effect
            else:  # Weekend
                day_context = "weekend"
                work_stress_factor = 0.2  # Relaxed

            context_factors["day_of_week"] = {
                "context": day_context,
                "work_stress_factor": work_stress_factor,
            }

            # Seasonal context (simplified)
            month = current_time.month
            if month in [12, 1, 2]:
                season = "winter"
                seasonal_effect = -0.05  # Winter blues
            elif month in [3, 4, 5]:
                season = "spring"
                seasonal_effect = 0.15  # Spring optimism
            elif month in [6, 7, 8]:
                season = "summer"
                seasonal_effect = 0.1  # Summer positivity
            else:
                season = "fall"
                seasonal_effect = 0.0  # Neutral

            context_factors["season"] = {
                "season": season,
                "seasonal_effect": seasonal_effect,
            }

            # Calculate overall contextual sentiment
            contextual_sentiment = (
                expected_sentiment + work_stress_factor + seasonal_effect
            )

            # Confidence based on predictability of context
            confidence = 0.6  # Moderate confidence for contextual factors

            return {
                "sentiment_score": contextual_sentiment,
                "confidence": confidence,
                "context_factors": context_factors,
                "dominant_context": time_context,
            }

        except Exception as e:
            logger.error(f"Contextual sentiment analysis failed: {e}")
            return {"sentiment_score": 0.0, "confidence": 0.0, "error": str(e)}


class MultiModalSentimentAnalyzer:
    """
    Main multi-modal sentiment analyzer that combines all analysis types
    """

    def __init__(
        self,
        redis_manager: RedisClusterManager,
        event_publisher: EventPublisher,
        model_registry: MLModelRegistry,
    ):

        self.redis_manager = redis_manager
        self.event_publisher = event_publisher
        self.model_registry = model_registry

        # Initialize component analyzers
        self.text_analyzer = BERTSentimentAnalyzer()
        self.behavioral_analyzer = BehavioralSentimentAnalyzer(redis_manager)
        self.temporal_analyzer = TemporalSentimentAnalyzer(redis_manager)
        self.contextual_analyzer = ContextualSentimentAnalyzer()

        # Fusion weights for combining different modalities
        self.fusion_weights = {
            AnalysisModality.TEXT: 0.4,
            AnalysisModality.BEHAVIORAL: 0.3,
            AnalysisModality.TEMPORAL: 0.2,
            AnalysisModality.CONTEXTUAL: 0.1,
        }

        logger.info("Multi-modal sentiment analyzer initialized")

    async def initialize(self):
        """Initialize all component analyzers"""
        await self.text_analyzer.initialize()
        logger.info("All sentiment analyzers initialized")

    async def analyze_comprehensive_sentiment(
        self,
        user_id: int,
        data: Dict[str, Any],
        modalities: Optional[List[AnalysisModality]] = None,
    ) -> SentimentResult:
        """
        Perform comprehensive sentiment analysis across all modalities

        Args:
            user_id: User ID for personalized analysis
            data: Input data containing message, behavior data, etc.
            modalities: Specific modalities to use (all if None)

        Returns:
            Comprehensive sentiment analysis result
        """
        start_time = time.time()

        try:
            result = SentimentResult()
            result.user_context = {"user_id": user_id}

            if modalities is None:
                modalities = list(AnalysisModality)

            result.modalities_used = modalities

            # Text sentiment analysis
            if AnalysisModality.TEXT in modalities and "message_text" in data:
                with SENTIMENT_DURATION.time():
                    text_sentiment = await self.text_analyzer.analyze(
                        data["message_text"]
                    )
                    result.text_sentiment = text_sentiment
                    SENTIMENT_REQUESTS.labels(
                        analysis_type="text", status="success"
                    ).inc()

            # Behavioral sentiment analysis
            if AnalysisModality.BEHAVIORAL in modalities:
                behavioral_data = await self._get_user_behavioral_data(user_id)
                behavioral_sentiment = await self.behavioral_analyzer.infer_sentiment(
                    behavioral_data
                )
                result.behavioral_sentiment = behavioral_sentiment
                SENTIMENT_REQUESTS.labels(
                    analysis_type="behavioral", status="success"
                ).inc()

            # Temporal sentiment analysis
            if AnalysisModality.TEMPORAL in modalities:
                temporal_sentiment = await self.temporal_analyzer.analyze_patterns(
                    user_id, "24h"
                )
                result.temporal_sentiment = temporal_sentiment
                SENTIMENT_REQUESTS.labels(
                    analysis_type="temporal", status="success"
                ).inc()

            # Contextual sentiment analysis
            if AnalysisModality.CONTEXTUAL in modalities:
                contextual_sentiment = await self.contextual_analyzer.analyze_context(
                    user_id, datetime.utcnow()
                )
                result.contextual_sentiment = contextual_sentiment
                SENTIMENT_REQUESTS.labels(
                    analysis_type="contextual", status="success"
                ).inc()

            # Fuse all sentiment signals
            result = await self._fuse_sentiment_signals(result)

            # Extract emotions and personality insights
            await self._extract_emotions_and_traits(result)

            # Cache the result
            await self._cache_sentiment_result(user_id, result)

            # Publish sentiment analysis event
            await self.event_publisher.publish_sentiment_event(
                EventType.SENTIMENT_ANALYZED,
                {
                    "user_id": user_id,
                    "analysis_id": result.analysis_id,
                    "sentiment_score": result.overall_sentiment_score,
                    "emotional_state": result.emotional_state.value,
                    "confidence": result.confidence,
                    "modalities_used": [m.value for m in result.modalities_used],
                    "timestamp": result.analysis_timestamp.isoformat(),
                },
            )

            # Update metrics
            processing_time = time.time() - start_time
            SENTIMENT_DURATION.observe(processing_time)

            logger.info(
                f"Sentiment analysis completed for user {user_id}: {result.overall_sentiment_score:.3f}"
            )

            return result

        except Exception as e:
            SENTIMENT_REQUESTS.labels(
                analysis_type="comprehensive", status="error"
            ).inc()
            logger.error(
                f"Comprehensive sentiment analysis failed for user {user_id}: {e}"
            )

            # Return neutral result on error
            result = SentimentResult()
            result.user_context = {"user_id": user_id, "error": str(e)}
            return result

    async def _fuse_sentiment_signals(self, result: SentimentResult) -> SentimentResult:
        """Fuse sentiment signals from different modalities"""
        try:
            weighted_sentiment = 0.0
            total_weight = 0.0
            confidence_scores = []

            # Text sentiment
            if result.text_sentiment:
                weight = self.fusion_weights[AnalysisModality.TEXT]
                sentiment = result.text_sentiment["sentiment_score"]
                confidence = result.text_sentiment["confidence"]

                weighted_sentiment += sentiment * weight * confidence
                total_weight += weight * confidence
                confidence_scores.append(confidence)

            # Behavioral sentiment
            if result.behavioral_sentiment:
                weight = self.fusion_weights[AnalysisModality.BEHAVIORAL]
                sentiment = result.behavioral_sentiment["sentiment_score"]
                confidence = result.behavioral_sentiment["confidence"]

                weighted_sentiment += sentiment * weight * confidence
                total_weight += weight * confidence
                confidence_scores.append(confidence)

            # Temporal sentiment
            if result.temporal_sentiment:
                weight = self.fusion_weights[AnalysisModality.TEMPORAL]
                sentiment = result.temporal_sentiment["sentiment_score"]
                confidence = result.temporal_sentiment["confidence"]

                weighted_sentiment += sentiment * weight * confidence
                total_weight += weight * confidence
                confidence_scores.append(confidence)

            # Contextual sentiment
            if result.contextual_sentiment:
                weight = self.fusion_weights[AnalysisModality.CONTEXTUAL]
                sentiment = result.contextual_sentiment["sentiment_score"]
                confidence = result.contextual_sentiment["confidence"]

                weighted_sentiment += sentiment * weight * confidence
                total_weight += weight * confidence
                confidence_scores.append(confidence)

            # Calculate final sentiment and confidence
            if total_weight > 0:
                result.overall_sentiment_score = weighted_sentiment / total_weight
            else:
                result.overall_sentiment_score = 0.0

            if confidence_scores:
                result.confidence = np.mean(confidence_scores)
            else:
                result.confidence = 0.0

            # Determine emotional state
            result.emotional_state = self._classify_emotional_state(
                result.overall_sentiment_score, result
            )

            # Determine sentiment intensity
            result.sentiment_intensity = self._classify_sentiment_intensity(
                result.overall_sentiment_score
            )

            return result

        except Exception as e:
            logger.error(f"Sentiment fusion failed: {e}")
            return result

    def _classify_emotional_state(
        self, sentiment_score: float, result: SentimentResult
    ) -> EmotionalState:
        """Classify emotional state based on sentiment score and context"""

        # Consider behavioral patterns for more nuanced classification
        if result.behavioral_sentiment:
            engagement = result.behavioral_sentiment.get("engagement_level", 0.5)

            if sentiment_score > 0.6:
                if engagement > 0.8:
                    return EmotionalState.EXCITED
                else:
                    return EmotionalState.CONTENT
            elif sentiment_score > 0.3:
                return EmotionalState.HAPPY
            elif sentiment_score > 0.1:
                return EmotionalState.OPTIMISTIC
            elif sentiment_score > -0.1:
                return EmotionalState.NEUTRAL
            elif sentiment_score > -0.3:
                if engagement < 0.3:
                    return EmotionalState.MELANCHOLY
                else:
                    return EmotionalState.ANXIOUS
            else:
                return EmotionalState.FRUSTRATED

        # Simple classification based on sentiment score
        if sentiment_score > 0.5:
            return EmotionalState.EXCITED
        elif sentiment_score > 0.2:
            return EmotionalState.HAPPY
        elif sentiment_score > 0.05:
            return EmotionalState.CONTENT
        elif sentiment_score > -0.05:
            return EmotionalState.NEUTRAL
        elif sentiment_score > -0.2:
            return EmotionalState.MELANCHOLY
        else:
            return EmotionalState.FRUSTRATED

    def _classify_sentiment_intensity(
        self, sentiment_score: float
    ) -> SentimentIntensity:
        """Classify sentiment intensity"""
        if sentiment_score > 0.7:
            return SentimentIntensity.VERY_POSITIVE
        elif sentiment_score > 0.3:
            return SentimentIntensity.POSITIVE
        elif sentiment_score > 0.1:
            return SentimentIntensity.SLIGHTLY_POSITIVE
        elif sentiment_score > -0.1:
            return SentimentIntensity.NEUTRAL
        elif sentiment_score > -0.3:
            return SentimentIntensity.SLIGHTLY_NEGATIVE
        elif sentiment_score > -0.7:
            return SentimentIntensity.NEGATIVE
        else:
            return SentimentIntensity.VERY_NEGATIVE

    async def _extract_emotions_and_traits(self, result: SentimentResult):
        """Extract specific emotions and personality traits"""
        try:
            # Extract emotions from text analysis
            if result.text_sentiment and "features" in result.text_sentiment:
                features = result.text_sentiment["features"]

                # Detect specific emotions based on text features
                if features.get("positive_word_count", 0) > 0:
                    result.emotions.append("joy")
                    result.emotion_scores["joy"] = min(
                        features["positive_word_count"] / 3.0, 1.0
                    )

                if features.get("exclamation_count", 0) > 2:
                    result.emotions.append("excitement")
                    result.emotion_scores["excitement"] = min(
                        features["exclamation_count"] / 5.0, 1.0
                    )

                if features.get("negative_word_count", 0) > 0:
                    result.emotions.append("sadness")
                    result.emotion_scores["sadness"] = min(
                        features["negative_word_count"] / 3.0, 1.0
                    )

            # Extract personality traits from behavioral data
            if result.behavioral_sentiment:
                behavioral_indicators = result.behavioral_sentiment.get(
                    "behavioral_indicators", {}
                )

                # Extraversion
                if behavioral_indicators.get("social_openness") == "very_open":
                    result.personality_traits["extraversion"] = 0.8
                elif behavioral_indicators.get("social_openness") == "open":
                    result.personality_traits["extraversion"] = 0.6
                else:
                    result.personality_traits["extraversion"] = 0.3

                # Conscientiousness
                if behavioral_indicators.get("decision_style") == "deliberate":
                    result.personality_traits["conscientiousness"] = 0.8
                elif behavioral_indicators.get("decision_style") == "balanced":
                    result.personality_traits["conscientiousness"] = 0.6
                else:
                    result.personality_traits["conscientiousness"] = 0.3

                # Openness to experience
                engagement = result.behavioral_sentiment.get("engagement_level", 0.5)
                result.personality_traits["openness"] = engagement

            # Communication style analysis
            if result.text_sentiment and "features" in result.text_sentiment:
                features = result.text_sentiment["features"]

                # Formality
                if features.get("formal_language"):
                    result.communication_style["formality"] = 0.8
                elif features.get("casual_language"):
                    result.communication_style["formality"] = 0.2
                else:
                    result.communication_style["formality"] = 0.5

                # Expressiveness
                expressiveness = (
                    features.get("emoji_count", 0) * 0.2
                    + features.get("exclamation_count", 0) * 0.1
                )
                result.communication_style["expressiveness"] = min(expressiveness, 1.0)

            # Relationship compatibility indicators
            result.relationship_compatibility_indicators = {
                "emotional_expressiveness": result.communication_style.get(
                    "expressiveness", 0.5
                ),
                "social_engagement": result.personality_traits.get("extraversion", 0.5),
                "emotional_stability": 1.0
                - abs(result.overall_sentiment_score),  # More stable = less extreme
                "communication_clarity": result.confidence,
            }

        except Exception as e:
            logger.error(f"Failed to extract emotions and traits: {e}")

    async def _get_user_behavioral_data(self, user_id: int) -> Dict[str, Any]:
        """Get user behavioral data for analysis"""
        try:
            # This would fetch real behavioral data from Redis or database
            # For now, return mock data
            return {
                "session_duration": 1800,  # 30 minutes
                "swipe_velocity": 5,  # swipes per minute
                "response_rate": 0.7,  # 70% response rate
                "feature_usage_diversity": 0.8,  # Uses 80% of features
                "photo_uploads": 3,
                "avg_profile_view_time": 90,  # seconds
            }
        except Exception as e:
            logger.error(f"Failed to get behavioral data for user {user_id}: {e}")
            return {}

    async def _cache_sentiment_result(self, user_id: int, result: SentimentResult):
        """Cache sentiment analysis result"""
        try:
            # Cache recent sentiment for temporal analysis
            await self.redis_manager.cache_sentiment_analysis(
                user_id,
                int(time.time()),  # Use timestamp as message_id
                result.to_dict(),
            )

            # Update user's current sentiment profile
            sentiment_profile_key = f"user_sentiment_profile:{user_id}"
            profile = (
                await self.redis_manager.get(
                    DatabaseType.SENTIMENT_CACHE, sentiment_profile_key
                )
                or {}
            )

            profile.update(
                {
                    "current_sentiment": result.overall_sentiment_score,
                    "emotional_state": result.emotional_state.value,
                    "last_analysis": result.analysis_timestamp.isoformat(),
                    "personality_traits": result.personality_traits,
                    "communication_style": result.communication_style,
                    "analysis_count": profile.get("analysis_count", 0) + 1,
                }
            )

            await self.redis_manager.set_with_ttl(
                DatabaseType.SENTIMENT_CACHE,
                sentiment_profile_key,
                profile,
                ttl=86400,  # 24 hours
            )

        except Exception as e:
            logger.error(f"Failed to cache sentiment result: {e}")

    async def get_user_sentiment_profile(
        self, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get user's current sentiment profile"""
        try:
            sentiment_profile_key = f"user_sentiment_profile:{user_id}"
            profile = await self.redis_manager.get(
                DatabaseType.SENTIMENT_CACHE, sentiment_profile_key
            )
            return profile
        except Exception as e:
            logger.error(f"Failed to get sentiment profile for user {user_id}: {e}")
            return None

    async def detect_mood_change(
        self, user_id: int, new_sentiment: float, threshold: float = 0.3
    ) -> Optional[Dict[str, Any]]:
        """Detect significant mood changes"""
        try:
            profile = await self.get_user_sentiment_profile(user_id)
            if not profile:
                return None

            previous_sentiment = profile.get("current_sentiment", 0.0)
            sentiment_change = new_sentiment - previous_sentiment

            if abs(sentiment_change) >= threshold:
                mood_change = {
                    "user_id": user_id,
                    "previous_sentiment": previous_sentiment,
                    "new_sentiment": new_sentiment,
                    "change_magnitude": sentiment_change,
                    "change_direction": (
                        "positive" if sentiment_change > 0 else "negative"
                    ),
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Update metrics
                previous_mood = (
                    "positive"
                    if previous_sentiment > 0
                    else "negative" if previous_sentiment < 0 else "neutral"
                )
                new_mood = (
                    "positive"
                    if new_sentiment > 0
                    else "negative" if new_sentiment < 0 else "neutral"
                )
                MOOD_CHANGES.labels(from_mood=previous_mood, to_mood=new_mood).inc()

                # Publish mood change event
                await self.event_publisher.publish_sentiment_event(
                    EventType.MOOD_CHANGED, mood_change
                )

                return mood_change

            return None

        except Exception as e:
            logger.error(f"Failed to detect mood change for user {user_id}: {e}")
            return None


# Global sentiment analyzer instance
sentiment_analyzer: Optional[MultiModalSentimentAnalyzer] = None


def get_sentiment_analyzer() -> MultiModalSentimentAnalyzer:
    """Get global sentiment analyzer instance"""
    if sentiment_analyzer is None:
        raise Exception(
            "Sentiment analyzer not initialized. Call init_sentiment_analyzer first."
        )
    return sentiment_analyzer


async def init_sentiment_analyzer(
    redis_manager: RedisClusterManager,
    event_publisher: EventPublisher,
    model_registry: MLModelRegistry,
) -> MultiModalSentimentAnalyzer:
    """Initialize global sentiment analyzer"""
    global sentiment_analyzer
    sentiment_analyzer = MultiModalSentimentAnalyzer(
        redis_manager, event_publisher, model_registry
    )
    await sentiment_analyzer.initialize()
    logger.info("Sentiment analyzer initialized globally")
    return sentiment_analyzer
