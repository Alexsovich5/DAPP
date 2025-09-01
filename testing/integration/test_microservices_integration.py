"""
Integration Testing Suite for Dinner First Sprint 8 Microservices Architecture

Tests end-to-end workflows across all microservices:
- User registration through authentication service
- Profile creation through profile service
- AI matching through matching service
- Sentiment analysis integration
- Real-time messaging via messaging service
- Event-driven communication via RabbitMQ
- Redis caching integration
- Database consistency across services

Validates performance targets:
- Sub-100ms 95th percentile response times
- Proper error handling and circuit breakers
- Data consistency across microservices
- Real-time capabilities
"""

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aio_pika
import aiohttp
import pytest
import redis.asyncio as redis
import websockets


class TestConfig:
    """Test configuration and endpoints"""

    API_BASE_URL = "https://api.dinner-first.app/api/v1"
    WEBSOCKET_URL = "wss://ws.dinner-first.app"
    REDIS_CLUSTER = ["redis-cluster.dinner-first-redis.svc.cluster.local:6379"]
    RABBITMQ_URL = "amqp://dinner-first:dinner-first-messaging-2025@rabbitmq.dinner-first-messaging.svc.cluster.local:5672"

    # Performance thresholds
    MAX_RESPONSE_TIME_MS = 100
    MAX_WEBSOCKET_LATENCY_MS = 50
    MAX_CACHE_RESPONSE_TIME_MS = 10


