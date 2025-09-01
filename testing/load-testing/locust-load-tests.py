"""
Comprehensive Load Testing Suite for Dinner First Platform
Using Locust for performance testing of Sprint 8 microservices architecture

Tests various scenarios:
- User authentication and registration
- Profile creation and updates
- AI matching requests
- Sentiment analysis processing
- Real-time messaging
- WebSocket connections

Target: 10,000+ concurrent users with sub-100ms 95th percentile response times
"""

import json
import random
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

import websocket
from locust import HttpUser, between, events, task
from locust.contrib.fasthttp import FastHttpUser


class DinnerFirstUser(FastHttpUser):
    """
    Simulates a typical Dinner First user journey with realistic behavior patterns
    """

    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    host = "https://api.dinner-first.app"

    def __init__(self, environment):
        super().__init__(environment)
        self.user_id = None
        self.auth_token = None
        self.profile_id = None
        self.connection_id = None
        self.websocket = None
        self.user_data = self._generate_user_data()

    def on_start(self):
        """Initialize user session"""
        self.register_user()
        self.login_user()
        self.create_profile()

    def on_stop(self):
        """Cleanup on user stop"""
        if self.websocket:
            self.websocket.close()

    def _generate_user_data(self) -> Dict[str, Any]:
        """Generate realistic user data for testing"""
        first_names = [
            "Alex",
            "Jordan",
            "Taylor",
            "Casey",
            "Riley",
            "Avery",
            "Quinn",
            "Sage",
        ]
        interests = [
            "cooking",
            "travel",
            "photography",
            "hiking",
            "reading",
            "music",
            "art",
            "fitness",
            "yoga",
            "meditation",
            "dancing",
            "gardening",
            "wine_tasting",
            "coffee",
            "movies",
            "theater",
            "volunteering",
        ]

        return {
            "email": f"test_{uuid.uuid4().hex[:8]}@dinner-first-load-test.com",
            "password": "LoadTest2025!",
            "first_name": random.choice(first_names),
            "age": random.randint(25, 45),
            "gender": random.choice(["male", "female", "non-binary"]),
            "location": {
                "city": random.choice(
                    ["San Francisco", "New York", "Los Angeles", "Chicago", "Austin"]
                ),
                "latitude": round(random.uniform(32.0, 45.0), 6),
                "longitude": round(random.uniform(-122.0, -74.0), 6),
            },
            "interests": random.sample(interests, random.randint(5, 12)),
            "life_philosophy": random.choice(
                [
                    "Live authentically and cherish meaningful connections",
                    "Embrace growth through shared experiences",
                    "Find joy in simple moments together",
                    "Build deep relationships based on understanding",
                ]
            ),
            "core_values": random.sample(
                [
                    "honesty",
                    "kindness",
                    "adventure",
                    "growth",
                    "loyalty",
                    "humor",
                    "stability",
                    "creativity",
                    "family",
                    "career",
                ],
                random.randint(3, 6),
            ),
        }

    @task(1)
    def register_user(self):
        """Test user registration endpoint"""
        if self.user_id:
            return  # Already registered

        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.user_data["email"],
                "password": self.user_data["password"],
                "first_name": self.user_data["first_name"],
                "age": self.user_data["age"],
                "gender": self.user_data["gender"],
            },
            name="/api/v1/auth/register",
        )

        if response.status_code == 201:
            data = response.json()
            self.user_id = data.get("user_id")

    @task(2)
    def login_user(self):
        """Test user login endpoint"""
        if self.auth_token:
            return  # Already logged in

        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.user_data["email"],
                "password": self.user_data["password"],
            },
            name="/api/v1/auth/login",
        )

        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})

    @task(1)
    def create_profile(self):
        """Test profile creation"""
        if not self.auth_token or self.profile_id:
            return

        response = self.client.post(
            "/api/v1/profiles",
            json={
                "location": self.user_data["location"],
                "interests": self.user_data["interests"],
                "life_philosophy": self.user_data["life_philosophy"],
                "core_values": self.user_data["core_values"],
                "emotional_onboarding_completed": True,
            },
            name="/api/v1/profiles",
        )

        if response.status_code in [200, 201]:
            data = response.json()
            self.profile_id = data.get("profile_id")

    @task(5)
    def get_profile(self):
        """Test profile retrieval"""
        if not self.auth_token:
            return

        self.client.get("/api/v1/profiles/me", name="/api/v1/profiles/me")

    @task(3)
    def update_profile(self):
        """Test profile updates"""
        if not self.auth_token or not self.profile_id:
            return

        # Update random field
        updates = {
            "life_philosophy": "Updated philosophy during load test",
            "interests": random.sample(
                self.user_data["interests"], random.randint(3, 8)
            ),
        }

        self.client.put(
            "/api/v1/profiles/me", json=updates, name="/api/v1/profiles/update"
        )

    @task(8)
    def discover_matches(self):
        """Test AI matching discovery endpoint"""
        if not self.auth_token or not self.profile_id:
            return

        response = self.client.get(
            "/api/v1/matching/discover",
            params={"limit": 10, "radius_km": 50},
            name="/api/v1/matching/discover",
        )

        # Simulate user viewing matches
        if response.status_code == 200:
            matches = response.json().get("matches", [])
            if matches:
                # View a random match profile
                match = random.choice(matches)
                self.client.get(
                    f"/api/v1/profiles/{match['user_id']}",
                    name="/api/v1/profiles/view_match",
                )

    @task(4)
    def initiate_connection(self):
        """Test connection initiation"""
        if not self.auth_token or not self.profile_id:
            return

        # Get potential matches first
        response = self.client.get(
            "/api/v1/matching/discover",
            params={"limit": 5},
            name="/api/v1/matching/discover_for_connection",
        )

        if response.status_code == 200:
            matches = response.json().get("matches", [])
            if matches:
                target_user = random.choice(matches)
                connection_response = self.client.post(
                    "/api/v1/connections/initiate",
                    json={
                        "target_user_id": target_user["user_id"],
                        "connection_message": "I'd love to get to know you better!",
                    },
                    name="/api/v1/connections/initiate",
                )

                if connection_response.status_code in [200, 201]:
                    data = connection_response.json()
                    self.connection_id = data.get("connection_id")

    @task(6)
    def send_message(self):
        """Test messaging functionality"""
        if not self.auth_token or not self.connection_id:
            return

        messages = [
            "How was your day?",
            "What's your favorite cuisine?",
            "Do you enjoy cooking together?",
            "I love your perspective on life!",
            "Would you like to plan our first dinner?",
            "What makes you feel most alive?",
        ]

        self.client.post(
            f"/api/v1/messages/{self.connection_id}",
            json={"message_text": random.choice(messages), "message_type": "text"},
            name="/api/v1/messages/send",
        )

    @task(4)
    def get_messages(self):
        """Test message retrieval"""
        if not self.auth_token or not self.connection_id:
            return

        self.client.get(
            f"/api/v1/messages/{self.connection_id}",
            params={"limit": 20, "offset": 0},
            name="/api/v1/messages/get",
        )

    @task(3)
    def analyze_sentiment(self):
        """Test sentiment analysis endpoint"""
        if not self.auth_token:
            return

        test_texts = [
            "I'm so excited about our upcoming dinner date!",
            "This conversation has been really meaningful to me.",
            "I appreciate how thoughtful you are.",
            "Looking forward to learning more about you.",
            "Your sense of humor brightens my day!",
            "I feel like we have a genuine connection.",
        ]

        self.client.post(
            "/api/v1/sentiment/analyze",
            json={
                "text": random.choice(test_texts),
                "context": "conversation",
                "analysis_types": ["emotion", "sentiment", "behavioral"],
            },
            name="/api/v1/sentiment/analyze",
        )

    @task(2)
    def get_compatibility_score(self):
        """Test compatibility scoring"""
        if not self.auth_token:
            return

        # Get a random user for compatibility check
        response = self.client.get(
            "/api/v1/matching/discover",
            params={"limit": 1},
            name="/api/v1/matching/compatibility_check",
        )

        if response.status_code == 200:
            matches = response.json().get("matches", [])
            if matches:
                target_user = matches[0]
                self.client.get(
                    f"/api/v1/matching/compatibility/{target_user['user_id']}",
                    name="/api/v1/matching/compatibility_score",
                )

    @task(7)
    def health_checks(self):
        """Test service health endpoints"""
        services = [
            "/api/v1/auth/health",
            "/api/v1/matching/health",
            "/api/v1/sentiment/health",
            "/api/v1/messages/health",
            "/api/v1/profiles/health",
        ]

        service = random.choice(services)
        self.client.get(service, name="health_check")


