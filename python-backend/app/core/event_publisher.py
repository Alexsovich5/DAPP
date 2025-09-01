"""
Event Publisher for Sprint 8 - Advanced Microservices Architecture
RabbitMQ-based event bus with topic exchanges and event schemas
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aio_pika
import pika
import structlog
from aio_pika import DeliveryMode, ExchangeType, Message
from aio_pika.exceptions import AMQPException
from prometheus_client import Counter, Histogram

logger = structlog.get_logger(__name__)

# Prometheus metrics
EVENTS_PUBLISHED = Counter('events_published_total', 'Total events published', ['exchange', 'routing_key', 'status'])
EVENT_PUBLISH_DURATION = Histogram('event_publish_duration_seconds', 'Time spent publishing events')
EVENT_PROCESSING_ERRORS = Counter('event_processing_errors_total', 'Total event processing errors', ['exchange', 'error_type'])


class EventExchange(Enum):
    """Event exchange types"""
    USER_EVENTS = "user_events"
    MATCHING_EVENTS = "matching_events"
    MESSAGING_EVENTS = "messaging_events"
    SENTIMENT_EVENTS = "sentiment_events"
    ANALYTICS_EVENTS = "analytics_events"
    AUTH_EVENTS = "auth_events"
    SYSTEM_EVENTS = "system_events"


class EventType(Enum):
    """Event type definitions with routing keys"""
    # User events
    USER_REGISTERED = "user.registered"
    USER_PROFILE_UPDATED = "user.profile.updated"
    USER_DEACTIVATED = "user.deactivated"
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"

    # Matching events
    MATCH_CREATED = "match.created"
    MATCH_ACCEPTED = "match.accepted"
    MATCH_REJECTED = "match.rejected"
    MATCH_INTERACTION = "match.interaction"

    # Messaging events
    MESSAGE_SENT = "message.sent"
    MESSAGE_DELIVERED = "message.delivered"
    MESSAGE_READ = "message.read"

    # Sentiment events
    SENTIMENT_ANALYZED = "sentiment.analyzed"
    EMOTION_DETECTED = "emotion.detected"
    MOOD_CHANGED = "mood.changed"

    # Analytics events
    USER_ACTION_TRACKED = "analytics.user_action"
    CONVERSION_EVENT = "analytics.conversion"
    PERFORMANCE_METRIC = "analytics.performance"

    # Auth events
    TOKEN_REFRESHED = "token.refreshed"
    USER_LOCKED_OUT = "user.locked_out"
    SECURITY_VIOLATION = "security.violation"

    # System events
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    HEALTH_CHECK_FAILED = "health.check.failed"


class EventSchema:
    """Event schema validator and definitions"""

    SCHEMAS = {
        EventType.USER_REGISTERED: {
            "type": "object",
            "required": ["user_id", "email", "registration_timestamp"],
            "properties": {
                "user_id": {"type": "integer"},
                "email": {"type": "string", "format": "email"},
                "registration_timestamp": {"type": "string", "format": "date-time"},
                "onboarding_completed": {"type": "boolean"}
            }
        },

        EventType.MATCH_CREATED: {
            "type": "object",
            "required": ["match_id", "user1_id", "user2_id", "compatibility_score"],
            "properties": {
                "match_id": {"type": "integer"},
                "user1_id": {"type": "integer"},
                "user2_id": {"type": "integer"},
                "compatibility_score": {"type": "number", "minimum": 0, "maximum": 1},
                "created_timestamp": {"type": "string", "format": "date-time"}
            }
        },

        EventType.SENTIMENT_ANALYZED: {
            "type": "object",
            "required": ["user_id", "message_id", "sentiment_score"],
            "properties": {
                "user_id": {"type": "integer"},
                "message_id": {"type": "integer"},
                "sentiment_score": {"type": "number", "minimum": -1, "maximum": 1},
                "emotions": {"type": "array", "items": {"type": "string"}},
                "analysis_timestamp": {"type": "string", "format": "date-time"}
            }
        }
    }

    @classmethod
    def validate_event(cls, event_type: EventType, data: Dict[str, Any]) -> bool:
        """Validate event data against schema (simplified validation)"""
        schema = cls.SCHEMAS.get(event_type)
        if not schema:
            return True  # No schema defined, assume valid

        # Simplified validation - check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field '{field}' in {event_type.value} event")
                return False

        return True


class EventPublisher:
    """
    High-performance RabbitMQ event publisher with automatic retry,
    dead letter handling, and comprehensive monitoring
    """

    def __init__(self, connection_url: str = None, max_retries: int = 3):
        self.connection_url = connection_url or "amqp://guest:guest@localhost:5672/"
        self.max_retries = max_retries
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchanges: Dict[str, aio_pika.Exchange] = {}

        # Dead letter exchange for failed messages
        self.dlx_name = "dinner_first_dlx"

        # Performance tracking
        self.stats = {
            "total_published": 0,
            "successful_publishes": 0,
            "failed_publishes": 0,
            "average_publish_time": 0.0
        }

        logger.info("Event Publisher initialized")

    async def initialize(self):
        """Initialize RabbitMQ connection and exchanges"""
        try:
            # Create robust connection for auto-reconnection
            self.connection = await aio_pika.connect_robust(
                self.connection_url,
                loop=asyncio.get_event_loop()
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=100)

            # Create dead letter exchange
            dlx_exchange = await self.channel.declare_exchange(
                self.dlx_name,
                ExchangeType.TOPIC,
                durable=True
            )

            # Create main exchanges
            for exchange_type in EventExchange:
                exchange = await self.channel.declare_exchange(
                    exchange_type.value,
                    ExchangeType.TOPIC,
                    durable=True
                )
                self.exchanges[exchange_type.value] = exchange

                logger.info(f"Created exchange: {exchange_type.value}")

            # Create dead letter queue
            await self.channel.declare_queue(
                "dinner_first_dlq",
                durable=True,
                arguments={"x-message-ttl": 86400000}  # 24 hours TTL
            )

            logger.info("Event Publisher initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize event publisher: {e}")
            raise

    async def publish_event(self,
                           exchange: str,
                           routing_key: str,
                           event_data: Dict[str, Any],
                           event_type: Optional[EventType] = None,
                           headers: Optional[Dict[str, Any]] = None,
                           priority: int = 0,
                           expiration: Optional[int] = None) -> bool:
        """
        Publish event to RabbitMQ with enhanced features

        Args:
            exchange: Exchange name to publish to
            routing_key: Routing key for the event
            event_data: Event payload data
            event_type: Optional event type for validation
            headers: Optional message headers
            priority: Message priority (0-255)
            expiration: Message expiration in milliseconds

        Returns:
            True if published successfully, False otherwise
        """
        start_time = time.time()

        try:
            # Validate event data if event_type is provided
            if event_type and not EventSchema.validate_event(event_type, event_data):
                EVENTS_PUBLISHED.labels(exchange=exchange, routing_key=routing_key, status="validation_error").inc()
                return False

            # Ensure connection and exchange exist
            if not self.connection or self.connection.is_closed:
                await self.initialize()

            if exchange not in self.exchanges:
                logger.error(f"Unknown exchange: {exchange}")
                EVENTS_PUBLISHED.labels(exchange=exchange, routing_key=routing_key, status="unknown_exchange").inc()
                return False

            # Create message
            message_body = {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "exchange": exchange,
                "routing_key": routing_key,
                "data": event_data,
                "version": "1.0"
            }

            # Add custom headers
            message_headers = {
                "content_type": "application/json",
                "delivery_mode": 2,  # Persistent
                "priority": priority,
                **headers if headers else {}
            }

            if expiration:
                message_headers["expiration"] = str(expiration)

            # Create AMQP message
            message = Message(
                json.dumps(message_body).encode(),
                headers=message_headers,
                delivery_mode=DeliveryMode.PERSISTENT,
                priority=priority
            )

            # Publish with retry logic
            for attempt in range(self.max_retries):
                try:
                    await self.exchanges[exchange].publish(
                        message,
                        routing_key=routing_key
                    )

                    # Update metrics
                    publish_time = time.time() - start_time
                    self._update_stats(publish_time, success=True)

                    EVENTS_PUBLISHED.labels(exchange=exchange, routing_key=routing_key, status="success").inc()
                    EVENT_PUBLISH_DURATION.observe(publish_time)

                    logger.debug(f"Published event {message_body['event_id']} to {exchange}/{routing_key}")
                    return True

                except AMQPException as e:
                    logger.warning(f"Publish attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        raise

                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        except Exception as e:
            publish_time = time.time() - start_time
            self._update_stats(publish_time, success=False)

            EVENTS_PUBLISHED.labels(exchange=exchange, routing_key=routing_key, status="error").inc()
            EVENT_PROCESSING_ERRORS.labels(exchange=exchange, error_type=type(e).__name__).inc()

            logger.error(f"Failed to publish event to {exchange}/{routing_key}: {e}")
            return False

    async def publish_user_event(self, event_type: EventType, data: Dict[str, Any]) -> bool:
        """Publish user-related event"""
        return await self.publish_event(
            exchange=EventExchange.USER_EVENTS.value,
            routing_key=event_type.value,
            event_data=data,
            event_type=event_type
        )

    async def publish_matching_event(self, event_type: EventType, data: Dict[str, Any]) -> bool:
        """Publish matching-related event"""
        return await self.publish_event(
            exchange=EventExchange.MATCHING_EVENTS.value,
            routing_key=event_type.value,
            event_data=data,
            event_type=event_type
        )

    async def publish_sentiment_event(self, event_type: EventType, data: Dict[str, Any]) -> bool:
        """Publish sentiment analysis event"""
        return await self.publish_event(
            exchange=EventExchange.SENTIMENT_EVENTS.value,
            routing_key=event_type.value,
            event_data=data,
            event_type=event_type
        )

    async def publish_analytics_event(self, event_type: EventType, data: Dict[str, Any]) -> bool:
        """Publish analytics event"""
        return await self.publish_event(
            exchange=EventExchange.ANALYTICS_EVENTS.value,
            routing_key=event_type.value,
            event_data=data,
            event_type=event_type
        )

    def _update_stats(self, publish_time: float, success: bool):
        """Update internal performance statistics"""
        self.stats["total_published"] += 1

        if success:
            self.stats["successful_publishes"] += 1
        else:
            self.stats["failed_publishes"] += 1

        # Update rolling average
        current_avg = self.stats["average_publish_time"]
        total_published = self.stats["total_published"]

        self.stats["average_publish_time"] = (
            (current_avg * (total_published - 1) + publish_time) / total_published
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get publisher performance statistics"""
        stats = self.stats.copy()

        if stats["total_published"] > 0:
            stats["success_rate"] = stats["successful_publishes"] / stats["total_published"]
            stats["error_rate"] = stats["failed_publishes"] / stats["total_published"]
        else:
            stats["success_rate"] = 0.0
            stats["error_rate"] = 0.0

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Check publisher health"""
        try:
            if not self.connection or self.connection.is_closed:
                return {
                    "status": "unhealthy",
                    "error": "No connection to RabbitMQ",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Test publish to system exchange
            test_success = await self.publish_event(
                exchange=EventExchange.SYSTEM_EVENTS.value,
                routing_key="health.check",
                event_data={"test": True, "timestamp": datetime.utcnow().isoformat()}
            )

            return {
                "status": "healthy" if test_success else "degraded",
                "connection_status": "open",
                "exchanges_created": len(self.exchanges),
                "statistics": self.get_stats(),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def close(self):
        """Close publisher connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Event Publisher closed")


