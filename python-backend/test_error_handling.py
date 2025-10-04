#!/usr/bin/env python3
"""
Comprehensive Error Handling Test - Sprint 4
Tests all error handling and logging improvements
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.error_handlers import (  # noqa: E402
    ActivityTrackingError,
    DatabaseError,
    DinnerAppException,
    ErrorCategory,
    safe_execute,
)
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def test_error_categories():
    """Test error category enumeration"""
    print("🧪 Testing Error Categories...")

    categories = list(ErrorCategory)
    expected_categories = [
        "database_connection",
        "authentication",
        "websocket_connection",
        "activity_logging",
        "realtime_integration",
        "request_validation",
    ]

    found_categories = [cat.value for cat in categories]

    for expected in expected_categories:
        if expected in found_categories:
            print(f"  ✅ Found category: {expected}")
        else:
            print(f"  ❌ Missing category: {expected}")
            return False

    print(f"  ✅ Total categories: {len(categories)}")
    return True


def test_custom_exceptions():
    """Test custom exception classes"""
    print("🧪 Testing Custom Exceptions...")

    try:
        # Test base exception
        base_error = DinnerAppException(
            "Test error",
            category=ErrorCategory.SYSTEM,
            details={"test_key": "test_value"},
            user_message="User-friendly message",
        )

        error_dict = base_error.to_dict()
        required_keys = [
            "error_code",
            "category",
            "message",
            "user_message",
            "details",
            "timestamp",
        ]

        for key in required_keys:
            if key in error_dict:
                print(f"  ✅ Base exception has {key}")
            else:
                print(f"  ❌ Missing key in base exception: {key}")
                return False

        # Test activity tracking error
        activity_error = ActivityTrackingError(
            "Activity test error", activity_type="test_activity"
        )

        if activity_error.category == ErrorCategory.ACTIVITY_LOGGING:
            print("  ✅ ActivityTrackingError has correct category")
        else:
            print(
                f"  ❌ Wrong category for ActivityTrackingError: {activity_error.category}"
            )
            return False

        # Test database error
        db_error = DatabaseError("Database test error")
        if db_error.category == ErrorCategory.DATABASE_CONNECTION:
            print("  ✅ DatabaseError has correct category")
        else:
            print(f"  ❌ Wrong category for DatabaseError: {db_error.category}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Exception testing failed: {str(e)}")
        return False


async def test_safe_execute():
    """Test safe_execute function"""
    print("🧪 Testing Safe Execute Function...")

    # Test successful execution
    async def successful_operation():
        return "success"

    result = await safe_execute(
        "test_operation", successful_operation, fallback_value="fallback"
    )

    if result == "success":
        print("  ✅ Safe execute handles success correctly")
    else:
        print(f"  ❌ Safe execute failed on success: {result}")
        return False

    # Test failed execution with fallback
    async def failing_operation():
        raise Exception("Test failure")

    result = await safe_execute(
        "failing_operation", failing_operation, fallback_value="fallback"
    )

    if result == "fallback":
        print("  ✅ Safe execute handles failure with fallback correctly")
    else:
        print(f"  ❌ Safe execute failed on failure: {result}")
        return False

    # Test with retries
    retry_count = 0

    async def retry_operation():
        nonlocal retry_count
        retry_count += 1
        if retry_count < 3:
            raise Exception("Retry needed")
        return "success_after_retry"

    retry_count = 0  # Reset counter
    result = await safe_execute(
        "retry_operation",
        retry_operation,
        max_retries=3,
        retry_delay=0.01,  # Fast retry for testing
        fallback_value="fallback",
    )

    if result == "success_after_retry":
        print(
            f"  ✅ Safe execute handles retries correctly (tried {retry_count} times)"
        )
    else:
        print(f"  ❌ Safe execute failed on retry: {result}")
        return False

    return True


def test_health_endpoints():
    """Test health monitoring endpoints"""
    print("🧪 Testing Health Monitoring Endpoints...")

    client = TestClient(app)

    # Test basic health check
    response = client.get("/api/v1/health/")
    if response.status_code == 200:
        print("  ✅ Basic health endpoint accessible")
        data = response.json()
        if "status" in data and data["status"] == "healthy":
            print("  ✅ Basic health returns healthy status")
        else:
            print(f"  ❌ Unexpected basic health response: {data}")
            return False
    else:
        print(f"  ❌ Basic health endpoint failed: {response.status_code}")
        return False

    # Test detailed health check
    response = client.get("/api/v1/health/detailed")
    if response.status_code in [200, 503]:  # Both are acceptable
        print(
            f"  ✅ Detailed health endpoint accessible (status: {response.status_code})"
        )
        data = response.json()

        required_fields = ["overall_status", "timestamp", "components"]
        for field in required_fields:
            if field in data:
                print(f"  ✅ Detailed health has {field}")
            else:
                print(f"  ❌ Missing field in detailed health: {field}")
                return False
    else:
        print(f"  ❌ Detailed health endpoint failed: {response.status_code}")
        return False

    # Test system status
    response = client.get("/api/v1/health/status")
    if response.status_code == 200:
        print("  ✅ System status endpoint accessible")
    else:
        print(f"  ❌ System status endpoint failed: {response.status_code}")
        return False

    return True


def test_activity_endpoints_error_handling():
    """Test activity endpoints with error handling"""
    print("🧪 Testing Activity Endpoints Error Handling...")

    client = TestClient(app)

    # Test activity types endpoint
    response = client.get("/api/v1/activity/activity-types")
    if response.status_code == 200:
        print("  ✅ Activity types endpoint works")
    else:
        print(f"  ❌ Activity types endpoint failed: {response.status_code}")
        return False

    # Test invalid activity session start (without auth)
    response = client.post(
        "/api/v1/activity/sessions/start",
        json={"session_id": "test-session", "device_type": "test"},
    )

    if response.status_code == 401:  # Unauthorized - expected
        print("  ✅ Activity session start properly requires auth")
    else:
        print(
            f"  ❌ Unexpected response for unauthenticated request: {response.status_code}"
        )
        return False

    return True


async def test_logging_system():
    """Test logging configuration and functionality"""
    print("🧪 Testing Logging System...")

    try:
        from app.core.logging_config import (  # noqa: E402
            get_logger,
            log_error,
            log_performance,
        )

        # Test logger creation
        logger = get_logger("test.module")
        if logger:
            print("  ✅ Logger creation works")
        else:
            print("  ❌ Logger creation failed")
            return False

        # Test context logger
        context_logger = get_logger("test.context", user_id=123, session_id="test")
        if context_logger:
            print("  ✅ Context logger creation works")
        else:
            print("  ❌ Context logger creation failed")
            return False

        # Test error logging function
        try:
            test_error = Exception("Test error for logging")
            log_error(
                logger,
                test_error,
                context={"test": True},
                error_type="test_error",
            )
            print("  ✅ Error logging function works")
        except Exception as e:
            print(f"  ❌ Error logging failed: {str(e)}")
            return False

        # Test performance logging function
        try:
            log_performance(logger, "test_operation", 150.5, context={"test": True})
            print("  ✅ Performance logging function works")
        except Exception as e:
            print(f"  ❌ Performance logging failed: {str(e)}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Logging system test failed: {str(e)}")
        return False


async def run_comprehensive_error_test():
    """Run all error handling and logging tests"""
    print("🚀 Starting Comprehensive Error Handling Test Suite")
    print("=" * 70)

    tests = [
        ("Error Categories", test_error_categories),
        ("Custom Exceptions", test_custom_exceptions),
        ("Safe Execute Function", test_safe_execute),
        ("Health Endpoints", test_health_endpoints),
        ("Activity Error Handling", test_activity_endpoints_error_handling),
        ("Logging System", test_logging_system),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)

        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} ERROR: {str(e)}")

    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All error handling tests PASSED!")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_error_test())

    print("\n🔧 Error Handling & Logging Features:")
    print("  • Structured JSON logging with context")
    print("  • Custom exception hierarchy with user messages")
    print("  • Safe execution with retry logic")
    print("  • Comprehensive health monitoring")
    print("  • Performance logging with thresholds")
    print("  • Request ID tracking for debugging")
    print("  • Environment-specific logging levels")
    print("  • Component-specific log files")

    print("\n📡 New Health Endpoints:")
    print("  • GET /api/v1/health/ - Basic health check")
    print("  • GET /api/v1/health/detailed - Comprehensive system health")
    print("  • GET /api/v1/health/component/{name} - Component-specific health")
    print("  • GET /api/v1/health/status - Cached system status")
    print("  • GET /api/v1/health/metrics - Health metrics for monitoring")

    if success:
        print("\n🎯 Sprint 4: Comprehensive Error Handling & Logging COMPLETE ✅")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please address issues before proceeding.")
        exit(1)