class WebSocketUser(HttpUser):
    """
    Specialized user for WebSocket connection testing
    """

    wait_time = between(2, 8)
    host = "https://api.dinner-first.app"

    def __init__(self, environment):
        super().__init__(environment)
        self.ws_url = "wss://ws.dinner-first.app"
        self.websocket = None
        self.auth_token = None
        self.connection_active = False
        self.messages_sent = 0
        self.messages_received = 0

    def on_start(self):
        """Initialize WebSocket connection"""
        # First authenticate via HTTP
        self.authenticate()
        if self.auth_token:
            self.connect_websocket()

    def on_stop(self):
        """Close WebSocket connection"""
        if self.websocket:
            self.websocket.close()

    def authenticate(self):
        """Authenticate user via HTTP API"""
        # Register and login (simplified for WebSocket testing)
        user_data = {
            "email": f"ws_test_{uuid.uuid4().hex[:8]}@dinner-first-load-test.com",
            "password": "WSTest2025!",
        }

        # Register
        register_response = self.client.post(
            "/api/v1/auth/register",
            json={
                **user_data,
                "first_name": "WSTest",
                "age": 30,
                "gender": "non-binary",
            },
        )

        # Login
        login_response = self.client.post("/api/v1/auth/login", json=user_data)
        if login_response.status_code == 200:
            self.auth_token = login_response.json().get("access_token")

    def connect_websocket(self):
        """Establish WebSocket connection"""
        try:
            self.websocket = websocket.WebSocket()

            # Connect with authentication
            headers = [f"Authorization: Bearer {self.auth_token}"]
            self.websocket.connect(self.ws_url, header=headers)

            self.connection_active = True

            # Start message listener in separate thread
            listener_thread = threading.Thread(target=self._message_listener)
            listener_thread.daemon = True
            listener_thread.start()

            events.request_success.fire(
                request_type="WebSocket",
                name="websocket_connect",
                response_time=100,  # Approximate connection time
                response_length=0,
            )

        except Exception as e:
            events.request_failure.fire(
                request_type="WebSocket",
                name="websocket_connect",
                response_time=0,
                exception=e,
            )

    def _message_listener(self):
        """Listen for incoming WebSocket messages"""
        while self.connection_active and self.websocket:
            try:
                message = self.websocket.recv()
                self.messages_received += 1

                events.request_success.fire(
                    request_type="WebSocket",
                    name="message_received",
                    response_time=10,  # Approximate processing time
                    response_length=len(message),
                )
            except Exception as e:
                if self.connection_active:  # Only log if we expect to be active
                    events.request_failure.fire(
                        request_type="WebSocket",
                        name="message_received",
                        response_time=0,
                        exception=e,
                    )
                break

    @task(10)
    def send_websocket_message(self):
        """Send messages via WebSocket"""
        if not self.websocket or not self.connection_active:
            return

        message_types = [
            {"type": "typing_start", "connection_id": "test_connection"},
            {"type": "typing_stop", "connection_id": "test_connection"},
            {
                "type": "message",
                "connection_id": "test_connection",
                "text": "Hello via WebSocket!",
            },
            {"type": "presence", "status": "online"},
            {"type": "read_receipt", "message_id": f"msg_{self.messages_sent}"},
        ]

        try:
            message = random.choice(message_types)
            message["timestamp"] = datetime.utcnow().isoformat()

            start_time = time.time()
            self.websocket.send(json.dumps(message))
            response_time = (time.time() - start_time) * 1000

            self.messages_sent += 1

            events.request_success.fire(
                request_type="WebSocket",
                name="message_sent",
                response_time=response_time,
                response_length=len(json.dumps(message)),
            )

        except Exception as e:
            events.request_failure.fire(
                request_type="WebSocket",
                name="message_sent",
                response_time=0,
                exception=e,
            )

    @task(2)
    def ping_websocket(self):
        """Send ping to maintain connection"""
        if not self.websocket or not self.connection_active:
            return

        try:
            start_time = time.time()
            self.websocket.ping()
            response_time = (time.time() - start_time) * 1000

            events.request_success.fire(
                request_type="WebSocket",
                name="websocket_ping",
                response_time=response_time,
                response_length=0,
            )

        except Exception as e:
            events.request_failure.fire(
                request_type="WebSocket",
                name="websocket_ping",
                response_time=0,
                exception=e,
            )


