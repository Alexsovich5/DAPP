# Analytics Middleware for Dinner First
# Automatic event tracking for user behavior analysis

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, Any
import time
import uuid
import logging
from datetime import datetime

from app.services.analytics_service import analytics_service
from app.models.soul_analytics import AnalyticsEventType

logger = logging.getLogger(__name__)

class AnalyticsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track user behavior and API usage
    """
    
    def __init__(self, app, analytics_service):
        super().__init__(app)
        self.analytics_service = analytics_service
        
        # Track specific endpoints that should generate events
        self.tracked_endpoints = {
            # Authentication endpoints
            "/api/v1/auth/login": AnalyticsEventType.LOGIN,
            "/api/v1/auth/logout": AnalyticsEventType.LOGOUT,
            "/api/v1/auth/register": AnalyticsEventType.REGISTER,
            
            # Profile endpoints
            "/api/v1/profiles": AnalyticsEventType.PROFILE_EDIT,
            "/api/v1/profiles/me": AnalyticsEventType.PROFILE_VIEW,
            
            # Matching endpoints
            "/api/v1/matches": AnalyticsEventType.SWIPE_ACTION,
            "/api/v1/connections/discover": AnalyticsEventType.DISCOVER_VIEWED,
            "/api/v1/connections/initiate": AnalyticsEventType.CONNECTION_INITIATED,
            
            # Messaging endpoints
            "/api/v1/messages": AnalyticsEventType.MESSAGE_SENT,
            
            # Revelation endpoints
            "/api/v1/revelations/create": AnalyticsEventType.REVELATION_SHARED,
            
            # Safety endpoints
            "/api/v1/safety/report": AnalyticsEventType.USER_REPORTED,
            "/api/v1/safety/block": AnalyticsEventType.USER_BLOCKED,
        }
    
    async def dispatch(self, request: Request, call_next):
        # Start timing the request
        start_time = time.time()
        
        # Extract user information
        user_id = self._extract_user_id(request)
        session_id = self._extract_session_id(request)
        
        # Process the request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Track the event asynchronously
        try:
            await self._track_request_event(
                request, response, user_id, session_id, process_time
            )
        except Exception as e:
            logger.error(f"Failed to track analytics event: {e}")
        
        # Add response headers for tracking
        response.headers["X-Response-Time"] = str(process_time)
        response.headers["X-Request-ID"] = session_id
        
        return response
    
    def _extract_user_id(self, request: Request) -> Optional[int]:
        """Extract user ID from request context"""
        try:
            # Check for authenticated user in request state
            if hasattr(request.state, 'current_user'):
                return request.state.current_user.id
            
            # Check for user ID in headers (for API clients)
            user_id_header = request.headers.get('X-User-ID')
            if user_id_header:
                return int(user_id_header)
                
        except (AttributeError, ValueError, TypeError):
            pass
        
        return None
    
    def _extract_session_id(self, request: Request) -> str:
        """Extract or generate session ID"""
        # Check for existing session ID in headers
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            return session_id
        
        # Check for session ID in cookies
        session_id = request.cookies.get('session_id')
        if session_id:
            return session_id
        
        # Generate new session ID
        return str(uuid.uuid4())
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first (for load balancers)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return 'unknown'
    
    def _determine_event_type(self, request: Request, response: Response) -> Optional[AnalyticsEventType]:
        """Determine the event type based on request path and method"""
        path = request.url.path
        method = request.method
        
        # Check exact path matches first
        if path in self.tracked_endpoints:
            return self.tracked_endpoints[path]
        
        # Pattern matching for dynamic paths
        if method == "GET":
            if "/api/v1/profiles/" in path and path != "/api/v1/profiles/me":
                return AnalyticsEventType.PROFILE_VIEW
            elif "/api/v1/messages/" in path:
                return AnalyticsEventType.MESSAGE_READ
            elif "/api/v1/revelations/timeline/" in path:
                return AnalyticsEventType.REVELATION_VIEWED
        
        elif method == "POST":
            if "/api/v1/matches" in path:
                return AnalyticsEventType.SWIPE_ACTION
            elif "/api/v1/messages/" in path:
                return AnalyticsEventType.MESSAGE_SENT
            elif "/api/v1/photos/upload" in path:
                return AnalyticsEventType.PHOTO_UPLOAD
        
        elif method == "PUT":
            if "/api/v1/matches/" in path:
                return AnalyticsEventType.CONNECTION_INITIATED
            elif "/api/v1/revelations/" in path and "/consent" in path:
                return AnalyticsEventType.PHOTO_CONSENT_GIVEN
        
        return None
    
    def _determine_event_category(self, event_type: AnalyticsEventType) -> str:
        """Determine event category based on event type"""
        category_mapping = {
            AnalyticsEventType.LOGIN: "authentication",
            AnalyticsEventType.LOGOUT: "authentication",
            AnalyticsEventType.REGISTER: "authentication",
            
            AnalyticsEventType.PROFILE_VIEW: "profile_management",
            AnalyticsEventType.PROFILE_EDIT: "profile_management",
            AnalyticsEventType.PHOTO_UPLOAD: "profile_management",
            
            AnalyticsEventType.SWIPE_ACTION: "matching",
            AnalyticsEventType.CONNECTION_INITIATED: "matching",
            AnalyticsEventType.DISCOVER_VIEWED: "matching",
            
            AnalyticsEventType.MESSAGE_SENT: "messaging",
            AnalyticsEventType.MESSAGE_READ: "messaging",
            
            AnalyticsEventType.REVELATION_SHARED: "revelation",
            AnalyticsEventType.REVELATION_VIEWED: "revelation",
            AnalyticsEventType.PHOTO_CONSENT_GIVEN: "revelation",
            
            AnalyticsEventType.USER_REPORTED: "safety",
            AnalyticsEventType.USER_BLOCKED: "safety",
        }
        
        return category_mapping.get(event_type, "user_behavior")
    
    async def _track_request_event(
        self, 
        request: Request, 
        response: Response, 
        user_id: Optional[int], 
        session_id: str, 
        process_time: float
    ):
        """Track request as analytics event"""
        
        # Determine if this request should be tracked
        event_type = self._determine_event_type(request, response)
        
        # Always track page views for GET requests to main routes
        if not event_type and request.method == "GET" and response.status_code == 200:
            if any(pattern in request.url.path for pattern in ['/discover', '/matches', '/messages', '/profile']):
                event_type = AnalyticsEventType.PAGE_VIEW
        
        # Skip tracking if no relevant event type
        if not event_type:
            return
        
        # Extract additional properties
        properties = {
            'http_method': request.method,
            'status_code': response.status_code,
            'response_time_ms': round(process_time * 1000, 2),
            'user_agent': request.headers.get('User-Agent', ''),
            'referer': request.headers.get('Referer', ''),
        }
        
        # Add request-specific properties
        if request.method == "POST" and hasattr(request, '_json'):
            # Add payload size for POST requests
            properties['payload_size'] = len(str(request._json)) if request._json else 0
        
        # Track the event using our analytics service
        await self.analytics_service.track_user_event(
            user_id=user_id,
            event_type=event_type,
            event_data={
                "session_id": session_id,
                "properties": properties,
                "page_url": str(request.url),
                "referrer": request.headers.get('Referer'),
                "user_agent": request.headers.get('User-Agent'),
                "ip_address": self._get_client_ip(request)
            },
            db=None,  # Would need to pass db session
            session_id=session_id
        )

class PerformanceTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API performance metrics
    """
    
    def __init__(self, app, analytics_service):
        super().__init__(app)
        self.analytics_service = analytics_service
        
        # Define slow endpoint thresholds (in seconds)
        self.slow_thresholds = {
            '/api/v1/connections/discover': 2.0,  # Matching algorithms
            '/api/v1/profiles': 1.0,              # Profile operations
            '/api/v1/messages': 0.5,              # Messaging
            'default': 1.0                        # Default threshold
        }
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Track slow requests
        await self._track_performance_metrics(request, response, process_time)
        
        return response
    
    async def _track_performance_metrics(
        self, 
        request: Request, 
        response: Response, 
        process_time: float
    ):
        """Track performance metrics for API endpoints"""
        
        path = request.url.path
        
        # Determine threshold for this endpoint
        threshold = self.slow_thresholds.get(path, self.slow_thresholds['default'])
        
        # Track slow requests
        if process_time > threshold:
            await self._track_slow_request(request, response, process_time, threshold)
        
        # Track error responses
        if response.status_code >= 400:
            await self._track_error_response(request, response, process_time)
    
    async def _track_slow_request(
        self, 
        request: Request, 
        response: Response, 
        process_time: float, 
        threshold: float
    ):
        """Track slow API requests"""
        
        user_id = self._extract_user_id(request)
        session_id = str(uuid.uuid4())
        
        # Track slow request as performance event
        await self.analytics_service.track_system_performance(
            metric_name="slow_request",
            value=process_time * 1000,  # Convert to milliseconds
            component=request.url.path,
            db=None  # Would need to pass db session
        )
    
    async def _track_error_response(
        self, 
        request: Request, 
        response: Response, 
        process_time: float
    ):
        """Track API error responses"""
        
        user_id = self._extract_user_id(request)
        session_id = str(uuid.uuid4())
        
        # Track error response as system metric
        await self.analytics_service.track_system_performance(
            metric_name=f"error_{response.status_code}",
            value=process_time * 1000,  # Convert to milliseconds
            component=request.url.path,
            db=None  # Would need to pass db session
        )
    
    def _extract_user_id(self, request: Request) -> Optional[int]:
        """Extract user ID from request context"""
        try:
            if hasattr(request.state, 'current_user'):
                return request.state.current_user.id
        except (AttributeError, TypeError):
            pass
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return 'unknown'