class BaseEventConsumer:
    """
    Base event consumer class with automatic retry, dead letter handling,
    and comprehensive error management
    """

    def __init__(self,
                 connection_url: str = None,
                 exchange_name: str = None,
                 routing_keys: List[str] = None,
                 queue_name: str = None,
                 consumer_tag: str = None):

        self.connection_url = connection_url or "amqp://guest:guest@localhost:5672/"
        self.exchange_name = exchange_name
        self.routing_keys = routing_keys or []
        self.queue_name = queue_name or f"{self.__class__.__name__.lower()}_queue"
        self.consumer_tag = consumer_tag or f"{self.__class__.__name__.lower()}_consumer"

        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None

        # Consumer stats
        self.stats = {
            "messages_processed": 0,
            "messages_failed": 0,
            "average_processing_time": 0.0
        }

        logger.info(f"Consumer {self.consumer_tag} initialized")

    async def initialize(self):
        """Initialize consumer connection and queue"""
        try:
            # Create connection
            self.connection = await aio_pika.connect_robust(self.connection_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange
            exchange = await self.channel.declare_exchange(
                self.exchange_name,
                ExchangeType.TOPIC,
                durable=True
            )

            # Declare queue with dead letter exchange
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "dinner_first_dlx",
                    "x-dead-letter-routing-key": f"dlq.{self.queue_name}"
                }
            )

            # Bind queue to routing keys
            for routing_key in self.routing_keys:
                await self.queue.bind(exchange, routing_key)
                logger.info(f"Bound queue {self.queue_name} to {self.exchange_name}/{routing_key}")

            logger.info(f"Consumer {self.consumer_tag} initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize consumer {self.consumer_tag}: {e}")
            raise

    async def process_event(self, message: aio_pika.IncomingMessage) -> bool:
        """
        Process individual event message
        Override this method in subclasses

        Args:
            message: Incoming RabbitMQ message

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            # Decode message
            message_body = json.loads(message.body.decode())

            logger.info(f"Processing event: {message_body.get('event_id')}")

            # Process the event (to be implemented in subclasses)
            await self.handle_event(message_body)

            return True

        except Exception as e:
            logger.error(f"Failed to process event: {e}")
            return False

    async def handle_event(self, event_data: Dict[str, Any]):
        """Override this method to handle specific events"""
        raise NotImplementedError("Subclasses must implement handle_event method")

    async def start_consuming(self):
        """Start consuming messages"""
        await self.initialize()

        async def message_handler(message: aio_pika.IncomingMessage):
            start_time = time.time()

            async with message.process():
                try:
                    success = await self.process_event(message)

                    processing_time = time.time() - start_time
                    self._update_stats(processing_time, success)

                    if success:
                        logger.debug(f"Successfully processed message in {processing_time:.3f}s")
                    else:
                        logger.warning("Message processing failed, will be retried or sent to DLQ")

                except Exception as e:
                    processing_time = time.time() - start_time
                    self._update_stats(processing_time, success=False)
                    logger.error(f"Message processing error: {e}")
                    raise  # Re-raise to trigger retry/DLQ

        # Start consuming
        await self.queue.consume(message_handler, consumer_tag=self.consumer_tag)
        logger.info(f"Started consuming with tag: {self.consumer_tag}")

    def _update_stats(self, processing_time: float, success: bool):
        """Update consumer statistics"""
        self.stats["messages_processed"] += 1

        if not success:
            self.stats["messages_failed"] += 1

        # Update average processing time
        current_avg = self.stats["average_processing_time"]
        total_processed = self.stats["messages_processed"]

        self.stats["average_processing_time"] = (
            (current_avg * (total_processed - 1) + processing_time) / total_processed
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics"""
        stats = self.stats.copy()

        if stats["messages_processed"] > 0:
            stats["success_rate"] = (stats["messages_processed"] - stats["messages_failed"]) / stats["messages_processed"]
            stats["error_rate"] = stats["messages_failed"] / stats["messages_processed"]
        else:
            stats["success_rate"] = 0.0
            stats["error_rate"] = 0.0

        return stats

    async def stop_consuming(self):
        """Stop consuming and close connections"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info(f"Consumer {self.consumer_tag} stopped")


# Global event publisher instance
event_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance"""
    global event_publisher
    if event_publisher is None:
        event_publisher = EventPublisher()
    return event_publisher


async def init_event_publisher(connection_url: str = None) -> EventPublisher:
    """Initialize global event publisher"""
    global event_publisher
    event_publisher = EventPublisher(connection_url)
    await event_publisher.initialize()
    return event_publisher


async def close_event_publisher():
    """Close global event publisher"""
    global event_publisher
    if event_publisher:
        await event_publisher.close()
        event_publisher = None
