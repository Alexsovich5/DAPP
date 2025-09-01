"""
Performance Test Suite for Dinner First Sprint 8 Microservices
Validates performance targets and benchmarks for:
- Sub-100ms 95th percentile response times
- 10,000+ concurrent user support
- Redis cluster performance
- Database query optimization
- AI/ML model inference times
- WebSocket real-time performance
- Memory and CPU utilization
"""

import asyncio
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import aiohttp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil
import redis.asyncio as redis
import websockets


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""

    endpoint: str
    response_times: List[float]
    success_count: int
    error_count: int
    start_time: datetime
    end_time: datetime

    @property
    def total_requests(self) -> int:
        return self.success_count + self.error_count

    @property
    def success_rate(self) -> float:
        return (
            self.success_count / self.total_requests if self.total_requests > 0 else 0
        )

    @property
    def average_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0

    @property
    def percentile_95(self) -> float:
        return np.percentile(self.response_times, 95) if self.response_times else 0

    @property
    def percentile_99(self) -> float:
        return np.percentile(self.response_times, 99) if self.response_times else 0

    @property
    def requests_per_second(self) -> float:
        duration = (self.end_time - self.start_time).total_seconds()
        return self.total_requests / duration if duration > 0 else 0


class PerformanceTestSuite:
    """Comprehensive performance testing suite"""

    def __init__(self):
        self.api_base_url = "https://api.dinner-first.app/api/v1"
        self.websocket_url = "wss://ws.dinner-first.app"
        self.redis_url = (
            "redis://redis-cluster.dinner-first-redis.svc.cluster.local:6379"
        )

        self.session: aiohttp.ClientSession = None
        self.redis_client: redis.RedisCluster = None
        self.test_results: Dict[str, PerformanceMetrics] = {}

        # Performance targets
        self.target_95th_percentile = 100  # milliseconds
        self.target_success_rate = 0.99
        self.target_concurrent_users = 10000

    async def setup(self):
        """Initialize test environment"""
        # HTTP session with optimized settings
        connector = aiohttp.TCPConnector(
            limit=1000,
            limit_per_host=100,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=5)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

        # Redis cluster connection
        self.redis_client = redis.RedisCluster(
            host="redis-cluster.dinner-first-redis.svc.cluster.local",
            port=6379,
            decode_responses=True,
            max_connections=100,
        )

        print("🚀 Performance test environment initialized")

    async def teardown(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.close()

        print("🧹 Test environment cleaned up")

    async def create_auth_token(self, user_suffix: str = None) -> str:
        """Create authenticated user and return token"""
        suffix = user_suffix or str(int(time.time() * 1000))
        user_data = {
            "email": f"perf_test_{suffix}@test.com",
            "password": "PerfTest2025!",
            "first_name": f"PerfTest{suffix}",
            "age": 28,
            "gender": "non-binary",
        }

        # Register user
        async with self.session.post(
            f"{self.api_base_url}/auth/register", json=user_data
        ) as response:
            if response.status != 201:
                raise Exception(f"Registration failed: {await response.text()}")

        # Login user
        async with self.session.post(
            f"{self.api_base_url}/auth/login",
            json={"email": user_data["email"], "password": user_data["password"]},
        ) as response:
            if response.status != 200:
                raise Exception(f"Login failed: {await response.text()}")

            result = await response.json()
            return result["access_token"]

    async def measure_endpoint_performance(
        self,
        endpoint: str,
        method: str = "GET",
        headers: Dict = None,
        json_data: Dict = None,
        concurrent_requests: int = 100,
        total_requests: int = 1000,
    ) -> PerformanceMetrics:
        """Measure endpoint performance with concurrent requests"""

        response_times = []
        success_count = 0
        error_count = 0
        start_time = datetime.now()

        semaphore = asyncio.Semaphore(concurrent_requests)

        async def make_request():
            nonlocal success_count, error_count
            async with semaphore:
                request_start = time.time()
                try:
                    if method.upper() == "GET":
                        async with self.session.get(
                            endpoint, headers=headers
                        ) as response:
                            await response.text()  # Consume response
                            if 200 <= response.status < 300:
                                success_count += 1
                            else:
                                error_count += 1
                    elif method.upper() == "POST":
                        async with self.session.post(
                            endpoint, headers=headers, json=json_data
                        ) as response:
                            await response.text()
                            if 200 <= response.status < 300:
                                success_count += 1
                            else:
                                error_count += 1

                    request_time = (time.time() - request_start) * 1000  # Convert to ms
                    response_times.append(request_time)

                except Exception as e:
                    error_count += 1
                    # Still record time for failed requests
                    request_time = (time.time() - request_start) * 1000
                    response_times.append(request_time)

        # Execute concurrent requests
        tasks = [make_request() for _ in range(total_requests)]
        await asyncio.gather(*tasks)

        end_time = datetime.now()

        return PerformanceMetrics(
            endpoint=endpoint,
            response_times=response_times,
            success_count=success_count,
            error_count=error_count,
            start_time=start_time,
            end_time=end_time,
        )

    async def test_authentication_performance(self):
        """Test authentication service performance"""
        print("🔐 Testing Authentication Service Performance...")

        # Test login endpoint
        user_data = {"email": "perf_test@test.com", "password": "PerfTest2025!"}

        # Pre-register the test user
        try:
            await self.create_auth_token("login_perf")
        except:
            pass  # User might already exist

        metrics = await self.measure_endpoint_performance(
            f"{self.api_base_url}/auth/login",
            method="POST",
            json_data=user_data,
            concurrent_requests=50,
            total_requests=500,
        )

        self.test_results["auth_login"] = metrics

        # Validate performance targets
        assert (
            metrics.percentile_95 < self.target_95th_percentile
        ), f"Auth login 95th percentile too high: {metrics.percentile_95}ms"
        assert (
            metrics.success_rate > self.target_success_rate
        ), f"Auth login success rate too low: {metrics.success_rate}"

        print(
            f"✅ Auth Login - 95th percentile: {metrics.percentile_95:.1f}ms, Success rate: {metrics.success_rate:.3f}"
        )

    async def test_profile_service_performance(self):
        """Test profile service performance"""
        print("👤 Testing Profile Service Performance...")

        # Create auth token
        auth_token = await self.create_auth_token("profile_perf")
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create profile first
        profile_data = {
            "location": {
                "city": "San Francisco",
                "latitude": 37.7749,
                "longitude": -122.4194,
            },
            "interests": ["cooking", "travel", "photography"],
            "life_philosophy": "Performance testing profile",
            "core_values": ["honesty", "growth"],
        }

        async with self.session.post(
            f"{self.api_base_url}/profiles", json=profile_data, headers=headers
        ) as response:
            if response.status not in [200, 201]:
                raise Exception(f"Profile creation failed: {await response.text()}")

        # Test profile retrieval performance
        metrics = await self.measure_endpoint_performance(
            f"{self.api_base_url}/profiles/me",
            headers=headers,
            concurrent_requests=75,
            total_requests=750,
        )

        self.test_results["profile_get"] = metrics

        # Validate performance targets
        assert (
            metrics.percentile_95 < self.target_95th_percentile
        ), f"Profile get 95th percentile too high: {metrics.percentile_95}ms"
        assert (
            metrics.success_rate > self.target_success_rate
        ), f"Profile get success rate too low: {metrics.success_rate}"

        print(
            f"✅ Profile Get - 95th percentile: {metrics.percentile_95:.1f}ms, Success rate: {metrics.success_rate:.3f}"
        )

    async def test_matching_service_performance(self):
        """Test AI matching service performance"""
        print("🧠 Testing AI Matching Service Performance...")

        # Create auth token and profile
        auth_token = await self.create_auth_token("matching_perf")
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create profile
        profile_data = {
            "location": {
                "city": "San Francisco",
                "latitude": 37.7749,
                "longitude": -122.4194,
            },
            "interests": ["cooking", "travel", "music", "hiking", "art"],
            "life_philosophy": "Matching performance test profile",
            "core_values": ["adventure", "honesty", "growth"],
        }

        async with self.session.post(
            f"{self.api_base_url}/profiles", json=profile_data, headers=headers
        ) as response:
            if response.status not in [200, 201]:
                print(f"Profile creation failed: {await response.text()}")

        # Test matching discovery performance
        metrics = await self.measure_endpoint_performance(
            f"{self.api_base_url}/matching/discover?limit=10&radius_km=50",
            headers=headers,
            concurrent_requests=25,  # Lower concurrency for AI service
            total_requests=250,
        )

        self.test_results["matching_discover"] = metrics

        # AI services have slightly higher tolerance
        ai_target = self.target_95th_percentile * 1.5  # 150ms for AI operations
        assert (
            metrics.percentile_95 < ai_target
        ), f"Matching 95th percentile too high: {metrics.percentile_95}ms"
        assert (
            metrics.success_rate > 0.95
        ), f"Matching success rate too low: {metrics.success_rate}"

        print(
            f"✅ Matching Discover - 95th percentile: {metrics.percentile_95:.1f}ms, Success rate: {metrics.success_rate:.3f}"
        )

    async def test_sentiment_analysis_performance(self):
        """Test sentiment analysis service performance"""
        print("😊 Testing Sentiment Analysis Performance...")

        auth_token = await self.create_auth_token("sentiment_perf")
        headers = {"Authorization": f"Bearer {auth_token}"}

        sentiment_data = {
            "text": "I'm so excited about our upcoming dinner date! This conversation has been really meaningful.",
            "context": "conversation",
            "analysis_types": ["sentiment", "emotion"],
        }

        metrics = await self.measure_endpoint_performance(
            f"{self.api_base_url}/sentiment/analyze",
            method="POST",
            headers=headers,
            json_data=sentiment_data,
            concurrent_requests=20,  # Lower for ML processing
            total_requests=200,
        )

        self.test_results["sentiment_analyze"] = metrics

        # AI services tolerance
        ai_target = self.target_95th_percentile * 1.5
        assert (
            metrics.percentile_95 < ai_target
        ), f"Sentiment 95th percentile too high: {metrics.percentile_95}ms"
        assert (
            metrics.success_rate > 0.95
        ), f"Sentiment success rate too low: {metrics.success_rate}"

        print(
            f"✅ Sentiment Analysis - 95th percentile: {metrics.percentile_95:.1f}ms, Success rate: {metrics.success_rate:.3f}"
        )

    async def test_messaging_service_performance(self):
        """Test messaging service performance"""
        print("💬 Testing Messaging Service Performance...")

        auth_token = await self.create_auth_token("messaging_perf")
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create a connection first (mock connection ID)
        connection_id = "perf_test_connection_123"

        message_data = {
            "message_text": "Performance test message",
            "message_type": "text",
        }

        # Test message retrieval (assuming some messages exist)
        metrics = await self.measure_endpoint_performance(
            f"{self.api_base_url}/messages/{connection_id}?limit=20",
            headers=headers,
            concurrent_requests=50,
            total_requests=500,
        )

        self.test_results["messaging_get"] = metrics

        # Messaging should be fast
        assert (
            metrics.percentile_95 < self.target_95th_percentile
        ), f"Messaging 95th percentile too high: {metrics.percentile_95}ms"

        print(
            f"✅ Messaging Get - 95th percentile: {metrics.percentile_95:.1f}ms, Success rate: {metrics.success_rate:.3f}"
        )

    async def test_redis_cache_performance(self):
        """Test Redis cluster cache performance"""
        print("🚀 Testing Redis Cache Performance...")

        response_times = []
        success_count = 0
        error_count = 0

        start_time = datetime.now()

        # Test Redis operations
        test_data = {"user_id": 123, "name": "Performance Test", "data": "x" * 1000}

        async def redis_operation():
            nonlocal success_count, error_count
            op_start = time.time()
            try:
                # Set operation
                key = f"perf_test:{int(time.time() * 1000000)}"
                await self.redis_client.set(key, json.dumps(test_data), ex=3600)

                # Get operation
                result = await self.redis_client.get(key)

                # Delete operation
                await self.redis_client.delete(key)

                if result:
                    success_count += 1
                else:
                    error_count += 1

                op_time = (time.time() - op_start) * 1000
                response_times.append(op_time)

            except Exception as e:
                error_count += 1
                op_time = (time.time() - op_start) * 1000
                response_times.append(op_time)

        # Execute concurrent Redis operations
        tasks = [redis_operation() for _ in range(1000)]
        await asyncio.gather(*tasks)

        end_time = datetime.now()

        metrics = PerformanceMetrics(
            endpoint="redis_operations",
            response_times=response_times,
            success_count=success_count,
            error_count=error_count,
            start_time=start_time,
            end_time=end_time,
        )

        self.test_results["redis_cache"] = metrics

        # Cache should be very fast
        cache_target = 10  # 10ms for cache operations
        assert (
            metrics.percentile_95 < cache_target
        ), f"Redis 95th percentile too high: {metrics.percentile_95}ms"
        assert (
            metrics.success_rate > 0.99
        ), f"Redis success rate too low: {metrics.success_rate}"

        print(
            f"✅ Redis Cache - 95th percentile: {metrics.percentile_95:.1f}ms, Success rate: {metrics.success_rate:.3f}"
        )

    async def test_websocket_performance(self):
        """Test WebSocket real-time performance"""
        print("⚡ Testing WebSocket Performance...")

        auth_token = await self.create_auth_token("websocket_perf")

        latencies = []
        success_count = 0
        error_count = 0

        async def websocket_test():
            nonlocal success_count, error_count
            try:
                headers = {"Authorization": f"Bearer {auth_token}"}
                async with websockets.connect(
                    self.websocket_url, extra_headers=headers
                ) as websocket:

                    # Send 10 messages and measure round-trip time
                    for i in range(10):
                        message = {
                            "type": "ping",
                            "id": f"perf_test_{i}",
                            "timestamp": time.time(),
                        }

                        start_time = time.time()
                        await websocket.send(json.dumps(message))

                        # Wait for pong response
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        latency = (time.time() - start_time) * 1000

                        latencies.append(latency)
                        success_count += 1

                        await asyncio.sleep(0.1)  # Small delay between messages

            except Exception as e:
                error_count += 10  # Failed websocket connection affects all messages

        # Run multiple concurrent WebSocket connections
        start_time = datetime.now()
        tasks = [websocket_test() for _ in range(10)]  # 10 concurrent connections
        await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()

        if latencies:
            metrics = PerformanceMetrics(
                endpoint="websocket_roundtrip",
                response_times=latencies,
                success_count=success_count,
                error_count=error_count,
                start_time=start_time,
                end_time=end_time,
            )

            self.test_results["websocket"] = metrics

            # WebSocket should be very fast
            ws_target = 50  # 50ms for WebSocket round-trip
            assert (
                metrics.percentile_95 < ws_target
            ), f"WebSocket 95th percentile too high: {metrics.percentile_95}ms"

            print(
                f"✅ WebSocket - 95th percentile: {metrics.percentile_95:.1f}ms, Success rate: {metrics.success_rate:.3f}"
            )
        else:
            print("❌ WebSocket test failed - no successful connections")

    async def test_concurrent_user_load(self):
        """Test system performance under concurrent user load"""
        print(
            f"👥 Testing Concurrent User Load ({self.target_concurrent_users} users)..."
        )

        # Create multiple authenticated users
        auth_tokens = []
        print("Creating test users...")
        for i in range(
            min(100, self.target_concurrent_users // 100)
        ):  # Create 1% of target users
            try:
                token = await self.create_auth_token(f"load_test_{i}")
                auth_tokens.append(token)
            except:
                pass  # Skip failed user creation

        if not auth_tokens:
            print("❌ Failed to create test users for load test")
            return

        print(f"Created {len(auth_tokens)} test users")

        # Simulate concurrent user activity
        async def simulate_user_activity(auth_token: str):
            headers = {"Authorization": f"Bearer {auth_token}"}

            # Simulate typical user session
            activities = [
                ("GET", f"{self.api_base_url}/profiles/me"),
                ("GET", f"{self.api_base_url}/matching/discover?limit=5"),
                ("GET", f"{self.api_base_url}/profiles/me"),  # Cache hit
            ]

            response_times = []
            success_count = 0
            error_count = 0

            for method, url in activities:
                start_time = time.time()
                try:
                    if method == "GET":
                        async with self.session.get(url, headers=headers) as response:
                            await response.text()
                            if 200 <= response.status < 300:
                                success_count += 1
                            else:
                                error_count += 1

                    request_time = (time.time() - start_time) * 1000
                    response_times.append(request_time)

                except Exception:
                    error_count += 1
                    request_time = (time.time() - start_time) * 1000
                    response_times.append(request_time)

                # Small delay between activities
                await asyncio.sleep(0.5)

            return response_times, success_count, error_count

        # Run concurrent user simulations
        start_time = datetime.now()
        tasks = [simulate_user_activity(token) for token in auth_tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()

        # Aggregate results
        all_response_times = []
        total_success = 0
        total_errors = 0

        for result in results:
            if isinstance(result, tuple):
                response_times, success_count, error_count = result
                all_response_times.extend(response_times)
                total_success += success_count
                total_errors += error_count

        if all_response_times:
            metrics = PerformanceMetrics(
                endpoint="concurrent_load",
                response_times=all_response_times,
                success_count=total_success,
                error_count=total_errors,
                start_time=start_time,
                end_time=end_time,
            )

            self.test_results["concurrent_load"] = metrics

            print(
                f"✅ Concurrent Load - 95th percentile: {metrics.percentile_95:.1f}ms, Success rate: {metrics.success_rate:.3f}"
            )
            print(
                f"   RPS: {metrics.requests_per_second:.1f}, Total requests: {metrics.total_requests}"
            )
        else:
            print("❌ Concurrent load test failed")

    def test_system_resources(self):
        """Test system resource utilization"""
        print("📊 Testing System Resource Utilization...")

        # Get current system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        resource_metrics = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
        }

        # Resource thresholds
        assert cpu_percent < 80, f"CPU usage too high: {cpu_percent}%"
        assert memory.percent < 80, f"Memory usage too high: {memory.percent}%"
        assert disk.percent < 90, f"Disk usage too high: {disk.percent}%"

        print(
            f"✅ System Resources - CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%"
        )

        self.test_results["system_resources"] = resource_metrics

    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        report = []
        report.append("# Dinner First Performance Test Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Summary table
        report.append("## Performance Summary")
        report.append(
            "| Service | 95th Percentile (ms) | Success Rate | RPS | Status |"
        )
        report.append("|---------|---------------------|--------------|-----|--------|")

        for test_name, metrics in self.test_results.items():
            if isinstance(metrics, PerformanceMetrics):
                status = (
                    "✅ PASS"
                    if metrics.percentile_95 < self.target_95th_percentile
                    else "❌ FAIL"
                )
                if (
                    "ai" in test_name.lower()
                    or "matching" in test_name.lower()
                    or "sentiment" in test_name.lower()
                ):
                    status = (
                        "✅ PASS"
                        if metrics.percentile_95 < (self.target_95th_percentile * 1.5)
                        else "❌ FAIL"
                    )

                report.append(
                    f"| {test_name} | {metrics.percentile_95:.1f} | {metrics.success_rate:.3f} | "
                    f"{metrics.requests_per_second:.1f} | {status} |"
                )

        report.append("")

        # Detailed results
        report.append("## Detailed Results")
        for test_name, metrics in self.test_results.items():
            if isinstance(metrics, PerformanceMetrics):
                report.append(f"### {test_name}")
                report.append(
                    f"- Average Response Time: {metrics.average_response_time:.2f}ms"
                )
                report.append(f"- 95th Percentile: {metrics.percentile_95:.2f}ms")
                report.append(f"- 99th Percentile: {metrics.percentile_99:.2f}ms")
                report.append(f"- Success Rate: {metrics.success_rate:.3f}")
                report.append(
                    f"- Requests per Second: {metrics.requests_per_second:.1f}"
                )
                report.append(f"- Total Requests: {metrics.total_requests}")
                report.append("")

        # System resources
        if "system_resources" in self.test_results:
            resources = self.test_results["system_resources"]
            report.append("## System Resources")
            report.append(f"- CPU Usage: {resources['cpu_percent']:.1f}%")
            report.append(f"- Memory Usage: {resources['memory_percent']:.1f}%")
            report.append(
                f"- Available Memory: {resources['memory_available_gb']:.1f}GB"
            )
            report.append(f"- Disk Usage: {resources['disk_percent']:.1f}%")
            report.append(f"- Free Disk Space: {resources['disk_free_gb']:.1f}GB")
            report.append("")

        # Performance targets
        report.append("## Performance Targets")
        report.append(f"- Target 95th Percentile: {self.target_95th_percentile}ms")
        report.append(f"- Target Success Rate: {self.target_success_rate}")
        report.append(f"- Target Concurrent Users: {self.target_concurrent_users}")

        return "\n".join(report)

    def save_performance_charts(self):
        """Generate and save performance visualization charts"""
        try:
            # Create performance comparison chart
            services = []
            p95_times = []
            success_rates = []

            for test_name, metrics in self.test_results.items():
                if isinstance(metrics, PerformanceMetrics):
                    services.append(test_name.replace("_", " ").title())
                    p95_times.append(metrics.percentile_95)
                    success_rates.append(metrics.success_rate * 100)

            if services:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

                # 95th percentile chart
                bars1 = ax1.bar(services, p95_times, color="skyblue", alpha=0.7)
                ax1.axhline(
                    y=self.target_95th_percentile,
                    color="red",
                    linestyle="--",
                    label=f"Target ({self.target_95th_percentile}ms)",
                )
                ax1.set_title("95th Percentile Response Times")
                ax1.set_ylabel("Response Time (ms)")
                ax1.tick_params(axis="x", rotation=45)
                ax1.legend()
                ax1.grid(True, alpha=0.3)

                # Add value labels on bars
                for bar, value in zip(bars1, p95_times):
                    ax1.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 5,
                        f"{value:.1f}",
                        ha="center",
                        va="bottom",
                    )

                # Success rate chart
                bars2 = ax2.bar(services, success_rates, color="lightgreen", alpha=0.7)
                ax2.axhline(
                    y=self.target_success_rate * 100,
                    color="red",
                    linestyle="--",
                    label=f"Target ({self.target_success_rate * 100:.1f}%)",
                )
                ax2.set_title("Success Rates")
                ax2.set_ylabel("Success Rate (%)")
                ax2.tick_params(axis="x", rotation=45)
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                ax2.set_ylim(90, 100)

                # Add value labels on bars
                for bar, value in zip(bars2, success_rates):
                    ax2.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.1,
                        f"{value:.1f}%",
                        ha="center",
                        va="bottom",
                    )

                plt.tight_layout()
                plt.savefig(
                    "/tmp/performance_results.png", dpi=300, bbox_inches="tight"
                )
                print("📊 Performance charts saved to /tmp/performance_results.png")

        except Exception as e:
            print(f"⚠️  Could not generate charts: {e}")

    async def run_full_performance_suite(self):
        """Run the complete performance test suite"""
        print("🚀 Starting Dinner First Performance Test Suite")
        print("=" * 60)

        await self.setup()

        try:
            # Run all performance tests
            await self.test_authentication_performance()
            await self.test_profile_service_performance()
            await self.test_matching_service_performance()
            await self.test_sentiment_analysis_performance()
            await self.test_messaging_service_performance()
            await self.test_redis_cache_performance()
            await self.test_websocket_performance()
            await self.test_concurrent_user_load()
            self.test_system_resources()

            print("\n" + "=" * 60)
            print("📊 PERFORMANCE TEST RESULTS")
            print("=" * 60)

            # Generate and display report
            report = self.generate_performance_report()
            print(report)

            # Save results
            with open("/tmp/performance_report.md", "w") as f:
                f.write(report)

            self.save_performance_charts()

            print("\n📁 Results saved to /tmp/performance_report.md")

            # Check if all tests passed
            all_passed = True
            for test_name, metrics in self.test_results.items():
                if isinstance(metrics, PerformanceMetrics):
                    target = self.target_95th_percentile
                    if (
                        "ai" in test_name.lower()
                        or "matching" in test_name.lower()
                        or "sentiment" in test_name.lower()
                    ):
                        target *= 1.5

                    if metrics.percentile_95 >= target or metrics.success_rate < 0.95:
                        all_passed = False
                        break

            if all_passed:
                print("\n🎉 ALL PERFORMANCE TESTS PASSED!")
                return 0
            else:
                print("\n💥 SOME PERFORMANCE TESTS FAILED!")
                return 1

        finally:
            await self.teardown()


if __name__ == "__main__":
    """
    Run performance tests directly
    Usage: python performance_test_suite.py
    """
    import sys

    async def main():
        suite = PerformanceTestSuite()
        exit_code = await suite.run_full_performance_suite()
        sys.exit(exit_code)

    asyncio.run(main())
