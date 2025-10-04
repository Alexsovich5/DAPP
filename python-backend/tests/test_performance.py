"""
Performance Tests for Real-time Features - Sprint 4
Load testing and performance validation for WebSocket and activity tracking
"""

import asyncio
import statistics
import time
from typing import Dict
from unittest.mock import MagicMock

import psutil
import pytest
from app.core.health_monitor import health_monitor
from app.models.user_activity_tracking import ActivityContext, ActivityType
from app.services.activity_tracking_service import activity_tracker
from app.services.realtime_connection_manager import (
    MessageType,
    RealtimeMessage,
    realtime_manager,
)


class PerformanceTracker:
    """Track performance metrics during tests"""

    def __init__(self):
        self.metrics = {
            "response_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "operations_per_second": 0,
            "errors": 0,
            "success_count": 0,
        }
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start performance tracking"""
        self.start_time = time.time()
        self.metrics["memory_usage"].append(psutil.virtual_memory().percent)
        self.metrics["cpu_usage"].append(psutil.cpu_percent())

    def record_operation(self, duration: float, success: bool = True):
        """Record an operation result"""
        self.metrics["response_times"].append(duration)
        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["errors"] += 1

    def stop(self):
        """Stop performance tracking and calculate final metrics"""
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time

        if total_duration > 0:
            self.metrics["operations_per_second"] = (
                self.metrics["success_count"] + self.metrics["errors"]
            ) / total_duration

        self.metrics["memory_usage"].append(psutil.virtual_memory().percent)
        self.metrics["cpu_usage"].append(psutil.cpu_percent())

    def get_summary(self) -> Dict:
        """Get performance summary"""
        response_times = self.metrics["response_times"]

        if response_times:
            return {
                "total_operations": len(response_times),
                "successful_operations": self.metrics["success_count"],
                "failed_operations": self.metrics["errors"],
                "operations_per_second": self.metrics["operations_per_second"],
                "avg_response_time_ms": statistics.mean(response_times) * 1000,
                "min_response_time_ms": min(response_times) * 1000,
                "max_response_time_ms": max(response_times) * 1000,
                "p95_response_time_ms": (
                    statistics.quantiles(response_times, n=20)[18] * 1000
                    if len(response_times) >= 20
                    else max(response_times) * 1000
                ),
                "avg_memory_usage_pct": statistics.mean(self.metrics["memory_usage"]),
                "max_memory_usage_pct": max(self.metrics["memory_usage"]),
                "avg_cpu_usage_pct": statistics.mean(self.metrics["cpu_usage"]),
                "max_cpu_usage_pct": max(self.metrics["cpu_usage"]),
            }
        else:
            return {"error": "No operations recorded"}


class TestWebSocketPerformance:
    """Performance tests for WebSocket connections"""

    @pytest.fixture
    def mock_websockets(self):
        """Create multiple mock WebSocket connections"""
        websockets = []
        for i in range(100):
            mock_ws = MagicMock()
            mock_ws.send_text = MagicMock()
            websockets.append(mock_ws)
        return websockets

    async def test_concurrent_connections_performance(self, mock_websockets):
        """Test performance with many concurrent WebSocket connections"""
        tracker = PerformanceTracker()
        tracker.start()

        # Connect multiple users concurrently
        connection_tasks = []
        for i, websocket in enumerate(mock_websockets):
            task = realtime_manager.connect(i, websocket)
            connection_tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        end_time = time.time()

        # Record connection performance
        for result in results:
            success = not isinstance(result, Exception)
            tracker.record_operation(end_time - start_time, success)

        tracker.stop()
        summary = tracker.get_summary()

        # Performance assertions
        assert (
            summary["successful_operations"] >= len(mock_websockets) * 0.95
        )  # 95% success rate
        assert summary["avg_response_time_ms"] < 100  # Under 100ms average
        assert summary["operations_per_second"] > 100  # At least 100 ops/sec

        print(f"Connection Performance: {summary}")

        # Cleanup connections
        for i in range(len(mock_websockets)):
            await realtime_manager.disconnect(i, None)

    async def test_message_broadcasting_performance(self, mock_websockets):
        """Test performance of message broadcasting to many users"""
        tracker = PerformanceTracker()

        # Connect users first
        for i, websocket in enumerate(mock_websockets[:50]):  # Use 50 connections
            await realtime_manager.connect(i, websocket)

        # Subscribe all users to a channel
        channel = "performance_test_channel"
        for i in range(50):
            await realtime_manager.subscribe_to_channel(i, channel)

        tracker.start()

        # Broadcast messages and measure performance
        num_broadcasts = 10
        for broadcast_num in range(num_broadcasts):
            message = RealtimeMessage(
                type=MessageType.NEW_MESSAGE,
                data={
                    "broadcast_id": broadcast_num,
                    "content": f"Performance test message {broadcast_num}",
                },
            )

            start_time = time.time()
            sent_count = await realtime_manager.broadcast_to_channel(channel, message)
            end_time = time.time()

            tracker.record_operation(end_time - start_time, sent_count > 0)

        tracker.stop()
        summary = tracker.get_summary()

        # Performance assertions
        assert summary["successful_operations"] == num_broadcasts
        assert summary["avg_response_time_ms"] < 50  # Under 50ms for broadcast
        assert summary["operations_per_second"] > 20  # At least 20 broadcasts/sec

        print(f"Broadcasting Performance: {summary}")

        # Cleanup
        for i in range(50):
            await realtime_manager.disconnect(i, None)

    async def test_high_frequency_heartbeats_performance(self, mock_websockets):
        """Test performance with high-frequency heartbeat messages"""
        tracker = PerformanceTracker()

        # Connect a subset of users
        connected_users = mock_websockets[:20]
        for i, websocket in enumerate(connected_users):
            await realtime_manager.connect(i, websocket)

        tracker.start()

        # Send rapid heartbeats
        heartbeat_tasks = []
        for i in range(len(connected_users)):
            for heartbeat_num in range(10):  # 10 heartbeats per user
                message_data = {
                    "type": "heartbeat",
                    "data": {
                        "timestamp": time.time(),
                        "sequence": heartbeat_num,
                    },
                }

                async def send_heartbeat(user_id, msg_data):
                    start_time = time.time()
                    try:
                        result = await realtime_manager.handle_message(
                            user_id, msg_data, None
                        )
                        end_time = time.time()
                        return end_time - start_time, result
                    except Exception:
                        end_time = time.time()
                        return end_time - start_time, False

                task = send_heartbeat(i, message_data)
                heartbeat_tasks.append(task)

        # Execute all heartbeats concurrently
        results = await asyncio.gather(*heartbeat_tasks)

        # Record performance metrics
        for duration, success in results:
            tracker.record_operation(duration, success)

        tracker.stop()
        summary = tracker.get_summary()

        # Performance assertions
        assert summary["successful_operations"] >= len(results) * 0.9  # 90% success
        assert summary["avg_response_time_ms"] < 10  # Under 10ms for heartbeats
        assert summary["operations_per_second"] > 500  # High throughput

        print(f"Heartbeat Performance: {summary}")

        # Cleanup
        for i in range(len(connected_users)):
            await realtime_manager.disconnect(i, None)


class TestActivityTrackingPerformance:
    """Performance tests for activity tracking system"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for performance testing"""
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.query = MagicMock()
        return mock_db

    async def test_concurrent_activity_logging_performance(self, mock_db_session):
        """Test performance with concurrent activity logging"""
        tracker = PerformanceTracker()
        tracker.start()

        # Create concurrent activity logging tasks
        num_users = 50
        activities_per_user = 5

        logging_tasks = []
        for user_id in range(num_users):
            for activity_num in range(activities_per_user):
                session_id = f"session_{user_id}_{activity_num}"

                async def log_activity_with_timing(uid, sid, activity_num):
                    start_time = time.time()
                    try:
                        result = await activity_tracker.log_activity(
                            user_id=uid,
                            session_id=sid,
                            activity_type=ActivityType.VIEWING_DISCOVERY,
                            context=ActivityContext.DISCOVERY_PAGE,
                            activity_data={
                                "test": True,
                                "sequence": activity_num,
                            },
                            db=mock_db_session,
                        )
                        end_time = time.time()
                        return end_time - start_time, result
                    except Exception:
                        end_time = time.time()
                        return end_time - start_time, False

                task = log_activity_with_timing(user_id, session_id, activity_num)
                logging_tasks.append(task)

        # Execute all activity logging concurrently
        results = await asyncio.gather(*logging_tasks)

        # Record performance metrics
        for duration, success in results:
            tracker.record_operation(duration, success)

        tracker.stop()
        summary = tracker.get_summary()

        # Performance assertions
        assert (
            summary["successful_operations"] >= len(results) * 0.8
        )  # 80% success (may have errors due to mocking)
        assert summary["avg_response_time_ms"] < 100  # Under 100ms for activity logging
        assert summary["operations_per_second"] > 50  # At least 50 ops/sec

        print(f"Activity Logging Performance: {summary}")

    async def test_activity_session_creation_performance(self, mock_db_session):
        """Test performance of activity session creation"""
        tracker = PerformanceTracker()
        tracker.start()

        # Create multiple sessions concurrently
        num_sessions = 100
        session_tasks = []

        for i in range(num_sessions):
            device_info = {
                "device_type": "desktop",
                "browser_info": {"name": "Chrome"},
                "network_type": "wifi",
            }

            async def create_session_with_timing(user_id, session_id, device_info):
                start_time = time.time()
                try:
                    result = await activity_tracker.start_activity_session(
                        user_id=user_id,
                        session_id=session_id,
                        device_info=device_info,
                        db=mock_db_session,
                    )
                    end_time = time.time()
                    return end_time - start_time, result
                except Exception:
                    end_time = time.time()
                    return end_time - start_time, False

            task = create_session_with_timing(i, f"perf_session_{i}", device_info)
            session_tasks.append(task)

        # Execute all session creations
        results = await asyncio.gather(*session_tasks)

        # Record performance metrics
        for duration, success in results:
            tracker.record_operation(duration, success)

        tracker.stop()
        summary = tracker.get_summary()

        # Performance assertions
        assert summary["successful_operations"] >= len(results) * 0.8  # 80% success
        assert summary["avg_response_time_ms"] < 200  # Under 200ms for session creation
        assert summary["operations_per_second"] > 20  # At least 20 sessions/sec

        print(f"Session Creation Performance: {summary}")

    async def test_presence_summary_updates_performance(self, mock_db_session):
        """Test performance of presence summary updates"""
        tracker = PerformanceTracker()
        tracker.start()

        # Update presence for multiple users
        num_updates = 200
        update_tasks = []

        for i in range(num_updates):
            user_id = i % 50  # Cycle through 50 users

            async def get_current_activity_with_timing(user_id):
                start_time = time.time()
                try:
                    result = await activity_tracker.get_user_current_activity(
                        user_id, mock_db_session
                    )
                    end_time = time.time()
                    return end_time - start_time, result is not None
                except Exception:
                    end_time = time.time()
                    return end_time - start_time, False

            task = get_current_activity_with_timing(user_id)
            update_tasks.append(task)

        # Execute all presence updates
        results = await asyncio.gather(*update_tasks)

        # Record performance metrics
        for duration, success in results:
            tracker.record_operation(duration, success)

        tracker.stop()
        summary = tracker.get_summary()

        # Performance assertions
        assert summary["avg_response_time_ms"] < 50  # Under 50ms for presence queries
        assert summary["operations_per_second"] > 100  # At least 100 ops/sec

        print(f"Presence Update Performance: {summary}")


