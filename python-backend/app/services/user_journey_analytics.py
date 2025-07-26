# User Journey Analytics Service for Dinner First
# Comprehensive analysis of user paths, conversion funnels, and behavioral insights

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import logging
from clickhouse_driver import Client
import redis
import pandas as pd
from collections import defaultdict, OrderedDict
import asyncio

logger = logging.getLogger(__name__)

class JourneyStage(Enum):
    REGISTRATION = "registration"
    ONBOARDING = "onboarding"
    PROFILE_CREATION = "profile_creation"
    DISCOVERY = "discovery"
    MATCHING = "matching"
    CONVERSATION = "conversation"
    REVELATION = "revelation"
    PHOTO_REVEAL = "photo_reveal"
    DATE_PLANNING = "date_planning"
    SUBSCRIPTION = "subscription"
    RETENTION = "retention"
    CHURN = "churn"

class ConversionEvent(Enum):
    SIGNED_UP = "signed_up"
    COMPLETED_ONBOARDING = "completed_onboarding"
    FIRST_PROFILE_VIEW = "first_profile_view"
    FIRST_LIKE = "first_like"
    FIRST_MATCH = "first_match"
    FIRST_MESSAGE = "first_message"
    FIRST_REVELATION = "first_revelation"
    PHOTO_REVEALED = "photo_revealed"
    FIRST_DATE_PLANNED = "first_date_planned"
    BECAME_SUBSCRIBER = "became_subscriber"

class CohortType(Enum):
    REGISTRATION_DATE = "registration_date"
    FIRST_MATCH_DATE = "first_match_date"
    SUBSCRIPTION_DATE = "subscription_date"
    FEATURE_USAGE = "feature_usage"

@dataclass
class UserJourney:
    user_id: int
    journey_start: datetime
    current_stage: JourneyStage
    completed_stages: List[JourneyStage]
    conversion_events: List[Dict[str, Any]]
    stage_durations: Dict[str, float]  # Hours spent in each stage
    total_journey_time: float
    drop_off_stage: Optional[JourneyStage] = None
    is_active: bool = True

@dataclass
class ConversionFunnel:
    funnel_name: str
    stages: List[str]
    conversion_rates: Dict[str, float]
    drop_off_rates: Dict[str, float]
    user_counts: Dict[str, int]
    avg_time_between_stages: Dict[str, float]
    analysis_period: Tuple[datetime, datetime]

@dataclass
class CohortAnalysis:
    cohort_name: str
    cohort_type: CohortType
    cohort_period: str  # e.g., "2024-01", "Week 1"
    total_users: int
    retention_rates: Dict[str, float]  # period -> retention rate
    activity_metrics: Dict[str, Any]
    revenue_metrics: Dict[str, float]