class AdminUser(HttpUser):
    """
    Administrative operations testing
    """

    wait_time = between(5, 15)
    host = "https://api.dinner-first.app"

    def __init__(self, environment):
        super().__init__(environment)
        self.admin_token = None

    def on_start(self):
        """Authenticate as admin user"""
        self.authenticate_admin()

    def authenticate_admin(self):
        """Authenticate with admin credentials"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "admin@dinner-first.app", "password": "AdminLoadTest2025!"},
        )

        if response.status_code == 200:
            self.admin_token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.admin_token}"})

    @task(3)
    def view_system_metrics(self):
        """Check system metrics endpoints"""
        if not self.admin_token:
            return

        metrics_endpoints = [
            "/api/v1/admin/metrics/users",
            "/api/v1/admin/metrics/matches",
            "/api/v1/admin/metrics/messages",
            "/api/v1/admin/metrics/system",
        ]

        endpoint = random.choice(metrics_endpoints)
        self.client.get(endpoint, name="admin_metrics")

    @task(1)
    def manage_ml_models(self):
        """Test ML model management"""
        if not self.admin_token:
            return

        self.client.get("/api/v1/admin/ml-models/status", name="ml_models_status")

    @task(2)
    def system_health_check(self):
        """Comprehensive system health check"""
        if not self.admin_token:
            return

        self.client.get("/api/v1/admin/health/detailed", name="system_health")


# Custom event handlers for detailed reporting
@events.request_success.add_listener
def my_request_success_handler(
    request_type, name, response_time, response_length, **kw
):
    """Log successful requests for analysis"""
    if response_time > 100:  # Log slow requests
        print(f"SLOW REQUEST: {name} took {response_time:.2f}ms")


@events.request_failure.add_listener
def my_request_failure_handler(
    request_type, name, response_time, response_length, exception, **kw
):
    """Log failed requests for analysis"""
    print(f"FAILED REQUEST: {name} - {exception}")


# Load testing scenarios configuration
load_test_scenarios = {
    "normal_load": {
        "users": 1000,
        "spawn_rate": 50,
        "duration": "10m",
        "user_classes": [
            {"class": DinnerFirstUser, "weight": 80},
            {"class": WebSocketUser, "weight": 15},
            {"class": AdminUser, "weight": 5},
        ],
    },
    "peak_load": {
        "users": 5000,
        "spawn_rate": 100,
        "duration": "15m",
        "user_classes": [
            {"class": DinnerFirstUser, "weight": 85},
            {"class": WebSocketUser, "weight": 12},
            {"class": AdminUser, "weight": 3},
        ],
    },
    "stress_test": {
        "users": 10000,
        "spawn_rate": 200,
        "duration": "20m",
        "user_classes": [
            {"class": DinnerFirstUser, "weight": 90},
            {"class": WebSocketUser, "weight": 8},
            {"class": AdminUser, "weight": 2},
        ],
    },
}

if __name__ == "__main__":
    print("Dinner First Load Testing Suite")
    print("Available scenarios:", list(load_test_scenarios.keys()))
    print(
        "Run with: locust -f locust-load-tests.py --host=https://api.dinner-first.app"
    )
    print("Web UI available at: http://localhost:8089")
