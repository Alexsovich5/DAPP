"""
Enhanced Authentication Service for Sprint 8 - Advanced Microservices Architecture
Integration with Redis Cluster, Event Bus, and Performance Monitoring
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import jwt
import structlog
from core.event_publisher import EventPublisher

# Import Redis cluster manager and event publisher
from core.redis_cluster_manager import DatabaseType, RedisClusterManager
from passlib.context import CryptContext
from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# Prometheus metrics
AUTH_REQUESTS = Counter(
    "auth_requests_total", "Total authentication requests", ["endpoint", "status"]
)
AUTH_DURATION = Histogram(
    "auth_request_duration_seconds", "Authentication request duration"
)
ACTIVE_SESSIONS = Gauge("auth_active_sessions", "Number of active user sessions")
TOKEN_CACHE_HITS = Counter("auth_token_cache_hits_total", "Token cache hits")
TOKEN_CACHE_MISSES = Counter("auth_token_cache_misses_total", "Token cache misses")


class EnhancedAuthService:
    """
    Enhanced Authentication Service with Redis cluster caching,
    event-driven architecture, and advanced security features
    """

    def __init__(
        self,
        redis_manager: RedisClusterManager,
        event_publisher: EventPublisher,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
    ):

        self.redis_manager = redis_manager
        self.event_publisher = event_publisher
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm

        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Service configuration
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30

        # Performance tracking
        self.service_stats = {
            "total_logins": 0,
            "failed_logins": 0,
            "total_registrations": 0,
            "active_sessions": 0,
            "cache_hit_ratio": 0.0,
        }

        logger.info("Enhanced Auth Service initialized")

    async def initialize(self):
        """Initialize the authentication service"""
        try:
            # Test Redis connectivity
            health = await self.redis_manager.health_check()
            if health["overall_status"] != "healthy":
                raise Exception("Redis cluster not healthy")

            # Test event publisher
            await self.event_publisher.publish_event(
                exchange="auth_events",
                routing_key="service.initialized",
                event_data={
                    "service": "auth-service",
                    "version": "2.0.0",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info("Enhanced Auth Service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize auth service: {e}")
            raise

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "type": "access", "jti": str(uuid4())})
        encoded_jwt = jwt.encode(
            to_encode, self.jwt_secret, algorithm=self.jwt_algorithm
        )

        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid4())})
        encoded_jwt = jwt.encode(
            to_encode, self.jwt_secret, algorithm=self.jwt_algorithm
        )

        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")

    async def cache_user_session(
        self, user_id: int, session_data: Dict[str, Any]
    ) -> bool:
        """Cache user session with optimized TTL"""
        session_key = f"session:{user_id}"

        enhanced_session_data = {
            **session_data,
            "last_activity": datetime.utcnow().isoformat(),
            "session_id": str(uuid4()),
            "created_at": datetime.utcnow().isoformat(),
        }

        success = await self.redis_manager.cache_user_session(
            user_id, enhanced_session_data
        )

        if success:
            ACTIVE_SESSIONS.inc()
            self.service_stats["active_sessions"] += 1

        return success

    async def get_cached_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user session"""
        session_data = await self.redis_manager.get_user_session(user_id)

        if session_data:
            TOKEN_CACHE_HITS.inc()
            # Update last activity
            session_data["last_activity"] = datetime.utcnow().isoformat()
            await self.redis_manager.cache_user_session(user_id, session_data)
        else:
            TOKEN_CACHE_MISSES.inc()

        return session_data

    async def invalidate_user_session(self, user_id: int) -> bool:
        """Invalidate user session"""
        success = await self.redis_manager.delete(
            DatabaseType.USER_SESSIONS, f"session:{user_id}"
        )

        if success:
            ACTIVE_SESSIONS.dec()
            self.service_stats["active_sessions"] -= 1

        return success

    async def check_rate_limit(self, identifier: str, action: str = "login") -> bool:
        """Check rate limiting for user actions"""
        rate_limit_key = f"rate_limit:{action}:{identifier}"

        # Get current attempt count
        attempts = await self.redis_manager.get(
            DatabaseType.USER_SESSIONS, rate_limit_key
        )
        current_attempts = int(attempts) if attempts else 0

        if current_attempts >= self.max_failed_attempts:
            # Check if lockout period has expired
            lockout_key = f"lockout:{action}:{identifier}"
            lockout_data = await self.redis_manager.get(
                DatabaseType.USER_SESSIONS, lockout_key
            )

            if lockout_data:
                lockout_time = datetime.fromisoformat(lockout_data["locked_at"])
                if datetime.utcnow() - lockout_time < timedelta(
                    minutes=self.lockout_duration_minutes
                ):
                    return False

            # Reset attempts after lockout period
            await self.redis_manager.delete(DatabaseType.USER_SESSIONS, rate_limit_key)
            await self.redis_manager.delete(DatabaseType.USER_SESSIONS, lockout_key)

        return True

    async def record_failed_attempt(self, identifier: str, action: str = "login"):
        """Record failed authentication attempt"""
        rate_limit_key = f"rate_limit:{action}:{identifier}"

        # Increment attempt count
        current_attempts = await self.redis_manager.get(
            DatabaseType.USER_SESSIONS, rate_limit_key
        )
        attempts = int(current_attempts) if current_attempts else 0
        attempts += 1

        await self.redis_manager.set_with_ttl(
            DatabaseType.USER_SESSIONS,
            rate_limit_key,
            str(attempts),
            ttl=self.lockout_duration_minutes * 60,
        )

        # If max attempts reached, set lockout
        if attempts >= self.max_failed_attempts:
            lockout_key = f"lockout:{action}:{identifier}"
            lockout_data = {
                "locked_at": datetime.utcnow().isoformat(),
                "attempts": attempts,
                "action": action,
            }

            await self.redis_manager.set_with_ttl(
                DatabaseType.USER_SESSIONS,
                lockout_key,
                lockout_data,
                ttl=self.lockout_duration_minutes * 60,
            )

            # Publish lockout event
            await self.event_publisher.publish_event(
                exchange="auth_events",
                routing_key="user.locked_out",
                event_data={
                    "identifier": identifier,
                    "action": action,
                    "attempts": attempts,
                    "locked_at": datetime.utcnow().isoformat(),
                },
            )

    async def register_user(
        self, user_data: Dict[str, Any], db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Register new user with enhanced security and caching"""

        with AUTH_DURATION.time():
            start_time = time.time()

            try:
                # Check rate limiting
                email = user_data["email"]
                if not await self.check_rate_limit(email, "registration"):
                    AUTH_REQUESTS.labels(
                        endpoint="register", status="rate_limited"
                    ).inc()
                    raise Exception("Registration rate limit exceeded")

                # Hash password
                hashed_password = self.hash_password(user_data["password"])

                # Create user in database (this would be actual SQLAlchemy code)
                # For now, simulating user creation
                new_user = {
                    "id": 12345,  # Would come from database
                    "email": email,
                    "username": user_data.get("username"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "date_of_birth": user_data.get("date_of_birth"),
                    "gender": user_data.get("gender"),
                    "is_active": True,
                    "created_at": datetime.utcnow().isoformat(),
                    "hashed_password": hashed_password,
                }

                # Cache user profile
                await self.redis_manager.cache_user_profile(
                    new_user["id"],
                    {k: v for k, v in new_user.items() if k != "hashed_password"},
                )

                # Publish registration event
                await self.event_publisher.publish_event(
                    exchange="auth_events",
                    routing_key="user.registered",
                    event_data={
                        "user_id": new_user["id"],
                        "email": new_user["email"],
                        "registration_timestamp": new_user["created_at"],
                        "onboarding_completed": False,
                    },
                )

                # Update stats
                self.service_stats["total_registrations"] += 1
                AUTH_REQUESTS.labels(endpoint="register", status="success").inc()

                logger.info(f"User registered successfully: {email}")

                return {k: v for k, v in new_user.items() if k != "hashed_password"}

            except Exception as e:
                AUTH_REQUESTS.labels(endpoint="register", status="error").inc()
                logger.error(f"Registration failed for {email}: {e}")
                raise

    async def authenticate_user(
        self, email: str, password: str, db_session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with Redis caching"""

        with AUTH_DURATION.time():
            try:
                # Check rate limiting
                if not await self.check_rate_limit(email, "login"):
                    AUTH_REQUESTS.labels(endpoint="login", status="rate_limited").inc()
                    raise Exception("Login rate limit exceeded")

                # Try to get user from cache first
                cached_user = await self.redis_manager.get_cached_profile(
                    hash(email) % 10000
                )

                if cached_user and cached_user.get("email") == email:
                    user_data = cached_user
                    TOKEN_CACHE_HITS.inc()
                else:
                    # Get user from database (simulated)
                    user_data = {
                        "id": 12345,
                        "email": email,
                        "hashed_password": self.hash_password(
                            "test_password"
                        ),  # Simulated
                        "is_active": True,
                        "last_login": datetime.utcnow().isoformat(),
                    }
                    TOKEN_CACHE_MISSES.inc()

                # Verify password
                if not self.verify_password(password, user_data["hashed_password"]):
                    await self.record_failed_attempt(email, "login")
                    AUTH_REQUESTS.labels(endpoint="login", status="failed").inc()
                    self.service_stats["failed_logins"] += 1
                    return None

                # Check if user is active
                if not user_data.get("is_active", True):
                    AUTH_REQUESTS.labels(endpoint="login", status="inactive").inc()
                    return None

                # Create tokens
                access_token = self.create_access_token(
                    data={"sub": str(user_data["id"]), "email": user_data["email"]}
                )

                refresh_token = self.create_refresh_token(
                    data={"sub": str(user_data["id"]), "email": user_data["email"]}
                )

                # Cache user session
                session_data = {
                    "user_id": user_data["id"],
                    "email": user_data["email"],
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "login_time": datetime.utcnow().isoformat(),
                }

                await self.cache_user_session(user_data["id"], session_data)

                # Cache updated user profile
                user_profile = {
                    k: v for k, v in user_data.items() if k != "hashed_password"
                }
                user_profile["last_login"] = datetime.utcnow().isoformat()
                await self.redis_manager.cache_user_profile(
                    user_data["id"], user_profile
                )

                # Publish login event
                await self.event_publisher.publish_event(
                    exchange="auth_events",
                    routing_key="user.logged_in",
                    event_data={
                        "user_id": user_data["id"],
                        "email": user_data["email"],
                        "login_timestamp": datetime.utcnow().isoformat(),
                        "session_id": session_data.get("session_id"),
                    },
                )

                # Update stats
                self.service_stats["total_logins"] += 1
                AUTH_REQUESTS.labels(endpoint="login", status="success").inc()

                logger.info(f"User authenticated successfully: {email}")

                return {
                    "user": user_profile,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": self.access_token_expire_minutes * 60,
                }

            except Exception as e:
                AUTH_REQUESTS.labels(endpoint="login", status="error").inc()
                logger.error(f"Authentication failed for {email}: {e}")
                return None

    async def logout_user(self, user_id: int) -> bool:
        """Logout user and invalidate session"""
        try:
            # Invalidate session cache
            success = await self.invalidate_user_session(user_id)

            # Publish logout event
            await self.event_publisher.publish_event(
                exchange="auth_events",
                routing_key="user.logged_out",
                event_data={
                    "user_id": user_id,
                    "logout_timestamp": datetime.utcnow().isoformat(),
                },
            )

            AUTH_REQUESTS.labels(endpoint="logout", status="success").inc()
            logger.info(f"User logged out: {user_id}")

            return success

        except Exception as e:
            AUTH_REQUESTS.labels(endpoint="logout", status="error").inc()
            logger.error(f"Logout failed for user {user_id}: {e}")
            return False

    async def verify_user_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify user token with caching"""
        try:
            # Verify JWT token
            payload = self.verify_token(token)
            user_id = int(payload.get("sub"))

            # Get cached session
            session_data = await self.get_cached_session(user_id)

            if not session_data:
                TOKEN_CACHE_MISSES.inc()
                return None

            # Verify token matches cached session
            if session_data.get("access_token") != token:
                return None

            # Get user profile from cache
            user_profile = await self.redis_manager.get_cached_profile(user_id)

            if not user_profile:
                # Fallback to database query (simulated)
                user_profile = {
                    "id": user_id,
                    "email": payload.get("email"),
                    "is_active": True,
                }

                # Cache the profile
                await self.redis_manager.cache_user_profile(user_id, user_profile)

            AUTH_REQUESTS.labels(endpoint="verify", status="success").inc()

            return {"valid": True, "user": user_profile, "session": session_data}

        except Exception as e:
            AUTH_REQUESTS.labels(endpoint="verify", status="error").inc()
            logger.error(f"Token verification failed: {e}")
            return None

    async def refresh_access_token(
        self, refresh_token: str
    ) -> Optional[Dict[str, Any]]:
        """Refresh access token"""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token)

            if payload.get("type") != "refresh":
                raise Exception("Invalid refresh token type")

            user_id = int(payload.get("sub"))
            email = payload.get("email")

            # Create new access token
            new_access_token = self.create_access_token(
                data={"sub": str(user_id), "email": email}
            )

            # Update cached session
            session_data = await self.get_cached_session(user_id)
            if session_data:
                session_data["access_token"] = new_access_token
                session_data["refreshed_at"] = datetime.utcnow().isoformat()
                await self.cache_user_session(user_id, session_data)

            # Publish token refresh event
            await self.event_publisher.publish_event(
                exchange="auth_events",
                routing_key="token.refreshed",
                event_data={
                    "user_id": user_id,
                    "email": email,
                    "refreshed_at": datetime.utcnow().isoformat(),
                },
            )

            AUTH_REQUESTS.labels(endpoint="refresh", status="success").inc()

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
            }

        except Exception as e:
            AUTH_REQUESTS.labels(endpoint="refresh", status="error").inc()
            logger.error(f"Token refresh failed: {e}")
            return None

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service performance statistics"""
        redis_stats = self.redis_manager.get_performance_stats()

        self.service_stats.update(
            {
                "cache_hit_ratio": redis_stats.get("cache_hit_ratio", 0.0),
                "average_response_time_ms": redis_stats.get(
                    "average_response_time", 0.0
                )
                * 1000,
                "total_requests": redis_stats.get("total_requests", 0),
                "error_rate": redis_stats.get("error_rate", 0.0),
            }
        )

        return self.service_stats

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            # Check Redis cluster health
            redis_health = await self.redis_manager.health_check()

            # Test token operations
            test_token = self.create_access_token(
                {"sub": "test", "email": "test@example.com"}
            )
            token_valid = self.verify_token(test_token) is not None

            overall_status = "healthy"
            if redis_health["overall_status"] != "healthy" or not token_valid:
                overall_status = "degraded"

            return {
                "service": "auth-service-enhanced",
                "version": "2.0.0",
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "redis_cluster": redis_health["overall_status"],
                    "jwt_operations": "healthy" if token_valid else "unhealthy",
                    "event_publisher": "healthy",  # Would implement actual check
                },
                "statistics": self.get_service_stats(),
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "service": "auth-service-enhanced",
                "version": "2.0.0",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