class UserJourneyAnalyticsService:
    """
    Comprehensive user journey analytics and conversion funnel analysis
    """
    
    def __init__(self, clickhouse_client: Client, redis_client: redis.Redis):
        self.clickhouse = clickhouse_client
        self.redis = redis_client
        
        # Predefined conversion funnels for dating platform
        self.standard_funnels = {
            "user_acquisition": [
                "landing_page_view", "sign_up_start", "sign_up_complete", 
                "email_verification", "onboarding_complete"
            ],
            "matching_funnel": [
                "first_profile_view", "first_like", "first_match", 
                "first_message", "conversation_ongoing"
            ],
            "soul_before_skin": [
                "first_match", "first_revelation", "revelation_exchange", 
                "photo_reveal_consent", "photo_revealed", "date_planned"
            ],
            "monetization": [
                "free_user", "premium_feature_shown", "paywall_hit", 
                "subscription_start", "subscription_active"
            ]
        }
        
        # Journey stage progressions
        self.stage_progressions = {
            JourneyStage.REGISTRATION: JourneyStage.ONBOARDING,
            JourneyStage.ONBOARDING: JourneyStage.PROFILE_CREATION,
            JourneyStage.PROFILE_CREATION: JourneyStage.DISCOVERY,
            JourneyStage.DISCOVERY: JourneyStage.MATCHING,
            JourneyStage.MATCHING: JourneyStage.CONVERSATION,
            JourneyStage.CONVERSATION: JourneyStage.REVELATION,
            JourneyStage.REVELATION: JourneyStage.PHOTO_REVEAL,
            JourneyStage.PHOTO_REVEAL: JourneyStage.DATE_PLANNING,
        }
    
    async def track_user_journey_event(self, user_id: int, event_type: str, 
                                     stage: JourneyStage, event_data: Dict[str, Any]) -> bool:
        """
        Track a user journey event and update user's current stage
        """
        try:
            # Get current user journey
            journey = await self._get_user_journey(user_id)
            
            if not journey:
                # Create new journey for new user
                journey = await self._create_user_journey(user_id, stage)
            
            # Update journey based on event
            await self._update_user_journey(journey, event_type, stage, event_data)
            
            # Store updated journey
            await self._store_user_journey(journey)
            
            # Update real-time funnel metrics
            await self._update_funnel_metrics(user_id, stage, event_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track journey event for user {user_id}: {e}")
            return False
    
    async def get_conversion_funnel_analysis(self, funnel_name: str, 
                                           start_date: datetime, 
                                           end_date: datetime) -> ConversionFunnel:
        """
        Analyze conversion funnel performance for a specific time period
        """
        try:
            if funnel_name not in self.standard_funnels:
                raise ValueError(f"Unknown funnel: {funnel_name}")
            
            stages = self.standard_funnels[funnel_name]
            
            # Get user counts for each stage
            user_counts = await self._get_funnel_user_counts(stages, start_date, end_date)
            
            # Calculate conversion rates
            conversion_rates = self._calculate_conversion_rates(user_counts, stages)
            
            # Calculate drop-off rates
            drop_off_rates = self._calculate_drop_off_rates(user_counts, stages)
            
            # Calculate average time between stages
            avg_times = await self._calculate_stage_timing(stages, start_date, end_date)
            
            return ConversionFunnel(
                funnel_name=funnel_name,
                stages=stages,
                conversion_rates=conversion_rates,
                drop_off_rates=drop_off_rates,
                user_counts=user_counts,
                avg_time_between_stages=avg_times,
                analysis_period=(start_date, end_date)
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze funnel {funnel_name}: {e}")
            raise
    
    async def perform_cohort_analysis(self, cohort_type: CohortType, 
                                    start_date: datetime, 
                                    end_date: datetime) -> List[CohortAnalysis]:
        """
        Perform cohort analysis for user retention and behavior
        """
        try:
            cohorts = []
            
            if cohort_type == CohortType.REGISTRATION_DATE:
                cohorts = await self._analyze_registration_cohorts(start_date, end_date)
            elif cohort_type == CohortType.FIRST_MATCH_DATE:
                cohorts = await self._analyze_match_cohorts(start_date, end_date)
            elif cohort_type == CohortType.SUBSCRIPTION_DATE:
                cohorts = await self._analyze_subscription_cohorts(start_date, end_date)
            elif cohort_type == CohortType.FEATURE_USAGE:
                cohorts = await self._analyze_feature_usage_cohorts(start_date, end_date)
            
            return cohorts
            
        except Exception as e:
            logger.error(f"Failed to perform cohort analysis: {e}")
            return []
    
    async def get_user_journey_insights(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive insights about a specific user's journey
        """
        try:
            journey = await self._get_user_journey(user_id)
            
            if not journey:
                return {"error": "User journey not found"}
            
            # Calculate journey metrics
            insights = {
                "user_id": user_id,
                "journey_summary": {
                    "start_date": journey.journey_start,
                    "current_stage": journey.current_stage.value,
                    "total_time_days": journey.total_journey_time / 24,
                    "completed_stages": [stage.value for stage in journey.completed_stages],
                    "is_active": journey.is_active
                },
                "stage_performance": {},
                "conversion_events": journey.conversion_events,
                "behavioral_insights": await self._get_behavioral_insights(user_id),
                "recommendations": await self._generate_journey_recommendations(journey)
            }
            
            # Add stage-specific insights
            for stage_name, duration in journey.stage_durations.items():
                insights["stage_performance"][stage_name] = {
                    "time_spent_hours": duration,
                    "relative_performance": await self._get_stage_performance_percentile(stage_name, duration)
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get journey insights for user {user_id}: {e}")
            return {}
    
    async def identify_journey_bottlenecks(self, start_date: datetime, 
                                         end_date: datetime) -> Dict[str, Any]:
        """
        Identify bottlenecks and optimization opportunities in user journeys
        """
        try:
            bottlenecks = {
                "analysis_period": {"start": start_date, "end": end_date},
                "stage_bottlenecks": {},
                "funnel_bottlenecks": {},
                "recommendations": []
            }
            
            # Analyze each standard funnel for bottlenecks
            for funnel_name in self.standard_funnels:
                funnel_analysis = await self.get_conversion_funnel_analysis(
                    funnel_name, start_date, end_date
                )
                
                # Identify stages with low conversion rates
                low_conversion_stages = [
                    stage for stage, rate in funnel_analysis.conversion_rates.items()
                    if rate < 0.5  # Less than 50% conversion
                ]
                
                if low_conversion_stages:
                    bottlenecks["funnel_bottlenecks"][funnel_name] = {
                        "problematic_stages": low_conversion_stages,
                        "conversion_rates": {
                            stage: funnel_analysis.conversion_rates[stage]
                            for stage in low_conversion_stages
                        }
                    }
            
            # Analyze individual stages
            for stage in JourneyStage:
                stage_metrics = await self._analyze_stage_performance(stage, start_date, end_date)
                
                if stage_metrics["avg_time_spent"] > stage_metrics["expected_time"] * 2:
                    bottlenecks["stage_bottlenecks"][stage.value] = {
                        "issue": "excessive_time",
                        "avg_time_hours": stage_metrics["avg_time_spent"],
                        "expected_time_hours": stage_metrics["expected_time"],
                        "affected_users": stage_metrics["user_count"]
                    }
            
            # Generate recommendations
            bottlenecks["recommendations"] = self._generate_bottleneck_recommendations(bottlenecks)
            
            return bottlenecks
            
        except Exception as e:
            logger.error(f"Failed to identify journey bottlenecks: {e}")
            return {}
    
    async def get_real_time_funnel_metrics(self) -> Dict[str, Any]:
        """
        Get real-time funnel performance metrics
        """
        try:
            metrics = {}
            
            for funnel_name in self.standard_funnels:
                funnel_key = f"realtime_funnel:{funnel_name}"
                funnel_data = self.redis.hgetall(funnel_key)
                
                if funnel_data:
                    metrics[funnel_name] = {
                        k.decode(): int(v.decode()) 
                        for k, v in funnel_data.items()
                    }
                else:
                    metrics[funnel_name] = {}
            
            # Add overall metrics
            metrics["summary"] = {
                "active_journeys": await self._count_active_journeys(),
                "completed_journeys_today": await self._count_completed_journeys_today(),
                "avg_journey_time_hours": await self._get_avg_journey_time(),
                "last_updated": datetime.utcnow()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get real-time funnel metrics: {e}")
            return {}
    
    async def generate_journey_report(self, start_date: datetime, 
                                    end_date: datetime) -> Dict[str, Any]:
        """
        Generate comprehensive journey analytics report
        """
        try:
            report = {
                "report_period": {"start": start_date, "end": end_date},
                "executive_summary": {},
                "funnel_analysis": {},
                "cohort_analysis": {},
                "user_segmentation": {},
                "recommendations": []
            }
            
            # Executive summary
            total_users = await self._count_users_in_period(start_date, end_date)
            completed_journeys = await self._count_completed_journeys(start_date, end_date)
            
            report["executive_summary"] = {
                "total_users": total_users,
                "completed_journeys": completed_journeys,
                "completion_rate": completed_journeys / total_users if total_users > 0 else 0,
                "avg_journey_time_hours": await self._get_avg_journey_time_period(start_date, end_date),
                "top_drop_off_stage": await self._get_top_drop_off_stage(start_date, end_date)
            }
            
            # Funnel analysis for all standard funnels
            for funnel_name in self.standard_funnels:
                funnel_analysis = await self.get_conversion_funnel_analysis(
                    funnel_name, start_date, end_date
                )
                report["funnel_analysis"][funnel_name] = asdict(funnel_analysis)
            
            # Cohort analysis
            for cohort_type in CohortType:
                cohort_analyses = await self.perform_cohort_analysis(
                    cohort_type, start_date, end_date
                )
                report["cohort_analysis"][cohort_type.value] = [
                    asdict(cohort) for cohort in cohort_analyses
                ]
            
            # User segmentation insights
            report["user_segmentation"] = await self._generate_user_segmentation(start_date, end_date)
            
            # Generate recommendations
            report["recommendations"] = await self._generate_report_recommendations(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate journey report: {e}")
            return {}
    
    # Private helper methods
    
    async def _get_user_journey(self, user_id: int) -> Optional[UserJourney]:
        """Get user's current journey from storage"""
        try:
            journey_key = f"user_journey:{user_id}"
            journey_data = self.redis.get(journey_key)
            
            if journey_data:
                data = eval(journey_data)  # In production, use proper JSON serialization
                return UserJourney(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user journey for {user_id}: {e}")
            return None
    
    async def _create_user_journey(self, user_id: int, initial_stage: JourneyStage) -> UserJourney:
        """Create a new user journey"""
        return UserJourney(
            user_id=user_id,
            journey_start=datetime.utcnow(),
            current_stage=initial_stage,
            completed_stages=[],
            conversion_events=[],
            stage_durations={},
            total_journey_time=0.0,
            is_active=True
        )
    
    async def _update_user_journey(self, journey: UserJourney, event_type: str, 
                                 stage: JourneyStage, event_data: Dict[str, Any]):
        """Update user journey with new event"""
        now = datetime.utcnow()
        
        # Update stage if progressing
        if stage != journey.current_stage:
            # Calculate time spent in previous stage
            if journey.current_stage:
                stage_name = journey.current_stage.value
                time_in_stage = (now - journey.journey_start).total_seconds() / 3600
                journey.stage_durations[stage_name] = time_in_stage
            
            # Mark previous stage as completed
            if journey.current_stage not in journey.completed_stages:
                journey.completed_stages.append(journey.current_stage)
            
            # Move to new stage
            journey.current_stage = stage
        
        # Add conversion event
        conversion_event = {
            "event_type": event_type,
            "stage": stage.value,
            "timestamp": now,
            "data": event_data
        }
        journey.conversion_events.append(conversion_event)
        
        # Update total journey time
        journey.total_journey_time = (now - journey.journey_start).total_seconds() / 3600
    
    async def _store_user_journey(self, journey: UserJourney):
        """Store user journey in Redis"""
        try:
            journey_key = f"user_journey:{journey.user_id}"
            journey_data = asdict(journey)
            
            # Convert datetime objects to strings for storage
            journey_data['journey_start'] = journey.journey_start.isoformat()
            journey_data['completed_stages'] = [stage.value for stage in journey.completed_stages]
            journey_data['current_stage'] = journey.current_stage.value
            
            self.redis.set(journey_key, str(journey_data), ex=86400 * 90)  # 90 days
            
        except Exception as e:
            logger.error(f"Failed to store user journey: {e}")
            raise
    
    async def _update_funnel_metrics(self, user_id: int, stage: JourneyStage, event_type: str):
        """Update real-time funnel metrics"""
        try:
            # Update metrics for relevant funnels
            for funnel_name, stages in self.standard_funnels.items():
                if stage.value in stages or event_type in stages:
                    funnel_key = f"realtime_funnel:{funnel_name}"
                    self.redis.hincrby(funnel_key, stage.value, 1)
                    self.redis.expire(funnel_key, 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Failed to update funnel metrics: {e}")
    
    async def _get_funnel_user_counts(self, stages: List[str], 
                                    start_date: datetime, 
                                    end_date: datetime) -> Dict[str, int]:
        """Get user counts for each funnel stage"""
        # Mock implementation - would query ClickHouse
        user_counts = {}
        base_count = 1000
        
        for i, stage in enumerate(stages):
            # Simulate funnel drop-off
            user_counts[stage] = int(base_count * (0.8 ** i))
        
        return user_counts
    
    def _calculate_conversion_rates(self, user_counts: Dict[str, int], 
                                  stages: List[str]) -> Dict[str, float]:
        """Calculate conversion rates between funnel stages"""
        conversion_rates = {}
        
        for i in range(1, len(stages)):
            prev_stage = stages[i-1]
            current_stage = stages[i]
            
            prev_count = user_counts.get(prev_stage, 0)
            current_count = user_counts.get(current_stage, 0)
            
            if prev_count > 0:
                conversion_rates[f"{prev_stage}_to_{current_stage}"] = current_count / prev_count
            else:
                conversion_rates[f"{prev_stage}_to_{current_stage}"] = 0.0
        
        return conversion_rates
    
    def _calculate_drop_off_rates(self, user_counts: Dict[str, int], 
                                stages: List[str]) -> Dict[str, float]:
        """Calculate drop-off rates for each funnel stage"""
        drop_off_rates = {}
        
        for i in range(1, len(stages)):
            prev_stage = stages[i-1]
            current_stage = stages[i]
            
            prev_count = user_counts.get(prev_stage, 0)
            current_count = user_counts.get(current_stage, 0)
            
            if prev_count > 0:
                drop_off_rates[f"{prev_stage}_to_{current_stage}"] = (prev_count - current_count) / prev_count
            else:
                drop_off_rates[f"{prev_stage}_to_{current_stage}"] = 0.0
        
        return drop_off_rates
    
    async def _calculate_stage_timing(self, stages: List[str], 
                                    start_date: datetime, 
                                    end_date: datetime) -> Dict[str, float]:
        """Calculate average time between stages"""
        # Mock implementation
        avg_times = {}
        
        for i in range(1, len(stages)):
            prev_stage = stages[i-1]
            current_stage = stages[i]
            # Mock average times in hours
            avg_times[f"{prev_stage}_to_{current_stage}"] = 24.0 * (i + 1)
        
        return avg_times
    
    async def _analyze_registration_cohorts(self, start_date: datetime, 
                                          end_date: datetime) -> List[CohortAnalysis]:
        """Analyze user cohorts by registration date"""
        cohorts = []
        
        # Generate monthly cohorts
        current_date = start_date.replace(day=1)
        while current_date <= end_date:
            cohort_name = current_date.strftime("%Y-%m")
            
            # Mock cohort data
            cohort = CohortAnalysis(
                cohort_name=f"Registration {cohort_name}",
                cohort_type=CohortType.REGISTRATION_DATE,
                cohort_period=cohort_name,
                total_users=500,
                retention_rates={
                    "week_1": 0.75,
                    "week_2": 0.60,
                    "month_1": 0.45,
                    "month_3": 0.30,
                    "month_6": 0.20
                },
                activity_metrics={
                    "avg_sessions_per_user": 8.5,
                    "avg_matches_per_user": 12.3,
                    "avg_conversations_per_user": 4.7
                },
                revenue_metrics={
                    "total_revenue": 2500.0,
                    "revenue_per_user": 5.0,
                    "subscription_rate": 0.15
                }
            )
            
            cohorts.append(cohort)
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return cohorts
    
    async def _analyze_match_cohorts(self, start_date: datetime, 
                                   end_date: datetime) -> List[CohortAnalysis]:
        """Analyze cohorts by first match date"""
        # Similar implementation to registration cohorts
        return []
    
    async def _analyze_subscription_cohorts(self, start_date: datetime, 
                                          end_date: datetime) -> List[CohortAnalysis]:
        """Analyze subscription cohorts"""
        # Similar implementation to registration cohorts
        return []
    
    async def _analyze_feature_usage_cohorts(self, start_date: datetime, 
                                           end_date: datetime) -> List[CohortAnalysis]:
        """Analyze cohorts by feature usage patterns"""
        # Similar implementation to registration cohorts
        return []
    
    async def _get_behavioral_insights(self, user_id: int) -> Dict[str, Any]:
        """Get behavioral insights for a user"""
        return {
            "engagement_pattern": "evening_active",
            "preferred_features": ["discovery", "messaging"],
            "interaction_style": "selective",
            "response_time_avg_hours": 3.5
        }
    
    async def _generate_journey_recommendations(self, journey: UserJourney) -> List[Dict[str, Any]]:
        """Generate personalized journey recommendations"""
        recommendations = []
        
        if journey.current_stage == JourneyStage.DISCOVERY:
            recommendations.append({
                "type": "engagement",
                "message": "Try liking more profiles to increase your match potential",
                "action": "increase_activity"
            })
        
        if len(journey.completed_stages) < 3:
            recommendations.append({
                "type": "onboarding",
                "message": "Complete your profile to attract better matches",
                "action": "complete_profile"
            })
        
        return recommendations
    
    async def _get_stage_performance_percentile(self, stage_name: str, duration: float) -> float:
        """Get percentile rank for stage performance"""
        # Mock implementation - would calculate against historical data
        return 0.65  # 65th percentile
    
    async def _analyze_stage_performance(self, stage: JourneyStage, 
                                       start_date: datetime, 
                                       end_date: datetime) -> Dict[str, Any]:
        """Analyze performance metrics for a specific stage"""
        return {
            "avg_time_spent": 48.0,  # hours
            "expected_time": 24.0,   # hours
            "user_count": 250,
            "completion_rate": 0.75
        }
    
    def _generate_bottleneck_recommendations(self, bottlenecks: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on identified bottlenecks"""
        recommendations = []
        
        if bottlenecks["stage_bottlenecks"]:
            recommendations.append("Optimize user experience in slow-performing stages")
        
        if bottlenecks["funnel_bottlenecks"]:
            recommendations.append("Improve conversion rates in underperforming funnels")
        
        return recommendations
    
    # Additional helper methods for metrics and analysis
    
    async def _count_active_journeys(self) -> int:
        """Count currently active user journeys"""
        return 450  # Mock value
    
    async def _count_completed_journeys_today(self) -> int:
        """Count journeys completed today"""
        return 25  # Mock value
    
    async def _get_avg_journey_time(self) -> float:
        """Get average journey time in hours"""
        return 72.5  # Mock value
    
    async def _count_users_in_period(self, start_date: datetime, end_date: datetime) -> int:
        """Count users in period"""
        return 1500  # Mock value
    
    async def _count_completed_journeys(self, start_date: datetime, end_date: datetime) -> int:
        """Count completed journeys in period"""
        return 450  # Mock value
    
    async def _get_avg_journey_time_period(self, start_date: datetime, end_date: datetime) -> float:
        """Get average journey time for period"""
        return 65.3  # Mock value
    
    async def _get_top_drop_off_stage(self, start_date: datetime, end_date: datetime) -> str:
        """Get stage with highest drop-off rate"""
        return "discovery"  # Mock value
    
    async def _generate_user_segmentation(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate user segmentation insights"""
        return {
            "high_engagement": {"count": 300, "characteristics": ["daily_active", "multiple_matches"]},
            "moderate_engagement": {"count": 700, "characteristics": ["weekly_active", "some_matches"]},
            "low_engagement": {"count": 500, "characteristics": ["monthly_active", "few_matches"]}
        }
    
    async def _generate_report_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on report data"""
        return [
            "Focus on improving onboarding completion rates",
            "Optimize discovery experience to reduce drop-offs",
            "Implement re-engagement campaigns for inactive users"
        ]