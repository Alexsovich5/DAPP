# Analytics Service for Dinner1
# Comprehensive user behavior tracking and business intelligence

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import json
import uuid
from dataclasses import dataclass, asdict
from clickhouse_driver import Client
import redis
from user_agents import parse as parse_user_agent
import geoip2.database

logger = logging.getLogger(__name__)

class EventType(Enum):
    # User actions
    PAGE_VIEW = "page_view"
    BUTTON_CLICK = "button_click"
    FORM_SUBMIT = "form_submit"
    SEARCH = "search"
    FILTER_APPLY = "filter_apply"
    
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_RESET = "password_reset"
    
    # Profile actions
    PROFILE_VIEW = "profile_view"
    PROFILE_EDIT = "profile_edit"
    PHOTO_UPLOAD = "photo_upload"
    PHOTO_DELETE = "photo_delete"
    
    # Matching and interactions
    PROFILE_LIKE = "profile_like"
    PROFILE_PASS = "profile_pass"
    SUPER_LIKE = "super_like"
    MATCH_CREATED = "match_created"
    
    # Messaging
    MESSAGE_SENT = "message_sent"
    MESSAGE_READ = "message_read"
    CONVERSATION_STARTED = "conversation_started"
    
    # Soul Before Skin specific
    REVELATION_CREATED = "revelation_created"
    REVELATION_VIEWED = "revelation_viewed"
    PHOTO_REVEAL_CONSENT = "photo_reveal_consent"
    PHOTO_REVEALED = "photo_revealed"
    
    # Safety and moderation
    USER_REPORTED = "user_reported"
    USER_BLOCKED = "user_blocked"
    CONTENT_FLAGGED = "content_flagged"
    
    # Business events
    SUBSCRIPTION_STARTED = "subscription_started"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PURCHASE_MADE = "purchase_made"
    
    # Lifecycle events
    ONBOARDING_COMPLETED = "onboarding_completed"
    FIRST_MATCH = "first_match"
    FIRST_DATE_PLANNED = "first_date_planned"
    ACCOUNT_DELETED = "account_deleted"

class EventCategory(Enum):
    USER_BEHAVIOR = "user_behavior"
    AUTHENTICATION = "authentication"
    PROFILE_MANAGEMENT = "profile_management"
    MATCHING = "matching"
    MESSAGING = "messaging"
    REVELATION = "revelation"
    SAFETY = "safety"
    BUSINESS = "business"
    LIFECYCLE = "lifecycle"