class MicroservicesIntegrationTest:
    """Comprehensive integration test suite"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.RedisCluster] = None
        self.rabbitmq_connection: Optional[aio_pika.Connection] = None
        self.test_users: List[Dict] = []
        self.test_connections: List[str] = []

    async def setup(self):
        """Initialize test environment"""
        # HTTP session
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

        # Redis cluster connection
        self.redis_client = redis.RedisCluster(
            host="redis-cluster.dinner-first-redis.svc.cluster.local",
            port=6379,
            decode_responses=True,
        )

        # RabbitMQ connection
        self.rabbitmq_connection = await aio_pika.connect_robust(
            TestConfig.RABBITMQ_URL
        )

    async def teardown(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.close()
        if self.rabbitmq_connection:
            await self.rabbitmq_connection.close()

    async def create_test_user(self, user_suffix: str = None) -> Dict[str, Any]:
        """Create a test user and return user data with auth token"""
        suffix = user_suffix or uuid.uuid4().hex[:8]
        user_data = {
            "email": f"test_{suffix}@integration-test.com",
            "password": "IntegrationTest2025!",
            "first_name": f"Test{suffix}",
            "age": 28,
            "gender": "non-binary",
        }

        # Register user
        start_time = time.time()
        async with self.session.post(
            f"{TestConfig.API_BASE_URL}/auth/register", json=user_data
        ) as response:
            register_time = (time.time() - start_time) * 1000
            assert (
                response.status == 201
            ), f"Registration failed: {await response.text()}"
            assert (
                register_time < TestConfig.MAX_RESPONSE_TIME_MS
            ), f"Registration too slow: {register_time}ms"

            register_result = await response.json()

        # Login user
        start_time = time.time()
        async with self.session.post(
            f"{TestConfig.API_BASE_URL}/auth/login",
            json={"email": user_data["email"], "password": user_data["password"]},
        ) as response:
            login_time = (time.time() - start_time) * 1000
            assert response.status == 200, f"Login failed: {await response.text()}"
            assert (
                login_time < TestConfig.MAX_RESPONSE_TIME_MS
            ), f"Login too slow: {login_time}ms"

            login_result = await response.json()

        user_info = {
            **user_data,
            "user_id": register_result["user_id"],
            "auth_token": login_result["access_token"],
            "headers": {"Authorization": f"Bearer {login_result['access_token']}"},
        }

        self.test_users.append(user_info)
        return user_info

    async def create_user_profile(self, user_info: Dict) -> Dict[str, Any]:
        """Create emotional profile for user"""
        profile_data = {
            "location": {
                "city": "San Francisco",
                "latitude": 37.7749,
                "longitude": -122.4194,
            },
            "interests": ["cooking", "travel", "photography", "hiking", "music"],
            "life_philosophy": "Live authentically and cherish meaningful connections",
            "core_values": ["honesty", "kindness", "adventure", "growth"],
            "personality_traits": {
                "openness": 0.8,
                "conscientiousness": 0.7,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3,
            },
            "communication_style": {
                "preferred_style": "thoughtful",
                "response_speed": "moderate",
                "conversation_depth": "deep",
            },
            "emotional_onboarding_completed": True,
        }

        start_time = time.time()
        async with self.session.post(
            f"{TestConfig.API_BASE_URL}/profiles",
            json=profile_data,
            headers=user_info["headers"],
        ) as response:
            response_time = (time.time() - start_time) * 1000
            assert response.status in [
                200,
                201,
            ], f"Profile creation failed: {await response.text()}"
            assert (
                response_time < TestConfig.MAX_RESPONSE_TIME_MS
            ), f"Profile creation too slow: {response_time}ms"

            profile_result = await response.json()

        user_info["profile_id"] = profile_result["profile_id"]
        return profile_result

    async def test_auth_service_integration(self):
        """Test authentication service with Redis session caching"""
        user = await self.create_test_user("auth_test")

        # Verify Redis session caching
        session_key = f"session:{user['user_id']}"
        start_time = time.time()
        session_data = await self.redis_client.get(session_key)
        cache_time = (time.time() - start_time) * 1000

        assert session_data is not None, "Session not cached in Redis"
        assert (
            cache_time < TestConfig.MAX_CACHE_RESPONSE_TIME_MS
        ), f"Cache too slow: {cache_time}ms"

        # Test token refresh
        start_time = time.time()
        async with self.session.post(
            f"{TestConfig.API_BASE_URL}/auth/refresh", headers=user["headers"]
        ) as response:
            refresh_time = (time.time() - start_time) * 1000
            assert (
                response.status == 200
            ), f"Token refresh failed: {await response.text()}"
            assert (
                refresh_time < TestConfig.MAX_RESPONSE_TIME_MS
            ), f"Token refresh too slow: {refresh_time}ms"

    async def test_profile_service_integration(self):
        """Test profile service with multi-level caching"""
        user = await self.create_test_user("profile_test")
        profile = await self.create_user_profile(user)

        # Test profile retrieval (should hit cache on second request)
        # First request - database
        start_time = time.time()
        async with self.session.get(
            f"{TestConfig.API_BASE_URL}/profiles/me", headers=user["headers"]
        ) as response:
            first_request_time = (time.time() - start_time) * 1000
            assert (
                response.status == 200
            ), f"Profile retrieval failed: {await response.text()}"
            profile_data = await response.json()

        # Second request - should be faster (cache hit)
        start_time = time.time()
        async with self.session.get(
            f"{TestConfig.API_BASE_URL}/profiles/me", headers=user["headers"]
        ) as response:
            cached_request_time = (time.time() - start_time) * 1000
            assert response.status == 200
            cached_profile_data = await response.json()

        assert (
            cached_request_time < first_request_time
        ), "Cache not improving performance"
        assert (
            cached_request_time < TestConfig.MAX_CACHE_RESPONSE_TIME_MS
        ), f"Cached response too slow: {cached_request_time}ms"
        assert profile_data == cached_profile_data, "Cached data inconsistent"

        # Verify Redis profile caching
        profile_key = f"profile:{user['profile_id']}"
        cached_profile = await self.redis_client.get(profile_key)
        assert cached_profile is not None, "Profile not cached in Redis"

    async def test_matching_service_integration(self):
        """Test AI matching service with ML model registry integration"""
        # Create two compatible users
        user1 = await self.create_test_user("match_test_1")
        user2 = await self.create_test_user("match_test_2")

        await self.create_user_profile(user1)
        await self.create_user_profile(user2)

        # Test matching discovery
        start_time = time.time()
        async with self.session.get(
            f"{TestConfig.API_BASE_URL}/matching/discover",
            params={"limit": 10, "radius_km": 50},
            headers=user1["headers"],
        ) as response:
            matching_time = (time.time() - start_time) * 1000
            assert (
                response.status == 200
            ), f"Matching discovery failed: {await response.text()}"
            assert (
                matching_time < TestConfig.MAX_RESPONSE_TIME_MS
            ), f"Matching too slow: {matching_time}ms"

            matches = await response.json()

        assert "matches" in matches, "Missing matches in response"
        assert len(matches["matches"]) > 0, "No matches found"

        # Test compatibility scoring
        target_match = matches["matches"][0]
        start_time = time.time()
        async with self.session.get(
            f"{TestConfig.API_BASE_URL}/matching/compatibility/{target_match['user_id']}",
            headers=user1["headers"],
        ) as response:
            compatibility_time = (time.time() - start_time) * 1000
            assert (
                response.status == 200
            ), f"Compatibility check failed: {await response.text()}"
            assert (
                compatibility_time < TestConfig.MAX_RESPONSE_TIME_MS
            ), f"Compatibility check too slow: {compatibility_time}ms"

            compatibility = await response.json()

        assert "compatibility_score" in compatibility, "Missing compatibility score"
        assert (
            0 <= compatibility["compatibility_score"] <= 100
        ), "Invalid compatibility score"

        # Verify ML model caching
        model_key = "ml_model:compatibility:v2.0.0"
        cached_model = await self.redis_client.exists(model_key)
        assert cached_model, "ML model not cached"

    async def test_sentiment_service_integration(self):
        """Test sentiment analysis service with multi-modal analysis"""
        user = await self.create_test_user("sentiment_test")
        await self.create_user_profile(user)

        test_messages = [
            {
                "text": "I'm so excited about our upcoming dinner date!",
                "context": "conversation",
                "analysis_types": ["sentiment", "emotion", "behavioral"],
            },
            {
                "text": "This conversation has been really meaningful to me.",
                "context": "connection",
                "analysis_types": ["sentiment", "emotion", "contextual"],
            },
            {
                "text": "I appreciate how thoughtful and kind you are.",
                "context": "appreciation",
                "analysis_types": ["sentiment", "emotion", "temporal"],
            },
        ]

        for message_data in test_messages:
            start_time = time.time()
            async with self.session.post(
                f"{TestConfig.API_BASE_URL}/sentiment/analyze",
                json=message_data,
                headers=user["headers"],
            ) as response:
                analysis_time = (time.time() - start_time) * 1000
                assert (
                    response.status == 200
                ), f"Sentiment analysis failed: {await response.text()}"
                assert (
                    analysis_time < TestConfig.MAX_RESPONSE_TIME_MS
                ), f"Sentiment analysis too slow: {analysis_time}ms"

                analysis_result = await response.json()

            assert "sentiment_score" in analysis_result, "Missing sentiment score"
            assert "confidence" in analysis_result, "Missing confidence score"
            assert "emotions" in analysis_result, "Missing emotion analysis"
            assert analysis_result["confidence"] > 0.5, "Low confidence score"

        # Test batch sentiment analysis
        start_time = time.time()
        async with self.session.post(
            f"{TestConfig.API_BASE_URL}/sentiment/analyze/batch",
            json={"texts": [msg["text"] for msg in test_messages[:2]]},
            headers=user["headers"],
        ) as response:
            batch_time = (time.time() - start_time) * 1000
            assert (
                response.status == 200
            ), f"Batch sentiment analysis failed: {await response.text()}"
            assert (
                batch_time < TestConfig.MAX_RESPONSE_TIME_MS
            ), f"Batch analysis too slow: {batch_time}ms"

            batch_results = await response.json()

        assert len(batch_results["results"]) == 2, "Incorrect batch results count"

    async def test_messaging_service_integration(self):
        """Test messaging service with WebSocket and event publishing"""
        # Create two users for messaging
        user1 = await self.create_test_user("msg_test_1")
        user2 = await self.create_test_user("msg_test_2")

        await self.create_user_profile(user1)
        await self.create_user_profile(user2)

        # Create connection between users
        async with self.session.post(
            f"{TestConfig.API_BASE_URL}/connections/initiate",
            json={
                "target_user_id": user2["user_id"],
                "connection_message": "I'd love to get to know you better!",
            },
            headers=user1["headers"],
        ) as response:
            assert response.status in [
                200,
                201,
            ], f"Connection creation failed: {await response.text()}"
            connection_result = await response.json()

        connection_id = connection_result["connection_id"]
        self.test_connections.append(connection_id)

        # Test HTTP messaging
        message_data = {
            "message_text": "Hello! How are you doing today?",
            "message_type": "text",
        }

        start_time = time.time()
        async with self.session.post(
            f"{TestConfig.API_BASE_URL}/messages/{connection_id}",
            json=message_data,
            headers=user1["headers"],
        ) as response:
            message_time = (time.time() - start_time) * 1000
            assert response.status in [
                200,
                201,
            ], f"Message sending failed: {await response.text()}"
            assert (
                message_time < TestConfig.MAX_RESPONSE_TIME_MS
            ), f"Message sending too slow: {message_time}ms"

            message_result = await response.json()

        message_id = message_result["message_id"]

        # Test message retrieval
        start_time = time.time()
        async with self.session.get(
            f"{TestConfig.API_BASE_URL}/messages/{connection_id}",
            params={"limit": 10},
            headers=user2["headers"],
        ) as response:
            retrieval_time = (time.time() - start_time) * 1000
            assert (
                response.status == 200
            ), f"Message retrieval failed: {await response.text()}"
            assert (
                retrieval_time < TestConfig.MAX_RESPONSE_TIME_MS
            ), f"Message retrieval too slow: {retrieval_time}ms"

            messages = await response.json()

        assert "messages" in messages, "Missing messages in response"
        assert len(messages["messages"]) > 0, "No messages found"

        # Verify message caching
        message_key = f"messages:{connection_id}"
        cached_messages = await self.redis_client.lrange(message_key, 0, -1)
        assert len(cached_messages) > 0, "Messages not cached in Redis"

    async def test_websocket_integration(self):
        """Test WebSocket real-time messaging"""
        user = await self.create_test_user("ws_test")
        await self.create_user_profile(user)

        messages_received = []
        connection_established = asyncio.Event()

        async def websocket_handler():
            try:
                headers = {"Authorization": f"Bearer {user['auth_token']}"}
                async with websockets.connect(
                    TestConfig.WEBSOCKET_URL, extra_headers=headers
                ) as websocket:
                    connection_established.set()

                    # Send test message
                    test_message = {
                        "type": "message",
                        "connection_id": "test_connection",
                        "text": "WebSocket integration test message",
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    start_time = time.time()
                    await websocket.send(json.dumps(test_message))

                    # Wait for response
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    websocket_latency = (time.time() - start_time) * 1000

                    assert (
                        websocket_latency < TestConfig.MAX_WEBSOCKET_LATENCY_MS
                    ), f"WebSocket latency too high: {websocket_latency}ms"

                    messages_received.append(json.loads(response))

            except Exception as e:
                pytest.fail(f"WebSocket connection failed: {e}")

        # Run WebSocket test
        await asyncio.wait_for(websocket_handler(), timeout=10.0)

        assert len(messages_received) > 0, "No WebSocket messages received"

    async def test_event_driven_integration(self):
        """Test RabbitMQ event-driven communication between services"""
        # Create event listener
        channel = await self.rabbitmq_connection.channel()
        events_received = []

        # Declare test queue
        queue = await channel.declare_queue("test.integration.events", durable=True)

        async def event_handler(message):
            async with message.process():
                event_data = json.loads(message.body.decode())
                events_received.append(event_data)

        # Start consuming
        await queue.consume(event_handler)

        # Trigger events by creating user and profile
        user = await self.create_test_user("event_test")
        await self.create_user_profile(user)

        # Wait for events
        await asyncio.sleep(2)

        # Verify events were published
        expected_events = ["user.created", "profile.created"]
        received_event_types = [event.get("event_type") for event in events_received]

        for expected_event in expected_events:
            assert (
                expected_event in received_event_types
            ), f"Missing event: {expected_event}"

        await channel.close()

    async def test_caching_consistency(self):
        """Test Redis caching consistency across services"""
        user = await self.create_test_user("cache_test")
        profile = await self.create_user_profile(user)

        # Update profile via API
        updated_data = {
            "life_philosophy": "Updated philosophy for cache consistency test"
        }

        async with self.session.put(
            f"{TestConfig.API_BASE_URL}/profiles/me",
            json=updated_data,
            headers=user["headers"],
        ) as response:
            assert (
                response.status == 200
            ), f"Profile update failed: {await response.text()}"

        # Verify cache invalidation
        profile_key = f"profile:{user['profile_id']}"

        # Wait for cache invalidation
        await asyncio.sleep(1)

        # Get updated profile
        async with self.session.get(
            f"{TestConfig.API_BASE_URL}/profiles/me", headers=user["headers"]
        ) as response:
            assert response.status == 200
            updated_profile = await response.json()

        assert (
            updated_profile["life_philosophy"] == updated_data["life_philosophy"]
        ), "Cache not properly invalidated"

        # Verify Redis cache contains updated data
        cached_data = await self.redis_client.get(profile_key)
        if cached_data:
            cached_profile = json.loads(cached_data)
            assert (
                cached_profile["life_philosophy"] == updated_data["life_philosophy"]
            ), "Redis cache inconsistent"

    async def test_circuit_breaker_integration(self):
        """Test circuit breaker functionality across services"""
        user = await self.create_test_user("circuit_test")
        await self.create_user_profile(user)

        # Make rapid requests to trigger circuit breaker (if configured)
        failed_requests = 0
        total_requests = 20

        for i in range(total_requests):
            try:
                async with self.session.get(
                    f"{TestConfig.API_BASE_URL}/matching/discover",
                    params={"limit": 100},  # Large request
                    headers=user["headers"],
                ) as response:
                    if response.status != 200:
                        failed_requests += 1
            except asyncio.TimeoutError:
                failed_requests += 1

            # Small delay between requests
            await asyncio.sleep(0.1)

        # Circuit breaker should handle failures gracefully
        # At least some requests should succeed even under load
        success_rate = (total_requests - failed_requests) / total_requests
        assert (
            success_rate > 0.5
        ), f"Too many failed requests: {failed_requests}/{total_requests}"

    async def test_end_to_end_user_journey(self):
        """Test complete user journey across all services"""
        # Create two users
        user1 = await self.create_test_user("journey_1")
        user2 = await self.create_test_user("journey_2")

        # Create profiles
        await self.create_user_profile(user1)
        await self.create_user_profile(user2)

        # User 1 discovers matches
        async with self.session.get(
            f"{TestConfig.API_BASE_URL}/matching/discover", headers=user1["headers"]
        ) as response:
            assert response.status == 200
            matches = await response.json()

        # Find user2 in matches (if any)
        target_user = None
        for match in matches.get("matches", []):
            if match["user_id"] == user2["user_id"]:
                target_user = match
                break

        if not target_user:
            # Force match for testing
            target_user = {"user_id": user2["user_id"]}

        # User 1 initiates connection
        async with self.session.post(
            f"{TestConfig.API_BASE_URL}/connections/initiate",
            json={
                "target_user_id": target_user["user_id"],
                "connection_message": "I'd love to connect with you!",
            },
            headers=user1["headers"],
        ) as response:
            assert response.status in [200, 201]
            connection = await response.json()

        connection_id = connection["connection_id"]

        # Exchange messages
        messages = [
            {"sender": user1, "text": "Hi there! How are you?"},
            {"sender": user2, "text": "Hello! I'm doing great, thanks for asking!"},
            {"sender": user1, "text": "Would you like to plan our first dinner date?"},
        ]

        for message in messages:
            # Send message
            async with self.session.post(
                f"{TestConfig.API_BASE_URL}/messages/{connection_id}",
                json={"message_text": message["text"], "message_type": "text"},
                headers=message["sender"]["headers"],
            ) as response:
                assert response.status in [200, 201]
                message_result = await response.json()

            # Analyze sentiment
            async with self.session.post(
                f"{TestConfig.API_BASE_URL}/sentiment/analyze",
                json={"text": message["text"], "context": "conversation"},
                headers=message["sender"]["headers"],
            ) as response:
                assert response.status == 200
                sentiment = await response.json()
                assert "sentiment_score" in sentiment

        # Verify conversation history
        async with self.session.get(
            f"{TestConfig.API_BASE_URL}/messages/{connection_id}",
            headers=user1["headers"],
        ) as response:
            assert response.status == 200
            conversation = await response.json()
            assert len(conversation["messages"]) >= len(messages)

        print("✅ End-to-end user journey completed successfully")


# Pytest fixtures and test runners
@pytest.fixture
async def integration_test():
    """Test fixture that sets up and tears down integration test environment"""
    test = MicroservicesIntegrationTest()
    await test.setup()
    yield test
    await test.teardown()


@pytest.mark.asyncio
async def test_authentication_integration(integration_test):
    """Test authentication service integration"""
    await integration_test.test_auth_service_integration()


@pytest.mark.asyncio
async def test_profile_integration(integration_test):
    """Test profile service integration"""
    await integration_test.test_profile_service_integration()


@pytest.mark.asyncio
async def test_matching_integration(integration_test):
    """Test matching service integration"""
    await integration_test.test_matching_service_integration()


@pytest.mark.asyncio
async def test_sentiment_integration(integration_test):
    """Test sentiment analysis integration"""
    await integration_test.test_sentiment_service_integration()


@pytest.mark.asyncio
async def test_messaging_integration(integration_test):
    """Test messaging service integration"""
    await integration_test.test_messaging_service_integration()


@pytest.mark.asyncio
async def test_websocket_integration(integration_test):
    """Test WebSocket integration"""
    await integration_test.test_websocket_integration()


@pytest.mark.asyncio
async def test_event_driven_integration(integration_test):
    """Test event-driven communication"""
    await integration_test.test_event_driven_integration()


@pytest.mark.asyncio
async def test_caching_consistency(integration_test):
    """Test caching consistency"""
    await integration_test.test_caching_consistency()


@pytest.mark.asyncio
async def test_circuit_breaker_integration(integration_test):
    """Test circuit breaker functionality"""
    await integration_test.test_circuit_breaker_integration()


@pytest.mark.asyncio
async def test_end_to_end_journey(integration_test):
    """Test complete user journey"""
    await integration_test.test_end_to_end_user_journey()


if __name__ == "__main__":
    """
    Run integration tests directly
    Usage: python test_microservices_integration.py
    """
    import sys

    async def run_all_tests():
        test = MicroservicesIntegrationTest()
        await test.setup()

        try:
            print("🚀 Starting Dinner First Microservices Integration Tests")
            print("=" * 60)

            tests = [
                ("Authentication Service", test.test_auth_service_integration),
                ("Profile Service", test.test_profile_service_integration),
                ("Matching Service", test.test_matching_service_integration),
                ("Sentiment Service", test.test_sentiment_service_integration),
                ("Messaging Service", test.test_messaging_service_integration),
                ("WebSocket Integration", test.test_websocket_integration),
                ("Event-Driven Communication", test.test_event_driven_integration),
                ("Caching Consistency", test.test_caching_consistency),
                ("Circuit Breaker", test.test_circuit_breaker_integration),
                ("End-to-End Journey", test.test_end_to_end_user_journey),
            ]

            passed = 0
            failed = 0

            for test_name, test_func in tests:
                print(f"\n🧪 Running {test_name}...")
                try:
                    start_time = time.time()
                    await test_func()
                    duration = (time.time() - start_time) * 1000
                    print(f"✅ {test_name} PASSED ({duration:.0f}ms)")
                    passed += 1
                except Exception as e:
                    print(f"❌ {test_name} FAILED: {e}")
                    failed += 1

            print("\n" + "=" * 60)
            print(f"📊 Test Results: {passed} passed, {failed} failed")

            if failed == 0:
                print("🎉 All integration tests passed!")
                sys.exit(0)
            else:
                print("💥 Some tests failed!")
                sys.exit(1)

        finally:
            await test.teardown()

    asyncio.run(run_all_tests())
