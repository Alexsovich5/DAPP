"""
Sprint 8: Advanced Multi-Modal Sentiment Analysis System
Real-time sentiment analysis with text, emoji, behavioral, and contextual analysis
"""

import asyncio
import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import emoji
import numpy as np

# NLP and ML imports
try:
    import nltk
    from textblob import TextBlob
    from transformers import pipeline

    nltk_available = True
except ImportError:
    nltk_available = False
    logging.warning("NLP libraries not available - using fallback sentiment analysis")

from ..core.event_publisher import EventPublisher
from ..core.redis_manager import RedisClusterManager
from .model_registry import MLModelRegistry

logger = logging.getLogger(__name__)


class SentimentPolarity(Enum):
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class EmotionalState(Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"


@dataclass
class ConversationContext:
    conversation_id: str
    participant_ids: List[str]
    message_history: List[Dict[str, Any]]
    relationship_stage: str  # 'discovery', 'connection', 'intimate'
    conversation_duration_minutes: int
    previous_sentiment_trend: List["SentimentResult"]


@dataclass
class SentimentResult:
    polarity: SentimentPolarity
    confidence: float
    emotional_state: Optional[EmotionalState]
    intensity: float
    text_sentiment: Optional[Dict[str, float]] = None
    emoji_sentiment: Optional[Dict[str, float]] = None
    behavioral_sentiment: Optional[Dict[str, float]] = None
    contextual_factors: Optional[Dict[str, Any]] = None
    processing_time_ms: float = 0.0
    model_version: str = "multi-modal-v1.0"
    timestamp: datetime = None


class MultiModalSentimentAnalyzer:
    """
    Advanced multi-modal sentiment analyzer for Dinner First dating platform
    Combines text analysis, emoji interpretation, behavioral patterns, and conversation context
    """

    def __init__(
        self,
        model_registry: MLModelRegistry,
        redis_manager: RedisClusterManager,
        event_publisher: EventPublisher,
    ):

        self.model_registry = model_registry
        self.redis_manager = redis_manager
        self.event_publisher = event_publisher

        # Model configurations
        self.text_model_name = "roberta-base-sentiment"
        self.sentiment_cache_ttl = 3600  # 1 hour

        # Initialize NLP components
        self._initialize_nlp_components()

        # Sentiment scoring weights
        self.component_weights = {
            "text": 0.5,
            "emoji": 0.2,
            "behavioral": 0.2,
            "contextual": 0.1,
        }

        # Emoji sentiment mappings
        self.emoji_sentiments = self._initialize_emoji_sentiments()

        logger.info("Initialized Multi-Modal Sentiment Analyzer")

    def _initialize_nlp_components(self):
        """Initialize NLP models and components"""
        try:
            # Download required NLTK data
            nltk.download("vader_lexicon", quiet=True)
            nltk.download("punkt", quiet=True)
            nltk.download("stopwords", quiet=True)

            # Initialize transformer-based sentiment pipeline
            self.transformer_sentiment = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True,
            )

            logger.info("NLP components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize NLP components: {e}")
            # Fallback to basic components
            self.transformer_sentiment = None

    def _initialize_emoji_sentiments(self) -> Dict[str, Dict[str, float]]:
        """Initialize emoji sentiment mappings"""
        return {
            # Very positive emojis
            "😍": {"polarity": 0.9, "arousal": 0.8, "emotional_state": "joy"},
            "🥰": {"polarity": 0.85, "arousal": 0.7, "emotional_state": "joy"},
            "😘": {"polarity": 0.8, "arousal": 0.6, "emotional_state": "joy"},
            "💕": {"polarity": 0.85, "arousal": 0.7, "emotional_state": "joy"},
            "❤️": {"polarity": 0.9, "arousal": 0.8, "emotional_state": "joy"},
            # Positive emojis
            "😊": {"polarity": 0.7, "arousal": 0.5, "emotional_state": "joy"},
            "😄": {"polarity": 0.75, "arousal": 0.6, "emotional_state": "joy"},
            "🙂": {"polarity": 0.6, "arousal": 0.3, "emotional_state": "joy"},
            "👍": {"polarity": 0.6, "arousal": 0.4, "emotional_state": "trust"},
            "🎉": {"polarity": 0.8, "arousal": 0.9, "emotional_state": "joy"},
            # Neutral emojis
            "😐": {"polarity": 0.0, "arousal": 0.1, "emotional_state": "neutral"},
            "🤔": {"polarity": 0.1, "arousal": 0.3, "emotional_state": "anticipation"},
            "😌": {"polarity": 0.3, "arousal": 0.2, "emotional_state": "trust"},
            # Negative emojis
            "😔": {"polarity": -0.6, "arousal": 0.3, "emotional_state": "sadness"},
            "😢": {"polarity": -0.7, "arousal": 0.5, "emotional_state": "sadness"},
            "😞": {"polarity": -0.65, "arousal": 0.4, "emotional_state": "sadness"},
            "😕": {"polarity": -0.5, "arousal": 0.3, "emotional_state": "sadness"},
            "👎": {"polarity": -0.6, "arousal": 0.4, "emotional_state": "disgust"},
            # Very negative emojis
            "😡": {"polarity": -0.9, "arousal": 0.9, "emotional_state": "anger"},
            "🤬": {"polarity": -0.95, "arousal": 0.95, "emotional_state": "anger"},
            "😠": {"polarity": -0.8, "arousal": 0.8, "emotional_state": "anger"},
            "💔": {"polarity": -0.85, "arousal": 0.7, "emotional_state": "sadness"},
            # Complex emotions
            "😂": {"polarity": 0.8, "arousal": 0.9, "emotional_state": "joy"},
            "🤣": {"polarity": 0.85, "arousal": 0.95, "emotional_state": "joy"},
            "😅": {"polarity": 0.5, "arousal": 0.6, "emotional_state": "joy"},
            "😬": {"polarity": -0.2, "arousal": 0.6, "emotional_state": "fear"},
            "🙄": {"polarity": -0.4, "arousal": 0.3, "emotional_state": "disgust"},
            "😩": {"polarity": -0.7, "arousal": 0.8, "emotional_state": "sadness"},
        }

    async def analyze_sentiment(
        self,
        text: str,
        user_id: Optional[str] = None,
        conversation_context: Optional[ConversationContext] = None,
        behavioral_data: Optional[Dict[str, Any]] = None,
    ) -> SentimentResult:
        """
        Comprehensive multi-modal sentiment analysis
        """
        start_time = datetime.now()

        try:
            # Check cache first
            if user_id:
                cache_key = f"sentiment:analysis:{user_id}:{hash(text)}"
                cached_result = await self._get_cached_sentiment(cache_key)
                if cached_result:
                    return cached_result

            # Parallel analysis of different modalities
            text_sentiment_task = asyncio.create_task(
                self._analyze_text_sentiment(text)
            )
            emoji_sentiment_task = asyncio.create_task(
                self._analyze_emoji_sentiment(text)
            )
            behavioral_sentiment_task = asyncio.create_task(
                self._analyze_behavioral_sentiment(behavioral_data, user_id)
            )

            # Wait for all analyses to complete
            text_sentiment = await text_sentiment_task
            emoji_sentiment = await emoji_sentiment_task
            behavioral_sentiment = await behavioral_sentiment_task

            # Contextual analysis
            contextual_factors = await self._analyze_contextual_factors(
                text, conversation_context, user_id
            )

            # Combine multi-modal results
            combined_result = await self._combine_sentiment_scores(
                text_sentiment,
                emoji_sentiment,
                behavioral_sentiment,
                contextual_factors,
            )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Create final result
            sentiment_result = SentimentResult(
                polarity=combined_result["polarity"],
                confidence=combined_result["confidence"],
                emotional_state=combined_result.get("emotional_state"),
                intensity=combined_result["intensity"],
                text_sentiment=text_sentiment,
                emoji_sentiment=emoji_sentiment,
                behavioral_sentiment=behavioral_sentiment,
                contextual_factors=contextual_factors,
                processing_time_ms=processing_time,
                model_version="multi-modal-v1.0",
                timestamp=datetime.now(),
            )

            # Cache result
            if user_id:
                await self._cache_sentiment_result(cache_key, sentiment_result)

            # Publish sentiment analysis event
            await self._publish_sentiment_event(sentiment_result, user_id)

            return sentiment_result

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            # Return neutral sentiment as fallback
            return SentimentResult(
                polarity=SentimentPolarity.NEUTRAL,
                confidence=0.1,
                emotional_state=None,
                intensity=0.0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                model_version="fallback-v1.0",
                timestamp=datetime.now(),
            )

    async def _analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment from text using multiple NLP techniques"""
        try:
            results = {}

            # TextBlob analysis (basic but fast)
            blob = TextBlob(text)
            results["textblob_polarity"] = blob.sentiment.polarity
            results["textblob_subjectivity"] = blob.sentiment.subjectivity

            # Transformer-based analysis (more accurate)
            if self.transformer_sentiment:
                scores = self.transformer_sentiment(text)
                for result in scores:
                    if result["label"] == "LABEL_0":  # Negative
                        results["transformer_negative"] = result["score"]
                    elif result["label"] == "LABEL_1":  # Neutral
                        results["transformer_neutral"] = result["score"]
                    elif result["label"] == "LABEL_2":  # Positive
                        results["transformer_positive"] = result["score"]

            # Keyword-based sentiment analysis for dating context
            dating_positive_keywords = [
                "love",
                "amazing",
                "wonderful",
                "beautiful",
                "perfect",
                "incredible",
                "fantastic",
                "excited",
                "happy",
                "joy",
                "thrilled",
                "awesome",
                "gorgeous",
                "stunning",
                "brilliant",
                "excellent",
                "outstanding",
            ]

            dating_negative_keywords = [
                "hate",
                "terrible",
                "awful",
                "horrible",
                "disgusting",
                "boring",
                "disappointed",
                "frustrated",
                "angry",
                "sad",
                "depressed",
                "annoying",
                "stupid",
                "crazy",
                "weird",
                "uncomfortable",
            ]

            text_lower = text.lower()
            positive_count = sum(
                1 for word in dating_positive_keywords if word in text_lower
            )
            negative_count = sum(
                1 for word in dating_negative_keywords if word in text_lower
            )

            total_keywords = positive_count + negative_count
            if total_keywords > 0:
                results["keyword_polarity"] = (
                    positive_count - negative_count
                ) / total_keywords
            else:
                results["keyword_polarity"] = 0.0

            # Message length and complexity factors
            results["message_length"] = len(text)
            results["word_count"] = len(text.split())
            results["exclamation_count"] = text.count("!")
            results["question_count"] = text.count("?")
            results["caps_ratio"] = (
                sum(1 for c in text if c.isupper()) / len(text) if text else 0
            )

            return results

        except Exception as e:
            logger.error(f"Text sentiment analysis failed: {e}")
            return {"error": True, "textblob_polarity": 0.0}

    async def _analyze_emoji_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment from emojis in text"""
        try:
            results = {
                "emoji_count": 0,
                "positive_emoji_count": 0,
                "negative_emoji_count": 0,
                "neutral_emoji_count": 0,
                "total_emoji_polarity": 0.0,
                "emoji_diversity": 0.0,
                "dominant_emotion": None,
            }

            # Extract all emojis
            emoji_list = [char for char in text if char in emoji.EMOJI_DATA]

            if not emoji_list:
                return results

            results["emoji_count"] = len(emoji_list)
            results["emoji_diversity"] = len(set(emoji_list)) / len(emoji_list)

            # Analyze each emoji
            polarity_sum = 0.0
            emotion_counts = Counter()

            for emoji_char in emoji_list:
                if emoji_char in self.emoji_sentiments:
                    emoji_data = self.emoji_sentiments[emoji_char]
                    polarity = emoji_data["polarity"]
                    polarity_sum += polarity

                    if polarity > 0.3:
                        results["positive_emoji_count"] += 1
                    elif polarity < -0.3:
                        results["negative_emoji_count"] += 1
                    else:
                        results["neutral_emoji_count"] += 1

                    emotional_state = emoji_data.get("emotional_state")
                    if emotional_state:
                        emotion_counts[emotional_state] += 1

            if results["emoji_count"] > 0:
                results["total_emoji_polarity"] = polarity_sum / results["emoji_count"]

            # Determine dominant emotion
            if emotion_counts:
                results["dominant_emotion"] = emotion_counts.most_common(1)[0][0]

            return results

        except Exception as e:
            logger.error(f"Emoji sentiment analysis failed: {e}")
            return {"error": True, "emoji_count": 0}

    async def _analyze_behavioral_sentiment(
        self, behavioral_data: Optional[Dict[str, Any]], user_id: Optional[str]
    ) -> Dict[str, float]:
        """Analyze sentiment from behavioral patterns"""
        try:
            results = {
                "response_time_sentiment": 0.0,
                "message_frequency_sentiment": 0.0,
                "engagement_sentiment": 0.0,
                "typing_pattern_sentiment": 0.0,
            }

            if not behavioral_data or not user_id:
                return results

            # Response time analysis (faster responses often indicate
            # interest/excitement)
            response_time = behavioral_data.get("response_time_seconds", 300)
            if response_time <= 30:  # Very quick response
                results["response_time_sentiment"] = 0.3
            elif response_time <= 120:  # Quick response
                results["response_time_sentiment"] = 0.1
            elif response_time <= 600:  # Normal response
                results["response_time_sentiment"] = 0.0
            else:
                results["response_time_sentiment"] = -0.1

            # Message frequency (more messages can indicate engagement)
            messages_last_hour = behavioral_data.get("messages_last_hour", 1)
            if messages_last_hour >= 10:
                results["message_frequency_sentiment"] = 0.2
            elif messages_last_hour >= 5:
                results["message_frequency_sentiment"] = 0.1
            elif messages_last_hour >= 2:
                results["message_frequency_sentiment"] = 0.0
            else:
                results["message_frequency_sentiment"] = -0.05

            # Engagement indicators (reading messages, online status)
            is_online = behavioral_data.get("is_online", False)
            read_receipt_speed = behavioral_data.get("read_receipt_seconds", 600)

            engagement_score = 0.0
            if is_online:
                engagement_score += 0.1
            if read_receipt_speed < 60:  # Read within 1 minute
                engagement_score += 0.1

            results["engagement_sentiment"] = engagement_score

            # Typing patterns (capitals, punctuation, etc.)
            typing_indicators = behavioral_data.get("typing_indicators", {})
            results["typing_pattern_sentiment"] = typing_indicators.get(
                "enthusiasm_score", 0.0
            )

            return results

        except Exception as e:
            logger.error(f"Behavioral sentiment analysis failed: {e}")
            return {"error": True}

    async def _analyze_contextual_factors(
        self,
        text: str,
        conversation_context: Optional[ConversationContext],
        user_id: Optional[str],
    ) -> Dict[str, Any]:
        """Analyze contextual factors that influence sentiment interpretation"""
        try:
            factors = {
                "time_of_day_factor": 0.0,
                "conversation_stage_factor": 0.0,
                "relationship_progression_factor": 0.0,
                "sentiment_trend_factor": 0.0,
                "conversation_length_factor": 0.0,
            }

            current_hour = datetime.now().hour

            # Time of day influence (people are generally more positive during
            # certain hours)
            if 9 <= current_hour <= 11:  # Morning optimism
                factors["time_of_day_factor"] = 0.1
            elif 19 <= current_hour <= 21:  # Evening connection time
                factors["time_of_day_factor"] = 0.15
            elif 22 <= current_hour or current_hour <= 2:  # Late night vulnerability
                factors["time_of_day_factor"] = 0.05
            else:
                factors["time_of_day_factor"] = 0.0

            if conversation_context:
                # Relationship stage influence
                stage_factors = {
                    "discovery": 0.0,  # Neutral baseline
                    "connection": 0.1,  # Slight positive bias
                    "intimate": 0.15,  # More positive interpretation
                }
                factors["conversation_stage_factor"] = stage_factors.get(
                    conversation_context.relationship_stage, 0.0
                )

                # Conversation length factor (longer conversations indicate
                # engagement)
                if conversation_context.conversation_duration_minutes > 120:
                    factors["conversation_length_factor"] = 0.1
                elif conversation_context.conversation_duration_minutes > 60:
                    factors["conversation_length_factor"] = 0.05

                # Previous sentiment trend analysis
                if conversation_context.previous_sentiment_trend:
                    recent_sentiments = conversation_context.previous_sentiment_trend[
                        -5:
                    ]
                    avg_recent_polarity = np.mean(
                        [self._polarity_to_float(s.polarity) for s in recent_sentiments]
                    )
                    factors["sentiment_trend_factor"] = avg_recent_polarity * 0.2

            return factors

        except Exception as e:
            logger.error(f"Contextual analysis failed: {e}")
            return {"error": True}

    async def _combine_sentiment_scores(
        self,
        text_sentiment: Dict[str, float],
        emoji_sentiment: Dict[str, float],
        behavioral_sentiment: Dict[str, float],
        contextual_factors: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Combine all sentiment scores into final result"""
        try:
            # Extract primary text sentiment
            text_polarity = 0.0
            if (
                "transformer_positive" in text_sentiment
                and "transformer_negative" in text_sentiment
            ):
                text_polarity = (
                    text_sentiment["transformer_positive"]
                    - text_sentiment["transformer_negative"]
                )
            elif "textblob_polarity" in text_sentiment:
                text_polarity = text_sentiment["textblob_polarity"]

            # Apply keyword sentiment overlay
            if "keyword_polarity" in text_sentiment:
                text_polarity = (text_polarity * 0.7) + (
                    text_sentiment["keyword_polarity"] * 0.3
                )

            # Extract emoji sentiment
            emoji_polarity = emoji_sentiment.get("total_emoji_polarity", 0.0)

            # Extract behavioral sentiment
            behavioral_polarity = np.mean(
                [
                    behavioral_sentiment.get("response_time_sentiment", 0.0),
                    behavioral_sentiment.get("message_frequency_sentiment", 0.0),
                    behavioral_sentiment.get("engagement_sentiment", 0.0),
                    behavioral_sentiment.get("typing_pattern_sentiment", 0.0),
                ]
            )

            # Extract contextual adjustment
            contextual_adjustment = np.mean(
                [
                    contextual_factors.get("time_of_day_factor", 0.0),
                    contextual_factors.get("conversation_stage_factor", 0.0),
                    contextual_factors.get("relationship_progression_factor", 0.0),
                    contextual_factors.get("sentiment_trend_factor", 0.0),
                    contextual_factors.get("conversation_length_factor", 0.0),
                ]
            )

            # Weighted combination
            combined_polarity = (
                text_polarity * self.component_weights["text"]
                + emoji_polarity * self.component_weights["emoji"]
                + behavioral_polarity * self.component_weights["behavioral"]
                + contextual_adjustment * self.component_weights["contextual"]
            )

            # Determine polarity category
            polarity_category = self._float_to_polarity(combined_polarity)

            # Calculate confidence based on agreement between components
            confidence = self._calculate_confidence(
                text_polarity,
                emoji_polarity,
                behavioral_polarity,
                contextual_adjustment,
            )

            # Calculate intensity (absolute value of combined polarity)
            intensity = min(abs(combined_polarity), 1.0)

            # Determine dominant emotional state
            emotional_state = self._determine_emotional_state(
                combined_polarity, emoji_sentiment, text_sentiment
            )

            return {
                "polarity": polarity_category,
                "confidence": confidence,
                "intensity": intensity,
                "emotional_state": emotional_state,
                "combined_polarity_score": combined_polarity,
            }

        except Exception as e:
            logger.error(f"Score combination failed: {e}")
            return {
                "polarity": SentimentPolarity.NEUTRAL,
                "confidence": 0.1,
                "intensity": 0.0,
                "emotional_state": None,
            }

    def _polarity_to_float(self, polarity: SentimentPolarity) -> float:
        """Convert polarity enum to float value"""
        mapping = {
            SentimentPolarity.VERY_NEGATIVE: -1.0,
            SentimentPolarity.NEGATIVE: -0.5,
            SentimentPolarity.NEUTRAL: 0.0,
            SentimentPolarity.POSITIVE: 0.5,
            SentimentPolarity.VERY_POSITIVE: 1.0,
        }
        return mapping.get(polarity, 0.0)

    def _float_to_polarity(self, score: float) -> SentimentPolarity:
        """Convert float score to polarity enum"""
        if score >= 0.6:
            return SentimentPolarity.VERY_POSITIVE
        elif score >= 0.2:
            return SentimentPolarity.POSITIVE
        elif score > -0.2:
            return SentimentPolarity.NEUTRAL
        elif score > -0.6:
            return SentimentPolarity.NEGATIVE
        else:
            return SentimentPolarity.VERY_NEGATIVE

    def _calculate_confidence(
        self,
        text_pol: float,
        emoji_pol: float,
        behavioral_pol: float,
        contextual_adj: float,
    ) -> float:
        """Calculate confidence based on agreement between different analyses"""
        try:
            scores = [text_pol, emoji_pol, behavioral_pol, contextual_adj]
            non_zero_scores = [s for s in scores if abs(s) > 0.1]

            if len(non_zero_scores) < 2:
                return 0.3  # Low confidence with only one signal

            # Calculate variance (lower variance = higher agreement = higher
            # confidence)
            variance = np.var(non_zero_scores)
            base_confidence = max(0.3, 1.0 - variance)

            # Boost confidence if multiple components agree strongly
            strong_signals = len([s for s in non_zero_scores if abs(s) > 0.5])
            if strong_signals >= 2:
                base_confidence += 0.2

            return min(max(base_confidence, 0.1), 0.95)

        except Exception:
            return 0.5  # Default confidence

    def _determine_emotional_state(
        self,
        combined_polarity: float,
        emoji_sentiment: Dict[str, float],
        text_sentiment: Dict[str, float],
    ) -> Optional[EmotionalState]:
        """Determine primary emotional state from analysis"""
        try:
            # Check dominant emoji emotion first
            dominant_emoji_emotion = emoji_sentiment.get("dominant_emotion")
            if dominant_emoji_emotion:
                try:
                    return EmotionalState(dominant_emoji_emotion)
                except ValueError:
                    pass

            # Fall back to polarity-based emotion mapping
            if combined_polarity >= 0.6:
                return EmotionalState.JOY
            elif combined_polarity >= 0.2:
                return EmotionalState.TRUST
            elif combined_polarity <= -0.6:
                return EmotionalState.SADNESS
            elif combined_polarity <= -0.2:
                return EmotionalState.DISGUST
            else:
                return None  # Neutral emotional state

        except Exception:
            return None

    async def _get_cached_sentiment(self, cache_key: str) -> Optional[SentimentResult]:
        """Retrieve cached sentiment result"""
        try:
            if not self.redis_manager:
                return None

            cached_data = await self.redis_manager.get_value(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # Reconstruct SentimentResult object
                data["polarity"] = SentimentPolarity(data["polarity"])
                if data.get("emotional_state"):
                    data["emotional_state"] = EmotionalState(data["emotional_state"])
                if data.get("timestamp"):
                    data["timestamp"] = datetime.fromisoformat(data["timestamp"])

                return SentimentResult(**data)

            return None

        except Exception as e:
            logger.warning(f"Failed to retrieve cached sentiment: {e}")
            return None

    async def _cache_sentiment_result(self, cache_key: str, result: SentimentResult):
        """Cache sentiment result"""
        try:
            if not self.redis_manager:
                return

            # Convert to serializable format
            data = asdict(result)
            data["polarity"] = result.polarity.value
            if result.emotional_state:
                data["emotional_state"] = result.emotional_state.value
            if result.timestamp:
                data["timestamp"] = result.timestamp.isoformat()

            await self.redis_manager.set_with_expiry(
                cache_key, json.dumps(data), expiry_seconds=self.sentiment_cache_ttl
            )

        except Exception as e:
            logger.warning(f"Failed to cache sentiment result: {e}")

    async def _publish_sentiment_event(
        self, result: SentimentResult, user_id: Optional[str]
    ):
        """Publish sentiment analysis event to message bus"""
        try:
            if not self.event_publisher:
                return

            event_data = {
                "user_id": user_id,
                "sentiment_polarity": result.polarity.value,
                "confidence": result.confidence,
                "intensity": result.intensity,
                "emotional_state": (
                    result.emotional_state.value if result.emotional_state else None
                ),
                "processing_time_ms": result.processing_time_ms,
                "model_version": result.model_version,
                "timestamp": result.timestamp.isoformat() if result.timestamp else None,
            }

            # Determine routing key based on sentiment intensity
            if result.intensity >= 0.7:
                routing_key = "sentiment.analyzed.high_intensity"
            elif result.intensity >= 0.4:
                routing_key = "sentiment.analyzed.medium_intensity"
            else:
                routing_key = "sentiment.analyzed.low_intensity"

            await self.event_publisher.publish_event(
                exchange="sentiment_events", routing_key=routing_key, data=event_data
            )

        except Exception as e:
            logger.warning(f"Failed to publish sentiment event: {e}")

    async def analyze_conversation_sentiment_trend(
        self, conversation_id: str, time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Analyze sentiment trends over a conversation"""
        try:
            # This would typically fetch from a message database
            # For now, return a placeholder structure
            return {
                "conversation_id": conversation_id,
                "time_window_hours": time_window_hours,
                "overall_sentiment_trend": "improving",
                "sentiment_volatility": 0.3,
                "emotional_state_transitions": {
                    "joy": 0.4,
                    "trust": 0.3,
                    "neutral": 0.2,
                    "sadness": 0.1,
                },
                "peak_positive_moment": "2024-01-15T20:30:00Z",
                "peak_negative_moment": "2024-01-15T18:45:00Z",
                "recommendation": "Continue current conversation approach - sentiment trending positively",
            }

        except Exception as e:
            logger.error(f"Conversation sentiment trend analysis failed: {e}")
            return {}


# Utility functions for sentiment analysis


def create_conversation_context(
    conversation_id: str,
    participant_ids: List[str],
    message_history: List[Dict[str, Any]] = None,
) -> ConversationContext:
    """Create conversation context for sentiment analysis"""
    return ConversationContext(
        conversation_id=conversation_id,
        participant_ids=participant_ids,
        message_history=message_history or [],
        relationship_stage="discovery",  # Default stage
        conversation_duration_minutes=0,
        previous_sentiment_trend=[],
    )