@dataclass
class AnalyticsEvent:
    event_id: str
    user_id: Optional[int]
    session_id: str
    event_type: EventType
    event_category: EventCategory
    properties: Dict[str, Any]
    timestamp: datetime
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class AnalyticsService:
    """
    Comprehensive analytics service for dating platform insights
    """
    
    def __init__(self, clickhouse_client: Client, redis_client: redis.Redis):
        self.clickhouse = clickhouse_client
        self.redis = redis_client
        self.geoip_reader = self._load_geoip_database()
        
    def _load_geoip_database(self):
        """Load GeoIP database for location tracking"""
        try:
            return geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-City.mmdb')
        except Exception as e:
            logger.warning(f"Could not load GeoIP database: {e}")
            return None
    
    async def track_event(self, event: AnalyticsEvent) -> bool:
        """
        Track a user event with enriched metadata
        """
        try:
            # Enrich event with additional metadata
            enriched_event = await self._enrich_event(event)
            
            # Store in ClickHouse for analytics
            await self._store_event_clickhouse(enriched_event)
            
            # Store in Redis for real-time processing
            await self._store_event_redis(enriched_event)
            
            # Process real-time metrics
            await self._update_real_time_metrics(enriched_event)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track event {event.event_id}: {str(e)}")
            return False
    
    async def _enrich_event(self, event: AnalyticsEvent) -> Dict:
        """
        Enrich event with additional metadata
        """
        enriched = asdict(event)
        
        # Parse user agent
        if event.user_agent:
            ua = parse_user_agent(event.user_agent)
            enriched.update({
                'device_type': self._get_device_type(ua),
                'browser': ua.browser.family,
                'browser_version': ua.browser.version_string,
                'os': ua.os.family,
                'os_version': ua.os.version_string
            })
        
        # Get location from IP
        if event.ip_address and self.geoip_reader:
            try:
                response = self.geoip_reader.city(event.ip_address)
                enriched.update({
                    'country': response.country.iso_code,
                    'city': response.city.name,
                    'latitude': float(response.location.latitude) if response.location.latitude else None,
                    'longitude': float(response.location.longitude) if response.location.longitude else None
                })
            except Exception as e:
                logger.debug(f"Could not get location for IP {event.ip_address}: {e}")
        
        # Add derived fields
        enriched.update({
            'date': event.timestamp.date(),
            'hour': event.timestamp.hour,
            'day_of_week': event.timestamp.weekday(),
            'is_weekend': event.timestamp.weekday() >= 5
        })
        
        return enriched
    
    def _get_device_type(self, ua) -> str:
        """Determine device type from user agent"""
        if ua.is_mobile:
            return 'mobile'
        elif ua.is_tablet:
            return 'tablet'
        elif ua.is_pc:
            return 'desktop'
        else:
            return 'unknown'
    
    async def _store_event_clickhouse(self, event_data: Dict):
        """Store event in ClickHouse for analytics"""
        try:
            # Map to ClickHouse table structure
            ch_event = {
                'event_id': event_data['event_id'],
                'user_id': event_data['user_id'] or 0,
                'session_id': event_data['session_id'],
                'event_type': event_data['event_type'].value if hasattr(event_data['event_type'], 'value') else event_data['event_type'],
                'event_category': event_data['event_category'].value if hasattr(event_data['event_category'], 'value') else event_data['event_category'],
                'page_url': event_data.get('page_url', ''),
                'referrer': event_data.get('referrer', ''),
                'user_agent': event_data.get('user_agent', ''),
                'ip_address': event_data.get('ip_address', ''),
                'country': event_data.get('country', ''),
                'city': event_data.get('city', ''),
                'device_type': event_data.get('device_type', ''),
                'browser': event_data.get('browser', ''),
                'os': event_data.get('os', ''),
                'properties': event_data.get('properties', {}),
                'timestamp': event_data['timestamp'],
                'date': event_data['date']
            }
            
            # Insert into ClickHouse
            self.clickhouse.execute(
                "INSERT INTO user_events VALUES",
                [ch_event]
            )
            
        except Exception as e:
            logger.error(f"Failed to store event in ClickHouse: {e}")
            raise
    
    async def _store_event_redis(self, event_data: Dict):
        """Store event in Redis for real-time processing"""
        try:
            # Store in Redis stream for real-time processing
            stream_key = f"events:{event_data['event_category']}"
            
            self.redis.xadd(
                stream_key,
                event_data,
                maxlen=10000  # Keep last 10k events per category
            )
            
            # Store in recent events for dashboard
            recent_events_key = "recent_events"
            self.redis.lpush(recent_events_key, json.dumps(event_data, default=str))
            self.redis.ltrim(recent_events_key, 0, 999)  # Keep last 1000 events
            
        except Exception as e:
            logger.error(f"Failed to store event in Redis: {e}")
    
    async def _update_real_time_metrics(self, event_data: Dict):
        """Update real-time metrics in Redis"""
        try:
            now = datetime.utcnow()
            hour_key = now.strftime("%Y-%m-%d-%H")
            day_key = now.strftime("%Y-%m-%d")
            
            # Increment counters
            pipe = self.redis.pipeline()
            
            # Event counters
            pipe.hincrby(f"metrics:hourly:{hour_key}", f"events:{event_data['event_type']}", 1)
            pipe.hincrby(f"metrics:daily:{day_key}", f"events:{event_data['event_type']}", 1)
            
            # User activity
            if event_data['user_id']:
                pipe.sadd(f"active_users:hourly:{hour_key}", event_data['user_id'])
                pipe.sadd(f"active_users:daily:{day_key}", event_data['user_id'])
                pipe.expire(f"active_users:hourly:{hour_key}", 3600 * 25)  # Keep for 25 hours
                pipe.expire(f"active_users:daily:{day_key}", 86400 * 32)   # Keep for 32 days
            
            # Category-specific metrics
            await self._update_category_metrics(event_data, pipe, hour_key, day_key)
            
            pipe.execute()
            
        except Exception as e:
            logger.error(f"Failed to update real-time metrics: {e}")
    
    async def _update_category_metrics(self, event_data: Dict, pipe, hour_key: str, day_key: str):
        """Update category-specific metrics"""
        event_type = event_data['event_type']
        properties = event_data.get('properties', {})
        
        # Matching metrics
        if event_type in ['profile_like', 'profile_pass', 'super_like']:
            pipe.hincrby(f"metrics:hourly:{hour_key}", "profile_interactions", 1)
            pipe.hincrby(f"metrics:daily:{day_key}", "profile_interactions", 1)
            
        elif event_type == 'match_created':
            pipe.hincrby(f"metrics:hourly:{hour_key}", "matches_created", 1)
            pipe.hincrby(f"metrics:daily:{day_key}", "matches_created", 1)
            
        # Messaging metrics
        elif event_type == 'message_sent':
            pipe.hincrby(f"metrics:hourly:{hour_key}", "messages_sent", 1)
            pipe.hincrby(f"metrics:daily:{day_key}", "messages_sent", 1)
            
        elif event_type == 'conversation_started':
            pipe.hincrby(f"metrics:hourly:{hour_key}", "conversations_started", 1)
            pipe.hincrby(f"metrics:daily:{day_key}", "conversations_started", 1)
        
        # Revenue metrics
        elif event_type in ['subscription_started', 'purchase_made']:
            amount = properties.get('amount_cents', 0)
            pipe.hincrby(f"metrics:hourly:{hour_key}", "revenue_cents", amount)
            pipe.hincrby(f"metrics:daily:{day_key}", "revenue_cents", amount)
        
        # Safety metrics
        elif event_type in ['user_reported', 'content_flagged']:
            pipe.hincrby(f"metrics:hourly:{hour_key}", "safety_events", 1)
            pipe.hincrby(f"metrics:daily:{day_key}", "safety_events", 1)
    
    async def get_real_time_metrics(self) -> Dict:
        """Get current real-time metrics"""
        try:
            now = datetime.utcnow()
            hour_key = now.strftime("%Y-%m-%d-%H")
            day_key = now.strftime("%Y-%m-%d")
            
            # Get hourly and daily metrics
            hourly_metrics = self.redis.hgetall(f"metrics:hourly:{hour_key}")
            daily_metrics = self.redis.hgetall(f"metrics:daily:{day_key}")
            
            # Get active user counts
            active_users_hour = self.redis.scard(f"active_users:hourly:{hour_key}")
            active_users_day = self.redis.scard(f"active_users:daily:{day_key}")
            
            # Convert to proper types
            hourly_metrics = {k.decode(): int(v) for k, v in hourly_metrics.items()}
            daily_metrics = {k.decode(): int(v) for k, v in daily_metrics.items()}
            
            return {
                'timestamp': now,
                'hourly': {
                    'active_users': active_users_hour,
                    'metrics': hourly_metrics
                },
                'daily': {
                    'active_users': active_users_day,
                    'metrics': daily_metrics
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            return {}
    
    async def track_page_view(self, user_id: Optional[int], session_id: str, 
                            page_url: str, referrer: str = None, 
                            user_agent: str = None, ip_address: str = None):
        """Convenience method to track page views"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            event_type=EventType.PAGE_VIEW,
            event_category=EventCategory.USER_BEHAVIOR,
            properties={'page_url': page_url},
            timestamp=datetime.utcnow(),
            page_url=page_url,
            referrer=referrer,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        return await self.track_event(event)
    
    async def track_profile_interaction(self, viewer_id: int, viewed_id: int, 
                                      interaction_type: str, compatibility_score: float = None,
                                      session_id: str = None):
        """Track profile viewing and interactions"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            user_id=viewer_id,
            session_id=session_id or str(uuid.uuid4()),
            event_type=EventType(f"profile_{interaction_type}"),
            event_category=EventCategory.MATCHING,
            properties={
                'viewed_user_id': viewed_id,
                'interaction_type': interaction_type,
                'compatibility_score': compatibility_score
            },
            timestamp=datetime.utcnow()
        )
        
        # Also store in specific table for profile interactions
        await self._store_profile_interaction(viewer_id, viewed_id, interaction_type, 
                                            compatibility_score, datetime.utcnow())
        
        return await self.track_event(event)
    
    async def _store_profile_interaction(self, viewer_id: int, viewed_id: int, 
                                       interaction_type: str, compatibility_score: float,
                                       timestamp: datetime):
        """Store profile interaction in dedicated ClickHouse table"""
        try:
            interaction_data = {
                'interaction_id': str(uuid.uuid4()),
                'viewer_user_id': viewer_id,
                'viewed_user_id': viewed_id,
                'interaction_type': interaction_type,
                'from_recommendation': True,  # This would be determined by context
                'compatibility_score': compatibility_score or 0.0,
                'interaction_duration': 0,  # This would be tracked separately
                'timestamp': timestamp,
                'date': timestamp.date()
            }
            
            self.clickhouse.execute(
                "INSERT INTO profile_interactions VALUES",
                [interaction_data]
            )
            
        except Exception as e:
            logger.error(f"Failed to store profile interaction: {e}")
    
    async def track_match_created(self, user1_id: int, user2_id: int, 
                                match_type: str, compatibility_score: float,
                                algorithm_version: str = "v1.0"):
        """Track when a match is created"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            user_id=user1_id,
            session_id=str(uuid.uuid4()),
            event_type=EventType.MATCH_CREATED,
            event_category=EventCategory.MATCHING,
            properties={
                'user2_id': user2_id,
                'match_type': match_type,
                'compatibility_score': compatibility_score,
                'algorithm_version': algorithm_version
            },
            timestamp=datetime.utcnow()
        )
        
        # Store in matching events table
        await self._store_matching_event(user1_id, user2_id, match_type, 
                                       compatibility_score, algorithm_version)
        
        return await self.track_event(event)
    
    async def _store_matching_event(self, user1_id: int, user2_id: int, 
                                  match_type: str, compatibility_score: float,
                                  algorithm_version: str):
        """Store matching event in dedicated table"""
        try:
            match_data = {
                'match_id': str(uuid.uuid4()),
                'user1_id': user1_id,
                'user2_id': user2_id,
                'match_type': match_type,
                'compatibility_score': compatibility_score,
                'algorithm_version': algorithm_version,
                'conversation_started': False,
                'first_message_time': None,
                'conversation_length': 0,
                'date_planned': False,
                'date_completed': False,
                'match_dissolved': False,
                'dissolution_reason': '',
                'timestamp': datetime.utcnow(),
                'date': datetime.utcnow().date()
            }
            
            self.clickhouse.execute(
                "INSERT INTO matching_events VALUES",
                [match_data]
            )
            
        except Exception as e:
            logger.error(f"Failed to store matching event: {e}")
    
    async def track_revelation_event(self, user_id: int, match_id: int, 
                                   revelation_day: int, revelation_type: str,
                                   content_length: int):
        """Track revelation sharing events"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            event_type=EventType.REVELATION_CREATED,
            event_category=EventCategory.REVELATION,
            properties={
                'match_id': match_id,
                'revelation_day': revelation_day,
                'revelation_type': revelation_type,
                'content_length': content_length
            },
            timestamp=datetime.utcnow()
        )
        
        # Store in revelations table
        await self._store_revelation_event(user_id, match_id, revelation_day, 
                                         revelation_type, content_length)
        
        return await self.track_event(event)
    
    async def _store_revelation_event(self, user_id: int, match_id: int, 
                                    revelation_day: int, revelation_type: str,
                                    content_length: int):
        """Store revelation event in dedicated table"""
        try:
            revelation_data = {
                'revelation_id': str(uuid.uuid4()),
                'user_id': user_id,
                'match_id': match_id,
                'revelation_day': revelation_day,
                'revelation_type': revelation_type,
                'content_length': content_length,
                'response_received': False,
                'response_time_hours': None,
                'rating': None,
                'timestamp': datetime.utcnow(),
                'date': datetime.utcnow().date()
            }
            
            self.clickhouse.execute(
                "INSERT INTO revelation_events VALUES",
                [revelation_data]
            )
            
        except Exception as e:
            logger.error(f"Failed to store revelation event: {e}")
    
    async def get_user_journey_metrics(self, user_id: int) -> Dict:
        """Get comprehensive user journey analytics"""
        try:
            # Get user's event timeline
            events_query = """
            SELECT 
                event_type,
                event_category,
                properties,
                timestamp,
                date
            FROM user_events 
            WHERE user_id = %s 
            ORDER BY timestamp ASC
            LIMIT 1000
            """
            
            events = self.clickhouse.execute(events_query, [user_id])
            
            # Calculate journey metrics
            journey_metrics = {
                'user_id': user_id,
                'total_events': len(events),
                'first_seen': events[0][3] if events else None,
                'last_seen': events[-1][3] if events else None,
                'days_active': len(set(event[4] for event in events)),
                'event_categories': {},
                'conversion_funnel': await self._calculate_conversion_funnel(user_id),
                'engagement_score': await self._calculate_engagement_score(user_id)
            }
            
            # Count events by category
            for event in events:
                category = event[1]
                if category not in journey_metrics['event_categories']:
                    journey_metrics['event_categories'][category] = 0
                journey_metrics['event_categories'][category] += 1
            
            return journey_metrics
            
        except Exception as e:
            logger.error(f"Failed to get user journey metrics: {e}")
            return {}
    
    async def _calculate_conversion_funnel(self, user_id: int) -> Dict:
        """Calculate user conversion funnel"""
        funnel_steps = [
            'register',
            'onboarding_completed', 
            'first_profile_view',
            'first_like',
            'first_match',
            'first_message',
            'first_revelation',
            'photo_revealed',
            'subscription_started'
        ]
        
        funnel_data = {}
        
        for step in funnel_steps:
            query = """
            SELECT min(timestamp) as first_time
            FROM user_events 
            WHERE user_id = %s AND event_type = %s
            """
            
            result = self.clickhouse.execute(query, [user_id, step])
            funnel_data[step] = result[0][0] if result and result[0][0] else None
        
        return funnel_data
    
    async def _calculate_engagement_score(self, user_id: int) -> float:
        """Calculate user engagement score based on recent activity"""
        try:
            # Get activity in last 7 days
            query = """
            SELECT 
                count(*) as total_events,
                uniq(date) as active_days,
                countIf(event_category = 'matching') as matching_events,
                countIf(event_category = 'messaging') as messaging_events,
                countIf(event_category = 'revelation') as revelation_events
            FROM user_events 
            WHERE user_id = %s 
            AND date >= today() - 7
            """
            
            result = self.clickhouse.execute(query, [user_id])
            
            if not result:
                return 0.0
            
            total_events, active_days, matching_events, messaging_events, revelation_events = result[0]
            
            # Calculate engagement score (0-100)
            base_score = min(total_events * 2, 40)  # Up to 40 points for activity
            consistency_score = active_days * 5      # Up to 35 points for consistency
            interaction_score = (matching_events + messaging_events + revelation_events) * 1  # Up to 25 points
            
            return min(base_score + consistency_score + interaction_score, 100.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate engagement score: {e}")
            return 0.0

# Helper functions for middleware integration
async def track_request_event(user_id: Optional[int], session_id: str, 
                            request_path: str, request_method: str,
                            analytics_service: AnalyticsService):
    """Track API request as analytics event"""
    event = AnalyticsEvent(
        event_id=str(uuid.uuid4()),
        user_id=user_id,
        session_id=session_id,
        event_type=EventType.PAGE_VIEW,
        event_category=EventCategory.USER_BEHAVIOR,
        properties={
            'request_path': request_path,
            'request_method': request_method
        },
        timestamp=datetime.utcnow(),
        page_url=request_path
    )
    
    return await analytics_service.track_event(event)