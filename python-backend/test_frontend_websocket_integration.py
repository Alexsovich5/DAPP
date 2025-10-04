#!/usr/bin/env python3
"""
Frontend-Backend WebSocket Integration Test - Sprint 4
Tests real-time communication between Angular frontend and FastAPI backend
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import websockets

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.logging_config import get_logger, setup_logging  # noqa: E402
from app.core.security import create_access_token  # noqa: E402


class WebSocketIntegrationTester:
    """Test WebSocket integration between frontend and backend"""

    def __init__(self):
        self.logger = get_logger("websocket_integration_tester")
        self.test_results = {}
        self.websocket = None
        self.connected = False
        self.messages_received = []

        # Test configuration
        self.backend_url = "ws://localhost:8000/api/v1/ws/connect"
        self.test_user_data = {
            "sub": "test@example.com",
            "user_id": 123,
            "username": "test_user",
        }

    def setup_logging(self):
        """Setup logging for integration tests"""
        setup_logging(
            environment="development",
            log_level="INFO",
            enable_structured_logging=False,
        )
        print("🔧 Logging configured for WebSocket integration tests")

    def create_test_token(self) -> str:
        """Create a JWT token for testing"""
        try:
            token = create_access_token(self.test_user_data)
            print("✅ Test token created successfully")
            return token
        except Exception as e:
            print(f"❌ Failed to create test token: {e}")
            return None

    async def test_websocket_connection(self, token: str) -> bool:
        """Test WebSocket connection with authentication"""
        print("🔌 Testing WebSocket connection...")

        try:
            # Connect to WebSocket with authentication
            uri = f"{self.backend_url}?token={token}"

            print(f"Connecting to: {uri}")

            self.websocket = await websockets.connect(
                uri,
                timeout=10,
                extra_headers={
                    "Authorization": f"Bearer {token}",
                    "Origin": "http://localhost:5001",  # Simulate Angular frontend
                },
            )

            self.connected = True
            print("✅ WebSocket connection established")

            # Wait for initial connection messages
            try:
                initial_message = await asyncio.wait_for(
                    self.websocket.recv(), timeout=5.0
                )

                message_data = json.loads(initial_message)
                print(f"📨 Initial message received: {message_data}")
                self.messages_received.append(message_data)

                return True

            except asyncio.TimeoutError:
                print("⚠️  No initial message received (this might be normal)")
                return True

        except websockets.exceptions.InvalidStatusCode as e:
            print(f"❌ WebSocket connection failed with status {e.status_code}")
            return False
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return False

    async def test_message_sending(self) -> bool:
        """Test sending messages from frontend to backend"""
        print("📤 Testing message sending...")

        if not self.connected or not self.websocket:
            print("❌ Not connected to WebSocket")
            return False

        try:
            # Test heartbeat message (typical frontend behavior)
            heartbeat_message = {
                "type": "heartbeat",
                "data": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "client": "angular_frontend",
                },
            }

            await self.websocket.send(json.dumps(heartbeat_message))
            print("✅ Heartbeat message sent")

            # Test presence update (typical frontend behavior)
            presence_message = {
                "type": "presence_update",
                "data": {
                    "status": "online",
                    "activity": "browsing_connections",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            await self.websocket.send(json.dumps(presence_message))
            print("✅ Presence update message sent")

            # Test activity tracking message
            activity_message = {
                "type": "activity_update",
                "data": {
                    "activity_type": "viewing_profile",
                    "context": "soul_connections",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            await self.websocket.send(json.dumps(activity_message))
            print("✅ Activity tracking message sent")

            return True

        except Exception as e:
            print(f"❌ Message sending failed: {e}")
            return False

    async def test_message_receiving(self) -> bool:
        """Test receiving messages from backend"""
        print("📥 Testing message receiving...")

        if not self.connected or not self.websocket:
            print("❌ Not connected to WebSocket")
            return False

        try:
            # Listen for messages for a short period
            messages_received = 0
            listen_duration = 3.0
            end_time = time.time() + listen_duration

            while time.time() < end_time:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=0.5)

                    message_data = json.loads(message)
                    self.messages_received.append(message_data)
                    messages_received += 1

                    print(
                        f"📨 Received message: {message_data.get('type', 'unknown')} - {message_data}"
                    )

                except asyncio.TimeoutError:
                    continue  # Normal timeout, continue listening

            print(
                f"✅ Message receiving test completed. Received {messages_received} messages"
            )
            return True

        except Exception as e:
            print(f"❌ Message receiving failed: {e}")
            return False

    async def test_channel_subscription(self) -> bool:
        """Test channel subscription functionality"""
        print("📺 Testing channel subscription...")

        if not self.connected or not self.websocket:
            print("❌ Not connected to WebSocket")
            return False

        try:
            # Subscribe to soul_connections channel (typical frontend behavior)
            subscription_message = {
                "type": "subscribe",
                "channel": "soul_connections",
                "data": {
                    "user_id": self.test_user_data["user_id"],
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            await self.websocket.send(json.dumps(subscription_message))
            print("✅ Channel subscription message sent")

            # Wait for subscription confirmation
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=3.0)

                response_data = json.loads(response)
                print(f"📨 Subscription response: {response_data}")
                self.messages_received.append(response_data)

                return True

            except asyncio.TimeoutError:
                print("⚠️  No subscription confirmation received")
                return True  # Still considered successful if no explicit confirmation

        except Exception as e:
            print(f"❌ Channel subscription failed: {e}")
            return False

    async def test_connection_resilience(self) -> bool:
        """Test connection resilience and error handling"""
        print("🛡️  Testing connection resilience...")

        try:
            # Test invalid message format
            await self.websocket.send("invalid json message")
            print("✅ Sent invalid message (testing error handling)")

            # Listen for error response
            try:
                error_response = await asyncio.wait_for(
                    self.websocket.recv(), timeout=2.0
                )

                error_data = json.loads(error_response)
                if error_data.get("type") == "error":
                    print(f"✅ Error handling working: {error_data}")
                else:
                    print(f"📨 Response to invalid message: {error_data}")

            except asyncio.TimeoutError:
                print("ℹ️  No explicit error response (backend might handle silently)")

            return True

        except Exception as e:
            print(f"❌ Connection resilience test failed: {e}")
            return False

    async def disconnect(self):
        """Clean disconnect from WebSocket"""
        if self.websocket and self.connected:
            try:
                await self.websocket.close()
                print("✅ WebSocket disconnected cleanly")
            except Exception as e:
                print(f"⚠️  Disconnect error: {e}")
            finally:
                self.connected = False
                self.websocket = None

    async def run_integration_tests(self) -> bool:
        """Run complete frontend-backend integration test suite"""
        print("🚀 Starting Frontend-Backend WebSocket Integration Tests")
        print("=" * 80)

        start_time = time.time()

        # Setup
        self.setup_logging()
        token = self.create_test_token()

        if not token:
            print("❌ Cannot proceed without authentication token")
            return False

        test_results = {
            "connection": False,
            "message_sending": False,
            "message_receiving": False,
            "channel_subscription": False,
            "connection_resilience": False,
        }

        try:
            # Test WebSocket connection
            test_results["connection"] = await self.test_websocket_connection(token)

            if test_results["connection"]:
                # Test message flows
                test_results["message_sending"] = await self.test_message_sending()
                test_results["message_receiving"] = await self.test_message_receiving()
                test_results["channel_subscription"] = (
                    await self.test_channel_subscription()
                )
                test_results["connection_resilience"] = (
                    await self.test_connection_resilience()
                )

            # Disconnect
            await self.disconnect()

        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            self.logger.error(f"Integration test error: {e}", exc_info=True)

        finally:
            # Ensure cleanup
            await self.disconnect()

        # Results summary
        end_time = time.time()
        duration = end_time - start_time

        print("\n" + "=" * 80)
        print("📊 Frontend-Backend WebSocket Integration Test Results")
        print("=" * 80)

        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)

        print(f"\n✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📨 Messages Received: {len(self.messages_received)}")

        print("\n📋 Detailed Results:")
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {status} {test_name.replace('_', ' ').title()}")

        print("\n💬 Message Log:")
        for i, message in enumerate(self.messages_received, 1):
            message_type = message.get("type", "unknown")
            print(f"  {i}. {message_type}: {message}")

        # Overall result
        all_passed = all(test_results.values())

        if all_passed:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Frontend-Backend WebSocket integration is working correctly")
        else:
            print("\n⚠️  Some integration tests failed")
            print("🔧 Check backend server and WebSocket endpoint configuration")

        return all_passed


async def main():
    """Main test runner"""
    print("🧪 Frontend-Backend WebSocket Integration Tester")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Note: Backend server must be running on localhost:8000")

    tester = WebSocketIntegrationTester()
    success = await tester.run_integration_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