class TestHealthMonitoringPerformance:
    """Performance tests for health monitoring system"""

    async def test_health_check_performance(self):
        """Test performance of health monitoring system"""
        tracker = PerformanceTracker()
        tracker.start()

        # Perform multiple health checks
        num_checks = 10
        health_tasks = []

        for i in range(num_checks):

            async def health_check_with_timing():
                start_time = time.time()
                try:
                    health_result = (
                        await health_monitor.perform_comprehensive_health_check()
                    )
                    end_time = time.time()
                    return end_time - start_time, health_result is not None
                except Exception:
                    end_time = time.time()
                    return end_time - start_time, False

            task = health_check_with_timing()
            health_tasks.append(task)

        # Execute health checks
        results = await asyncio.gather(*health_tasks)

        # Record performance metrics
        for duration, success in results:
            tracker.record_operation(duration, success)

        tracker.stop()
        summary = tracker.get_summary()

        # Performance assertions
        assert summary["successful_operations"] >= num_checks * 0.9  # 90% success
        assert summary["avg_response_time_ms"] < 1000  # Under 1 second for health check
        assert summary["operations_per_second"] > 5  # At least 5 health checks/sec

        print(f"Health Check Performance: {summary}")

    async def test_concurrent_component_health_checks(self):
        """Test performance of concurrent component health checks"""
        tracker = PerformanceTracker()
        tracker.start()

        # Test individual component checks concurrently
        component_tasks = [
            health_monitor.check_websocket_health(),
            health_monitor.check_system_resources(),
            health_monitor.check_realtime_integration_health(),
        ]

        # Run multiple rounds concurrently
        all_tasks = []
        for round_num in range(5):
            for task in component_tasks:

                async def component_check_with_timing(check_task):
                    start_time = time.time()
                    try:
                        result = await check_task
                        end_time = time.time()
                        return end_time - start_time, result is not None
                    except Exception:
                        end_time = time.time()
                        return end_time - start_time, False

                timed_task = component_check_with_timing(task)
                all_tasks.append(timed_task)

        # Execute all component checks
        results = await asyncio.gather(*all_tasks)

        # Record performance metrics
        for duration, success in results:
            tracker.record_operation(duration, success)

        tracker.stop()
        summary = tracker.get_summary()

        # Performance assertions
        assert summary["avg_response_time_ms"] < 500  # Under 500ms for component checks
        assert summary["operations_per_second"] > 10  # At least 10 checks/sec

        print(f"Component Health Check Performance: {summary}")


