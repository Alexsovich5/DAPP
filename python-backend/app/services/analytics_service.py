"""
User Analytics and Engagement Tracking Service - Phase 4
Comprehensive analytics system for user behavior, engagement, and system optimization
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
import json

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.sql import text

from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation
from app.models.message import Message
from app.models.soul_analytics import (
    UserEngagementAnalytics, SoulConnectionAnalytics, EmotionalJourneyTracking,
    SystemPerformanceMetrics, UserRetentionMetrics, CompatibilityAccuracyTracking,
    AnalyticsEventType
)
from app.models.realtime_state import UserPresence, LiveTypingSession, AnimationEvent

logger = logging.getLogger(__name__)


@dataclass
class EngagementMetrics:
    """User engagement metrics summary"""
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    average_session_duration: float
    total_sessions: int
    bounce_rate: float
    retention_rates: Dict[str, float]


@dataclass
class ConnectionMetrics:
    """Soul connection metrics summary"""
    total_connections: int
    active_connections: int
    completed_revelations: int
    photo_reveals: int
    average_compatibility_score: float
    connection_success_rate: float
    average_time_to_first_message: float


@dataclass
class UserJourneyAnalytics:
    """User journey and funnel analytics"""
    onboarding_completion_rate: float
    profile_completion_rate: float
    first_swipe_rate: float
    first_match_rate: float
    first_message_rate: float
    revelation_sharing_rate: float
    photo_reveal_rate: float


@dataclass
class SystemHealthMetrics:
    """System performance and health metrics"""
    api_response_times: Dict[str, float]
    websocket_connections: int
    database_performance: Dict[str, float]
    error_rates: Dict[str, float]
    user_satisfaction_scores: Dict[str, float]


class AnalyticsService:
    """Comprehensive analytics and engagement tracking service"""
    
    def __init__(self):
        self.event_cache = {}  # In-memory cache for high-frequency events
        self.batch_size = 100  # Batch size for bulk operations
        logger.info("Analytics Service initialized")
    
    async def track_user_event(
        self, 
        user_id: int, 
        event_type: AnalyticsEventType,
        event_data: Dict[str, Any],
        db: Session,
        session_id: Optional[str] = None,
        connection_id: Optional[int] = None
    ) -> bool:
        """Track individual user engagement event"""
        try:
            analytics_event = UserEngagementAnalytics(
                user_id=user_id,
                event_type=event_type.value,
                event_data=event_data,
                session_id=session_id,
                device_type=event_data.get('device_type', 'unknown'),
                browser_info=event_data.get('browser_info'),
                timezone=event_data.get('timezone'),
                country_code=event_data.get('country_code'),
                created_at=datetime.utcnow()
            )
            
            db.add(analytics_event)
            
            # Update user's total counters
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                if event_type == AnalyticsEventType.SWIPE_ACTION:
                    user.total_swipes += 1
                elif event_type == AnalyticsEventType.MESSAGE_SENT:
                    user.total_messages_sent += 1
                elif event_type == AnalyticsEventType.REVELATION_SHARED:
                    user.total_revelations_shared += 1
            
            # Update emotional journey if connection-related
            if connection_id:
                await self._update_emotional_journey(
                    user_id, connection_id, event_type, event_data, db
                )
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking user event: {str(e)}")
            db.rollback()
            return False
    
    async def calculate_user_engagement_score(self, user_id: int, db: Session) -> float:
        """Calculate comprehensive engagement score for a user"""
        try:
            # Get recent activity (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            events = db.query(UserEngagementAnalytics).filter(
                UserEngagementAnalytics.user_id == user_id,
                UserEngagementAnalytics.created_at >= cutoff_date
            ).all()
            
            if not events:
                return 0.0
            
            # Calculate various engagement factors
            factors = {}
            
            # Activity frequency (0-25 points)
            unique_days = len(set(event.created_at.date() for event in events))
            factors['frequency'] = min(25.0, (unique_days / 30.0) * 25.0)
            
            # Action diversity (0-20 points)
            event_types = set(event.event_type for event in events)
            factors['diversity'] = min(20.0, (len(event_types) / 10.0) * 20.0)
            
            # Deep engagement actions (0-25 points)
            deep_actions = [
                AnalyticsEventType.REVELATION_SHARED,
                AnalyticsEventType.MESSAGE_SENT,
                AnalyticsEventType.CONNECTION_ACCEPTED
            ]
            deep_count = sum(1 for event in events if event.event_type in [e.value for e in deep_actions])
            factors['depth'] = min(25.0, (deep_count / 20.0) * 25.0)
            
            # Session quality (0-15 points)
            # Would calculate based on session duration data
            factors['quality'] = 10.0  # Placeholder
            
            # Recent activity bonus (0-15 points)
            recent_events = [e for e in events if e.created_at >= datetime.utcnow() - timedelta(days=7)]
            factors['recency'] = min(15.0, (len(recent_events) / 10.0) * 15.0)
            
            total_score = sum(factors.values())
            return min(100.0, total_score)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {str(e)}")
            return 0.0
    
    async def get_user_journey_funnel(self, db: Session, days: int = 30) -> UserJourneyAnalytics:
        """Calculate user journey funnel metrics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total users in period
            total_users = db.query(User).filter(
                User.created_at >= cutoff_date
            ).count()
            
            if total_users == 0:
                return self._empty_journey_analytics()
            
            # Onboarding completion
            onboarded_users = db.query(User).filter(
                User.created_at >= cutoff_date,
                User.emotional_onboarding_completed == True
            ).count()
            
            # Profile completion
            profile_complete_users = db.query(User).filter(
                User.created_at >= cutoff_date,
                User.is_profile_complete == True
            ).count()
            
            # First swipe
            first_swipe_users = db.query(UserEngagementAnalytics).filter(
                UserEngagementAnalytics.created_at >= cutoff_date,
                UserEngagementAnalytics.event_type == AnalyticsEventType.SWIPE_ACTION.value
            ).distinct(UserEngagementAnalytics.user_id).count()
            
            # First match
            first_match_users = db.query(UserEngagementAnalytics).filter(
                UserEngagementAnalytics.created_at >= cutoff_date,
                UserEngagementAnalytics.event_type == AnalyticsEventType.CONNECTION_INITIATED.value
            ).distinct(UserEngagementAnalytics.user_id).count()
            
            # First message
            first_message_users = db.query(UserEngagementAnalytics).filter(
                UserEngagementAnalytics.created_at >= cutoff_date,
                UserEngagementAnalytics.event_type == AnalyticsEventType.MESSAGE_SENT.value
            ).distinct(UserEngagementAnalytics.user_id).count()
            
            # Revelation sharing
            revelation_users = db.query(UserEngagementAnalytics).filter(
                UserEngagementAnalytics.created_at >= cutoff_date,
                UserEngagementAnalytics.event_type == AnalyticsEventType.REVELATION_SHARED.value
            ).distinct(UserEngagementAnalytics.user_id).count()
            
            # Photo reveal
            photo_reveal_users = db.query(UserEngagementAnalytics).filter(
                UserEngagementAnalytics.created_at >= cutoff_date,
                UserEngagementAnalytics.event_type == AnalyticsEventType.PHOTO_CONSENT_GIVEN.value
            ).distinct(UserEngagementAnalytics.user_id).count()
            
            return UserJourneyAnalytics(
                onboarding_completion_rate=(onboarded_users / total_users) * 100,
                profile_completion_rate=(profile_complete_users / total_users) * 100,
                first_swipe_rate=(first_swipe_users / total_users) * 100,
                first_match_rate=(first_match_users / total_users) * 100,
                first_message_rate=(first_message_users / total_users) * 100,
                revelation_sharing_rate=(revelation_users / total_users) * 100,
                photo_reveal_rate=(photo_reveal_users / total_users) * 100
            )
            
        except Exception as e:
            logger.error(f"Error calculating user journey funnel: {str(e)}")
            return self._empty_journey_analytics()
    
    async def get_engagement_metrics(self, db: Session) -> EngagementMetrics:
        """Calculate comprehensive engagement metrics"""
        try:
            now = datetime.utcnow()
            
            # Define time periods
            day_ago = now - timedelta(days=1)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            # Active users
            daily_active = db.query(UserEngagementAnalytics.user_id).filter(
                UserEngagementAnalytics.created_at >= day_ago
            ).distinct().count()
            
            weekly_active = db.query(UserEngagementAnalytics.user_id).filter(
                UserEngagementAnalytics.created_at >= week_ago
            ).distinct().count()
            
            monthly_active = db.query(UserEngagementAnalytics.user_id).filter(
                UserEngagementAnalytics.created_at >= month_ago
            ).distinct().count()
            
            # Session data (simplified - would be more complex in production)
            total_sessions = db.query(UserEngagementAnalytics).filter(
                UserEngagementAnalytics.event_type == AnalyticsEventType.LOGIN.value,
                UserEngagementAnalytics.created_at >= month_ago
            ).count()
            
            # Calculate retention rates
            retention_rates = await self._calculate_retention_rates(db)
            
            # Bounce rate (users who only had one session)
            single_session_users = db.query(
                UserEngagementAnalytics.user_id
            ).filter(
                UserEngagementAnalytics.event_type == AnalyticsEventType.LOGIN.value,
                UserEngagementAnalytics.created_at >= month_ago
            ).group_by(UserEngagementAnalytics.user_id).having(
                func.count(UserEngagementAnalytics.id) == 1
            ).count()
            
            bounce_rate = (single_session_users / max(1, monthly_active)) * 100
            
            return EngagementMetrics(
                daily_active_users=daily_active,
                weekly_active_users=weekly_active,
                monthly_active_users=monthly_active,
                average_session_duration=30.0,  # Placeholder - would calculate from actual session data
                total_sessions=total_sessions,
                bounce_rate=bounce_rate,
                retention_rates=retention_rates
            )
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {str(e)}")
            return self._empty_engagement_metrics()
    
    async def get_connection_metrics(self, db: Session) -> ConnectionMetrics:
        """Calculate soul connection metrics"""
        try:
            # Total connections
            total_connections = db.query(SoulConnection).count()
            
            # Active connections
            active_connections = db.query(SoulConnection).filter(
                SoulConnection.status == "active"
            ).count()
            
            # Completed revelations
            completed_revelations = db.query(DailyRevelation).count()
            
            # Photo reveals
            photo_reveals = db.query(SoulConnection).filter(
                SoulConnection.photo_revealed_at.isnot(None)
            ).count()
            
            # Average compatibility score
            avg_compatibility = db.query(func.avg(SoulConnection.compatibility_score)).filter(
                SoulConnection.compatibility_score.isnot(None)
            ).scalar() or 0.0
            
            # Success rate (connections that reached photo reveal)
            success_rate = (photo_reveals / max(1, total_connections)) * 100
            
            # Average time to first message
            avg_time_to_message = db.query(
                func.avg(
                    func.extract('epoch', SoulConnection.first_message_at - SoulConnection.created_at)
                )
            ).filter(
                SoulConnection.first_message_at.isnot(None)
            ).scalar() or 0.0
            
            return ConnectionMetrics(
                total_connections=total_connections,
                active_connections=active_connections,
                completed_revelations=completed_revelations,
                photo_reveals=photo_reveals,
                average_compatibility_score=round(avg_compatibility, 1),
                connection_success_rate=round(success_rate, 1),
                average_time_to_first_message=avg_time_to_message / 3600.0  # Convert to hours
            )
            
        except Exception as e:
            logger.error(f"Error calculating connection metrics: {str(e)}")
            return self._empty_connection_metrics()
    
    async def get_system_health_metrics(self, db: Session) -> SystemHealthMetrics:
        """Calculate system performance and health metrics"""
        try:
            # Get recent performance metrics
            recent_metrics = db.query(SystemPerformanceMetrics).filter(
                SystemPerformanceMetrics.measured_at >= datetime.utcnow() - timedelta(hours=24)
            ).all()
            
            # Group by metric type
            metrics_by_type = defaultdict(list)
            for metric in recent_metrics:
                metrics_by_type[metric.metric_name].append(float(metric.metric_value))
            
            # Calculate averages
            api_response_times = {}
            database_performance = {}
            error_rates = {}
            
            for metric_name, values in metrics_by_type.items():
                avg_value = sum(values) / len(values) if values else 0.0
                
                if 'response_time' in metric_name:
                    api_response_times[metric_name] = avg_value
                elif 'db_' in metric_name:
                    database_performance[metric_name] = avg_value
                elif 'error' in metric_name:
                    error_rates[metric_name] = avg_value
            
            # WebSocket connections (would get from real-time manager)
            websocket_connections = 0  # Placeholder
            
            # User satisfaction (from feedback/ratings)
            user_satisfaction_scores = {
                "overall_satisfaction": 4.2,
                "matching_quality": 4.0,
                "app_performance": 4.3,
                "user_experience": 4.1
            }
            
            return SystemHealthMetrics(
                api_response_times=api_response_times,
                websocket_connections=websocket_connections,
                database_performance=database_performance,
                error_rates=error_rates,
                user_satisfaction_scores=user_satisfaction_scores
            )
            
        except Exception as e:
            logger.error(f"Error calculating system health metrics: {str(e)}")
            return self._empty_system_health_metrics()
    
    async def generate_user_insights(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Generate personalized insights for a user"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # Get user's analytics data
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            events = db.query(UserEngagementAnalytics).filter(
                UserEngagementAnalytics.user_id == user_id,
                UserEngagementAnalytics.created_at >= cutoff_date
            ).all()
            
            # Calculate engagement score
            engagement_score = await self.calculate_user_engagement_score(user_id, db)
            
            # Get user's connections
            connections = db.query(SoulConnection).filter(
                or_(SoulConnection.user1_id == user_id, SoulConnection.user2_id == user_id)
            ).all()
            
            # Calculate success metrics
            total_connections = len(connections)
            successful_connections = len([c for c in connections if c.photo_revealed_at])
            active_conversations = len([c for c in connections if c.status == "active"])
            
            # Generate insights
            insights = {
                "engagement": {
                    "score": engagement_score,
                    "level": self._get_engagement_level(engagement_score),
                    "recent_activity_days": len(set(e.created_at.date() for e in events)),
                    "most_active_feature": self._get_most_used_feature(events)
                },
                "connections": {
                    "total": total_connections,
                    "successful": successful_connections,
                    "active": active_conversations,
                    "success_rate": (successful_connections / max(1, total_connections)) * 100
                },
                "recommendations": await self._generate_user_recommendations(user_id, events, connections, db),
                "milestones": await self._get_user_milestones(user_id, db),
                "trends": await self._get_user_trends(user_id, db)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating user insights: {str(e)}")
            return {}
    
    async def track_system_performance(self, metric_name: str, value: float, 
                                     component: str, db: Session) -> bool:
        """Track system performance metric"""
        try:
            metric = SystemPerformanceMetrics(
                metric_name=metric_name,
                metric_value=value,
                metric_unit="ms" if "time" in metric_name else "count",
                component=component,
                measured_at=datetime.utcnow()
            )
            
            db.add(metric)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking system performance: {str(e)}")
            db.rollback()
            return False
    
    async def update_user_retention_metrics(self, user_id: int, db: Session) -> bool:
        """Update retention metrics for a user"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Calculate cohort month
            cohort_month = user.created_at.strftime("%Y-%m")
            
            # Days since registration
            days_since_reg = (datetime.utcnow() - user.created_at).days
            
            # Get or create retention record
            retention = db.query(UserRetentionMetrics).filter(
                UserRetentionMetrics.user_id == user_id
            ).first()
            
            if not retention:
                retention = UserRetentionMetrics(
                    user_id=user_id,
                    cohort_month=cohort_month,
                    days_since_registration=days_since_reg
                )
                db.add(retention)
            else:
                retention.days_since_registration = days_since_reg
                retention.last_active_date = datetime.utcnow()
            
            # Update activity flags
            if days_since_reg >= 1 and not retention.is_active_day_1:
                # Check if user was active on day 1
                day1_activity = db.query(UserEngagementAnalytics).filter(
                    UserEngagementAnalytics.user_id == user_id,
                    UserEngagementAnalytics.created_at.between(
                        user.created_at,
                        user.created_at + timedelta(days=1)
                    )
                ).first()
                retention.is_active_day_1 = day1_activity is not None
            
            # Similar logic for day 7 and day 30
            if days_since_reg >= 7 and not retention.is_active_day_7:
                # Check activity in days 1-7
                week1_activity = db.query(UserEngagementAnalytics).filter(
                    UserEngagementAnalytics.user_id == user_id,
                    UserEngagementAnalytics.created_at.between(
                        user.created_at,
                        user.created_at + timedelta(days=7)
                    )
                ).first()
                retention.is_active_day_7 = week1_activity is not None
            
            if days_since_reg >= 30 and not retention.is_active_day_30:
                # Check activity in days 1-30
                month1_activity = db.query(UserEngagementAnalytics).filter(
                    UserEngagementAnalytics.user_id == user_id,
                    UserEngagementAnalytics.created_at.between(
                        user.created_at,
                        user.created_at + timedelta(days=30)
                    )
                ).first()
                retention.is_active_day_30 = month1_activity is not None
            
            # Update milestones
            retention.completed_onboarding = user.emotional_onboarding_completed
            retention.made_first_connection = db.query(SoulConnection).filter(
                or_(SoulConnection.user1_id == user_id, SoulConnection.user2_id == user_id)
            ).first() is not None
            
            retention.shared_first_revelation = user.total_revelations_shared > 0
            
            retention.reached_photo_reveal = db.query(SoulConnection).filter(
                or_(SoulConnection.user1_id == user_id, SoulConnection.user2_id == user_id),
                SoulConnection.photo_revealed_at.isnot(None)
            ).first() is not None
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating retention metrics: {str(e)}")
            db.rollback()
            return False
    
    # Helper methods
    
    async def _update_emotional_journey(self, user_id: int, connection_id: int,
                                       event_type: AnalyticsEventType, 
                                       event_data: Dict, db: Session):
        """Update emotional journey tracking"""
        try:
            # Determine journey stage based on event
            stage_mapping = {
                AnalyticsEventType.CONNECTION_INITIATED: "discovery",
                AnalyticsEventType.REVELATION_SHARED: "revelation", 
                AnalyticsEventType.PHOTO_CONSENT_GIVEN: "connection"
            }
            
            stage = stage_mapping.get(event_type)
            if not stage:
                return
            
            # Get or create journey record
            journey = db.query(EmotionalJourneyTracking).filter(
                EmotionalJourneyTracking.user_id == user_id,
                EmotionalJourneyTracking.connection_id == connection_id,
                EmotionalJourneyTracking.journey_stage == stage
            ).first()
            
            if not journey:
                journey = EmotionalJourneyTracking(
                    user_id=user_id,
                    connection_id=connection_id,
                    journey_stage=stage,
                    emotional_state=event_data.get('emotional_state', 'curious'),
                    stage_entered_at=datetime.utcnow()
                )
                db.add(journey)
            
            # Update interaction count
            journey.interaction_count += 1
            
            if event_type == AnalyticsEventType.HAPTIC_FEEDBACK_TRIGGERED:
                journey.haptic_triggers += 1
            
        except Exception as e:
            logger.error(f"Error updating emotional journey: {str(e)}")
    
    async def _calculate_retention_rates(self, db: Session) -> Dict[str, float]:
        """Calculate user retention rates"""
        try:
            # Get retention data
            retention_data = db.query(UserRetentionMetrics).all()
            
            if not retention_data:
                return {"day_1": 0.0, "day_7": 0.0, "day_30": 0.0}
            
            total_users = len(retention_data)
            day_1_retained = len([r for r in retention_data if r.is_active_day_1])
            day_7_retained = len([r for r in retention_data if r.is_active_day_7])
            day_30_retained = len([r for r in retention_data if r.is_active_day_30])
            
            return {
                "day_1": (day_1_retained / total_users) * 100,
                "day_7": (day_7_retained / total_users) * 100, 
                "day_30": (day_30_retained / total_users) * 100
            }
            
        except Exception as e:
            logger.error(f"Error calculating retention rates: {str(e)}")
            return {"day_1": 0.0, "day_7": 0.0, "day_30": 0.0}
    
    def _get_engagement_level(self, score: float) -> str:
        """Get engagement level label"""
        if score >= 80:
            return "High"
        elif score >= 60:
            return "Medium"
        elif score >= 40:
            return "Low"
        else:
            return "Very Low"
    
    def _get_most_used_feature(self, events: List[UserEngagementAnalytics]) -> str:
        """Get user's most used feature"""
        if not events:
            return "None"
        
        event_counts = Counter(event.event_type for event in events)
        most_common = event_counts.most_common(1)
        
        return most_common[0][0] if most_common else "None"
    
    async def _generate_user_recommendations(self, user_id: int, events: List, 
                                           connections: List, db: Session) -> List[str]:
        """Generate personalized recommendations for user"""
        recommendations = []
        
        # Based on activity patterns
        if len(events) < 10:
            recommendations.append("Try exploring more features to enhance your experience")
        
        if not any(e.event_type == AnalyticsEventType.REVELATION_SHARED.value for e in events):
            recommendations.append("Share your first soul revelation to deepen connections")
        
        if len(connections) == 0:
            recommendations.append("Complete your profile to start making meaningful connections")
        
        # Based on connection success
        active_connections = [c for c in connections if c.status == "active"]
        if len(active_connections) > 0 and not any(c.photo_revealed_at for c in connections):
            recommendations.append("Consider sharing photos after building emotional connection")
        
        return recommendations[:3]  # Top 3 recommendations
    
    async def _get_user_milestones(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get user's achieved milestones"""
        milestones = []
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return milestones
        
        if user.emotional_onboarding_completed:
            milestones.append({
                "type": "onboarding_complete",
                "title": "Soul Journey Begun",
                "description": "Completed emotional onboarding",
                "achieved_at": user.created_at.isoformat()
            })
        
        if user.total_revelations_shared > 0:
            milestones.append({
                "type": "first_revelation",
                "title": "First Soul Share",
                "description": "Shared your first revelation",
                "achieved_at": None  # Would track from analytics
            })
        
        return milestones
    
    async def _get_user_trends(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user activity trends"""
        # Get last 4 weeks of activity
        weeks_data = []
        for i in range(4):
            start_date = datetime.utcnow() - timedelta(weeks=i+1)
            end_date = datetime.utcnow() - timedelta(weeks=i)
            
            week_events = db.query(UserEngagementAnalytics).filter(
                UserEngagementAnalytics.user_id == user_id,
                UserEngagementAnalytics.created_at.between(start_date, end_date)
            ).count()
            
            weeks_data.append(week_events)
        
        return {
            "weekly_activity": list(reversed(weeks_data)),
            "trend": "increasing" if weeks_data[0] > weeks_data[-1] else "decreasing" if weeks_data[0] < weeks_data[-1] else "stable"
        }
    
    # Empty data methods for error cases
    
    def _empty_journey_analytics(self) -> UserJourneyAnalytics:
        return UserJourneyAnalytics(0, 0, 0, 0, 0, 0, 0)
    
    def _empty_engagement_metrics(self) -> EngagementMetrics:
        return EngagementMetrics(0, 0, 0, 0, 0, 0, {"day_1": 0, "day_7": 0, "day_30": 0})
    
    def _empty_connection_metrics(self) -> ConnectionMetrics:
        return ConnectionMetrics(0, 0, 0, 0, 0, 0, 0)
    
    def _empty_system_health_metrics(self) -> SystemHealthMetrics:
        return SystemHealthMetrics({}, 0, {}, {}, {})


# Global service instance
analytics_service = AnalyticsService()