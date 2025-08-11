"""
Phase 7: Enhanced Real-Time Communication Service
Advanced messaging system with voice notes, video calls, and intelligent features
"""
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import base64
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.enhanced_communication_models import (
    EnhancedMessage, VoiceMessage, VideoCallSession, SmartReply,
    MessageReaction, ConversationInsight, CommunicationPattern,
    EmotionalTone, MessageType, CallStatus, ReactionType
)
from app.services.personalization_service import personalization_engine
from app.services.ai_matching_service import ai_matching_engine

logger = logging.getLogger(__name__)


class EnhancedCommunicationEngine:
    """
    Advanced real-time communication system with AI-powered features
    Integrates voice, video, smart replies, and emotional intelligence
    """
    
    def __init__(self):
        self.voice_analysis_enabled = True
        self.smart_reply_cache = {}
        self.conversation_patterns = {}
        
        # Communication enhancement settings
        self.enhancement_settings = {
            "voice_emotion_analysis": True,
            "smart_reply_generation": True,
            "conversation_flow_optimization": True,
            "real_time_translation": False,  # Future feature
            "typing_indicator_intelligence": True,
            "message_sentiment_analysis": True
        }

    async def send_enhanced_message(
        self,
        sender_id: int,
        connection_id: int,
        message_content: str,
        message_type: str = "text",
        attachment_data: Optional[Dict[str, Any]] = None,
        emotional_context: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Send enhanced message with AI analysis and smart features"""
        try:
            # Get connection and validate
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError("Connection not found")
            
            # Analyze message content
            message_analysis = await self._analyze_message_content(
                message_content, sender_id, connection_id, db
            )
            
            # Create enhanced message
            enhanced_message = EnhancedMessage(
                sender_id=sender_id,
                connection_id=connection_id,
                message_type=MessageType(message_type),
                content_text=message_content,
                attachment_data=attachment_data,
                emotional_tone=message_analysis.get("emotional_tone"),
                sentiment_score=message_analysis.get("sentiment_score"),
                personalization_applied=message_analysis.get("personalizations"),
                ai_insights=message_analysis.get("insights"),
                conversation_context=emotional_context or {}
            )
            
            db.add(enhanced_message)
            db.commit()
            db.refresh(enhanced_message)
            
            # Generate smart reply suggestions for recipient
            smart_replies = await self._generate_smart_replies(
                enhanced_message, connection, db
            )
            
            # Update conversation patterns
            await self._update_conversation_patterns(
                sender_id, connection_id, message_analysis, db
            )
            
            return {
                "message_id": enhanced_message.id,
                "message": enhanced_message,
                "smart_replies": smart_replies,
                "conversation_insights": message_analysis.get("conversation_insights", {}),
                "delivery_status": "sent",
                "timestamp": enhanced_message.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending enhanced message: {str(e)}")
            raise

    async def process_voice_message(
        self,
        sender_id: int,
        connection_id: int,
        audio_data: bytes,
        duration: float,
        db: Session = None
    ) -> Dict[str, Any]:
        """Process voice message with emotion analysis and transcription"""
        try:
            # Create voice message record
            voice_message = VoiceMessage(
                sender_id=sender_id,
                connection_id=connection_id,
                audio_file_path=f"voice_messages/{sender_id}_{connection_id}_{datetime.utcnow().timestamp()}.wav",
                duration_seconds=duration,
                file_size_bytes=len(audio_data)
            )
            
            # Analyze voice for emotional content (placeholder for real ML)
            voice_analysis = await self._analyze_voice_emotion(audio_data, duration)
            
            voice_message.emotional_tone = voice_analysis.get("primary_emotion", "neutral")
            voice_message.confidence_score = voice_analysis.get("confidence", 0.7)
            voice_message.transcription = voice_analysis.get("transcription", "")
            voice_message.emotional_metadata = voice_analysis.get("metadata", {})
            
            db.add(voice_message)
            db.commit()
            db.refresh(voice_message)
            
            # Create corresponding enhanced message
            enhanced_message = await self.send_enhanced_message(
                sender_id=sender_id,
                connection_id=connection_id,
                message_content=voice_message.transcription or "[Voice Message]",
                message_type="voice",
                attachment_data={"voice_message_id": voice_message.id},
                emotional_context=voice_analysis,
                db=db
            )
            
            return {
                "voice_message_id": voice_message.id,
                "enhanced_message": enhanced_message,
                "emotional_analysis": voice_analysis,
                "transcription": voice_message.transcription
            }
            
        except Exception as e:
            logger.error(f"Error processing voice message: {str(e)}")
            raise

    async def initiate_video_call(
        self,
        initiator_id: int,
        connection_id: int,
        call_type: str = "revelation_reveal",
        db: Session = None
    ) -> Dict[str, Any]:
        """Initiate video call session with intelligent scheduling"""
        try:
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError("Connection not found")
            
            # Check if users are ready for video calls (Day 7 check)
            readiness_check = await self._check_video_call_readiness(
                connection, call_type, db
            )
            
            if not readiness_check["ready"]:
                return {
                    "success": False,
                    "reason": readiness_check["reason"],
                    "suggestions": readiness_check["suggestions"]
                }
            
            # Create video call session
            video_session = VideoCallSession(
                connection_id=connection_id,
                initiator_id=initiator_id,
                call_type=call_type,
                status=CallStatus.INITIATED,
                scheduled_time=datetime.utcnow() + timedelta(minutes=5),  # 5-min buffer
                call_metadata={
                    "revelation_day": connection.reveal_day or 7,
                    "compatibility_score": float(connection.compatibility_score or 0),
                    "readiness_factors": readiness_check["factors"]
                }
            )
            
            db.add(video_session)
            db.commit()
            db.refresh(video_session)
            
            # Generate call preparation insights
            call_insights = await self._generate_call_preparation_insights(
                connection, initiator_id, db
            )
            
            return {
                "success": True,
                "call_session_id": video_session.id,
                "call_token": self._generate_call_token(video_session.id),
                "preparation_insights": call_insights,
                "estimated_start_time": video_session.scheduled_time.isoformat(),
                "call_guidelines": self._get_call_guidelines(call_type)
            }
            
        except Exception as e:
            logger.error(f"Error initiating video call: {str(e)}")
            raise

    async def generate_conversation_insights(
        self,
        connection_id: int,
        user_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Generate intelligent conversation insights and suggestions"""
        try:
            # Get recent conversation history
            recent_messages = db.query(EnhancedMessage).filter(
                and_(
                    EnhancedMessage.connection_id == connection_id,
                    EnhancedMessage.created_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).order_by(EnhancedMessage.created_at.desc()).limit(50).all()
            
            if not recent_messages:
                return {"insights": [], "suggestions": []}
            
            # Analyze conversation patterns
            conversation_analysis = await self._analyze_conversation_flow(
                recent_messages, user_id, db
            )
            
            # Generate insights
            insights = {
                "communication_style_match": conversation_analysis.get("style_compatibility", 0.7),
                "emotional_synchrony": conversation_analysis.get("emotional_alignment", 0.6),
                "conversation_depth_progression": conversation_analysis.get("depth_progression", {}),
                "engagement_patterns": conversation_analysis.get("engagement_metrics", {}),
                "topic_affinity_analysis": conversation_analysis.get("topic_analysis", {}),
                "conversation_momentum": conversation_analysis.get("momentum_score", 0.5)
            }
            
            # Generate actionable suggestions
            suggestions = await self._generate_conversation_suggestions(
                conversation_analysis, connection_id, user_id, db
            )
            
            # Store insights for future reference
            conversation_insight = ConversationInsight(
                connection_id=connection_id,
                user_id=user_id,
                insight_type="comprehensive_analysis",
                insights_data=insights,
                suggestions=suggestions,
                confidence_score=conversation_analysis.get("analysis_confidence", 0.7)
            )
            
            db.add(conversation_insight)
            db.commit()
            
            return {
                "insights": insights,
                "suggestions": suggestions,
                "analysis_confidence": conversation_analysis.get("analysis_confidence", 0.7),
                "next_recommended_action": suggestions[0] if suggestions else None
            }
            
        except Exception as e:
            logger.error(f"Error generating conversation insights: {str(e)}")
            return {"insights": [], "suggestions": []}

    async def _analyze_message_content(
        self,
        content: str,
        sender_id: int,
        connection_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze message content for emotional tone and personalization opportunities"""
        
        # Sentiment analysis (placeholder for real NLP)
        sentiment_score = self._calculate_sentiment_score(content)
        
        # Emotional tone detection
        emotional_tone = self._detect_emotional_tone(content, sentiment_score)
        
        # Personalization opportunities
        personalizations = await self._identify_personalization_opportunities(
            content, sender_id, connection_id, db
        )
        
        # Conversation insights
        conversation_insights = await self._generate_message_insights(
            content, sender_id, connection_id, db
        )
        
        return {
            "sentiment_score": sentiment_score,
            "emotional_tone": emotional_tone,
            "personalizations": personalizations,
            "insights": conversation_insights,
            "conversation_insights": {
                "message_depth": self._calculate_message_depth(content),
                "vulnerability_level": self._assess_vulnerability_level(content),
                "connection_building_potential": self._assess_connection_potential(content)
            }
        }

    async def _generate_smart_replies(
        self,
        message: EnhancedMessage,
        connection: SoulConnection,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Generate intelligent reply suggestions based on message context"""
        
        # Get recipient's communication patterns
        recipient_id = connection.user2_id if message.sender_id == connection.user1_id else connection.user1_id
        recipient_patterns = await self._get_communication_patterns(recipient_id, db)
        
        # Generate context-aware replies
        smart_replies = []
        
        # Emotional response suggestions
        if message.emotional_tone in ["excited", "joyful"]:
            smart_replies.append({
                "text": "That's wonderful! Tell me more about that 😊",
                "type": "emotional_support",
                "confidence": 0.8
            })
        elif message.emotional_tone in ["contemplative", "vulnerable"]:
            smart_replies.append({
                "text": "I really appreciate you sharing that with me",
                "type": "validation",
                "confidence": 0.9
            })
        
        # Question-based replies
        if "?" not in message.content_text:
            smart_replies.append({
                "text": "What made you think about that?",
                "type": "curiosity",
                "confidence": 0.7
            })
        
        # Personalized responses based on recipient style
        if recipient_patterns.get("preferred_style") == "playful":
            smart_replies.append({
                "text": "Haha, that's so you! 😄",
                "type": "playful_response",
                "confidence": 0.6
            })
        
        # Limit to top 3 suggestions
        return sorted(smart_replies, key=lambda x: x["confidence"], reverse=True)[:3]

    async def _analyze_voice_emotion(self, audio_data: bytes, duration: float) -> Dict[str, Any]:
        """Analyze voice message for emotional content (placeholder for real ML)"""
        
        # This would integrate with actual voice emotion analysis ML models
        # For now, return mock analysis based on duration and basic patterns
        
        emotions = ["happy", "excited", "contemplative", "nervous", "confident", "romantic"]
        primary_emotion = emotions[len(audio_data) % len(emotions)]  # Mock selection
        
        confidence = min(0.9, 0.5 + (duration / 60))  # Longer messages = higher confidence
        
        return {
            "primary_emotion": primary_emotion,
            "confidence": confidence,
            "transcription": "[Voice message transcription would be here]",
            "metadata": {
                "voice_characteristics": {
                    "pace": "moderate",
                    "tone_variation": "normal",
                    "clarity": "good"
                },
                "emotional_indicators": {
                    "warmth": 0.7,
                    "authenticity": 0.8,
                    "engagement": 0.6
                }
            }
        }

    async def _check_video_call_readiness(
        self,
        connection: SoulConnection,
        call_type: str,
        db: Session
    ) -> Dict[str, Any]:
        """Check if users are ready for video call based on revelation progress"""
        
        current_day = connection.reveal_day or 1
        required_day = 7 if call_type == "revelation_reveal" else 5
        
        if current_day < required_day:
            return {
                "ready": False,
                "reason": f"Video calls available on day {required_day}. Currently on day {current_day}.",
                "suggestions": [
                    "Continue your daily revelations to unlock video calling",
                    "Share more about yourself to build deeper connection"
                ]
            }
        
        # Check mutual consent for photo/video reveal
        if not connection.mutual_reveal_consent:
            return {
                "ready": False,
                "reason": "Both users must consent to photo/video reveal",
                "suggestions": [
                    "Discuss video calling comfort levels with your match",
                    "Complete revelation cycle to build trust"
                ]
            }
        
        return {
            "ready": True,
            "factors": {
                "revelation_progress": current_day,
                "mutual_consent": True,
                "compatibility_score": float(connection.compatibility_score or 0)
            }
        }

    def _calculate_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score for text (placeholder for real NLP)"""
        positive_words = ["happy", "love", "amazing", "wonderful", "excited", "great"]
        negative_words = ["sad", "hate", "terrible", "awful", "angry", "disappointed"]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Scale from -1 (negative) to 1 (positive)
        total_words = len(words)
        if total_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_words

    def _detect_emotional_tone(self, text: str, sentiment: float) -> str:
        """Detect emotional tone from text content"""
        text_lower = text.lower()
        
        if sentiment > 0.3:
            if any(word in text_lower for word in ["excited", "amazing", "incredible"]):
                return "excited"
            return "positive"
        elif sentiment < -0.3:
            if any(word in text_lower for word in ["nervous", "worried", "anxious"]):
                return "nervous"
            return "negative"
        else:
            if any(word in text_lower for word in ["think", "wonder", "consider"]):
                return "contemplative"
            return "neutral"

    # Additional helper methods would continue here...
    async def _identify_personalization_opportunities(
        self, content: str, sender_id: int, connection_id: int, db: Session
    ) -> Dict[str, Any]:
        """Identify personalization opportunities in messages"""
        return {"opportunities": [], "applied": []}

    async def _generate_message_insights(
        self, content: str, sender_id: int, connection_id: int, db: Session
    ) -> Dict[str, Any]:
        """Generate insights about the message"""
        return {"depth": 0.5, "engagement_potential": 0.7}

    def _calculate_message_depth(self, content: str) -> float:
        """Calculate emotional/intellectual depth of message"""
        depth_indicators = ["feel", "believe", "experience", "remember", "dream", "hope"]
        words = content.lower().split()
        depth_score = sum(1 for word in words if word in depth_indicators) / max(len(words), 1)
        return min(depth_score * 2, 1.0)

    def _assess_vulnerability_level(self, content: str) -> float:
        """Assess vulnerability level in message"""
        vulnerability_words = ["afraid", "scared", "worried", "share", "personal", "secret"]
        words = content.lower().split()
        vulnerability_score = sum(1 for word in words if word in vulnerability_words) / max(len(words), 1)
        return min(vulnerability_score * 3, 1.0)

    def _assess_connection_potential(self, content: str) -> float:
        """Assess connection-building potential of message"""
        connection_words = ["we", "us", "together", "both", "similar", "understand"]
        words = content.lower().split()
        connection_score = sum(1 for word in words if word in connection_words) / max(len(words), 1)
        return min(connection_score * 2, 1.0)

    async def _update_conversation_patterns(
        self, sender_id: int, connection_id: int, message_analysis: Dict, db: Session
    ) -> None:
        """Update conversation patterns for users"""
        pass  # Implementation would store patterns for ML learning

    async def _get_communication_patterns(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user's communication patterns"""
        return {"preferred_style": "balanced", "response_time": "medium"}

    async def _analyze_conversation_flow(
        self, messages: List[EnhancedMessage], user_id: int, db: Session
    ) -> Dict[str, Any]:
        """Analyze conversation flow and patterns"""
        return {
            "style_compatibility": 0.7,
            "emotional_alignment": 0.6,
            "analysis_confidence": 0.8
        }

    async def _generate_conversation_suggestions(
        self, analysis: Dict, connection_id: int, user_id: int, db: Session
    ) -> List[str]:
        """Generate actionable conversation suggestions"""
        return [
            "Ask about their favorite childhood memory",
            "Share something you're looking forward to",
            "Discuss a value that's important to you"
        ]

    async def _generate_call_preparation_insights(
        self, connection: SoulConnection, initiator_id: int, db: Session
    ) -> Dict[str, Any]:
        """Generate insights to help prepare for video call"""
        return {
            "conversation_starters": [
                "What has surprised you most about our conversations so far?",
                "What are you most excited to discover when we meet?"
            ],
            "connection_highlights": [
                "You both love meaningful conversations",
                "You share similar values about relationships"
            ]
        }

    def _generate_call_token(self, session_id: int) -> str:
        """Generate secure token for video call"""
        data = f"{session_id}_{datetime.utcnow().timestamp()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _get_call_guidelines(self, call_type: str) -> List[str]:
        """Get guidelines for different types of calls"""
        guidelines = {
            "revelation_reveal": [
                "This is your first face-to-face moment - take it slow",
                "Focus on the emotional connection you've built",
                "Remember: you're already compatible souls"
            ],
            "casual_chat": [
                "Relax and be yourself",
                "Build on your previous conversations",
                "Enjoy getting to know each other better"
            ]
        }
        return guidelines.get(call_type, ["Be authentic and enjoy the moment"])


# Initialize the global enhanced communication engine
enhanced_communication_engine = EnhancedCommunicationEngine()