class TestMemoryLeakDetection:
    """Tests to detect memory leaks in real-time features"""

    async def test_websocket_connection_memory_usage(self):
        """Test for memory leaks in WebSocket connections"""
        initial_memory = psutil.virtual_memory().percent

        # Create and destroy many connections
        for batch in range(10):
            websockets = []
            for i in range(50):
                mock_ws = MagicMock()
                websockets.append(mock_ws)
                await realtime_manager.connect(batch * 50 + i, mock_ws)

            # Disconnect all connections
            for i, _ in enumerate(websockets):
                await realtime_manager.disconnect(batch * 50 + i, None)

            # Check memory after each batch
            current_memory = psutil.virtual_memory().percent
            memory_increase = current_memory - initial_memory

            # Memory increase should be reasonable (less than 5%)
            assert (
                memory_increase < 5.0
            ), f"Potential memory leak detected: {memory_increase}% increase"

        print(f"Memory usage test completed. Max increase: {memory_increase:.2f}%")

    async def test_activity_logging_memory_usage(self):
        """Test for memory leaks in activity logging"""
        initial_memory = psutil.virtual_memory().percent

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        # Log many activities
        for batch in range(5):
            for user_id in range(20):
                for activity_num in range(10):
                    try:
                        await activity_tracker.log_activity(
                            user_id=user_id,
                            session_id=f"memory_test_session_{user_id}_{activity_num}",
                            activity_type=ActivityType.VIEWING_DISCOVERY,
                            context=ActivityContext.DISCOVERY_PAGE,
                            activity_data={
                                "batch": batch,
                                "sequence": activity_num,
                            },
                            db=mock_db,
                        )
                    except Exception:
                        pass  # Expected due to mocking

            # Check memory after each batch
            current_memory = psutil.virtual_memory().percent
            memory_increase = current_memory - initial_memory

            # Memory increase should be reasonable
            assert (
                memory_increase < 3.0
            ), f"Potential memory leak in activity logging: {memory_increase}%"

        print(
            f"Activity logging memory test completed. Max increase: {memory_increase:.2f}%"
        )


class TestStressConditions:
    """Tests under stress conditions"""

    async def test_system_under_high_load(self):
        """Test system behavior under high load"""
        tracker = PerformanceTracker()
        tracker.start()

        # Create high load scenario
        tasks = []

        # WebSocket connections
        for i in range(100):
            mock_ws = MagicMock()
            task = realtime_manager.connect(i, mock_ws)
            tasks.append(task)

        # Message broadcasting
        for i in range(20):
            message = RealtimeMessage(
                type=MessageType.NEW_MESSAGE,
                data={"stress_test": True, "message_id": i},
            )
            task = realtime_manager.broadcast_to_channel("stress_test", message)
            tasks.append(task)

        # Activity logging
        mock_db = MagicMock()
        for i in range(200):
            task = activity_tracker.log_activity(
                user_id=i % 50,
                session_id=f"stress_session_{i}",
                activity_type=ActivityType.VIEWING_DISCOVERY,
                context=ActivityContext.DISCOVERY_PAGE,
                db=mock_db,
            )
            tasks.append(task)

        # Execute all tasks
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Analyze results
        successful = sum(1 for result in results if not isinstance(result, Exception))
        failed = len(results) - successful

        tracker.record_operation(end_time - start_time, successful > failed)
        tracker.stop()
        summary = tracker.get_summary()

        # System should handle at least 70% of operations successfully under stress
        success_rate = successful / len(results)
        assert success_rate > 0.7, f"Low success rate under stress: {success_rate:.2%}"

        print(f"Stress test completed. Success rate: {success_rate:.2%}")
        print(f"Performance under stress: {summary}")

        # Cleanup
        for i in range(100):
            try:
                await realtime_manager.disconnect(i, None)
            except Exception:
                pass


# Benchmark utilities
def benchmark_function(func, *args, iterations=100, **kwargs):
    """Benchmark a function call"""
    times = []

    for _ in range(iterations):
        start_time = time.perf_counter()
        try:
            if asyncio.iscoroutinefunction(func):
                asyncio.run(func(*args, **kwargs))
            else:
                func(*args, **kwargs)
            success = True
        except Exception:
            success = False
        end_time = time.perf_counter()

        times.append((end_time - start_time, success))

    successful_times = [t for t, s in times if s]

    if successful_times:
        return {
            "avg_time_ms": statistics.mean(successful_times) * 1000,
            "min_time_ms": min(successful_times) * 1000,
            "max_time_ms": max(successful_times) * 1000,
            "success_rate": len(successful_times) / len(times),
            "operations_per_second": 1 / statistics.mean(successful_times),
        }
    else:
        return {"error": "No successful operations"}


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
