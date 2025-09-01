#!/usr/bin/env python3
"""
Sprint 8 Import Validation Script
Tests if Sprint 8 microservices components can be imported safely in CI environment
"""

import importlib.util
import os
import sys
from unittest.mock import Mock


# Mock heavy dependencies for CI
def mock_heavy_dependencies():
    """Mock heavy dependencies that may not be available in CI"""
    # Mock external libraries
    sys.modules["torch"] = Mock()
    sys.modules["transformers"] = Mock()
    sys.modules["sentence_transformers"] = Mock()
    sys.modules["numpy"] = Mock()
    sys.modules["pandas"] = Mock()
    sys.modules["sklearn"] = Mock()
    sys.modules["joblib"] = Mock()

    # Mock Redis components
    redis_mock = Mock()
    redis_mock.Redis = Mock()
    sys.modules["aioredis"] = Mock()
    sys.modules["aioredis"].Redis = Mock()
    sys.modules["redis"] = redis_mock
    sys.modules["rediscluster"] = Mock()
    sys.modules["rediscluster"].RedisCluster = Mock()

    # Mock RabbitMQ
    sys.modules["pika"] = Mock()

    # Mock Prometheus and other dependencies
    sys.modules["prometheus_client"] = Mock()
    sys.modules["structlog"] = Mock()
    sys.modules["aio_pika"] = Mock()

    # Mock aioredis exceptions
    aioredis_mock = Mock()
    aioredis_mock.exceptions = Mock()
    aioredis_mock.exceptions.RedisError = Exception
    sys.modules["aioredis"] = aioredis_mock
    sys.modules["aioredis.exceptions"] = aioredis_mock.exceptions


def test_sprint8_components():
    """Test importing Sprint 8 components"""

    # Mock dependencies first
    mock_heavy_dependencies()

    # Get the correct path relative to script location
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(script_dir))
    
    test_files = [
        os.path.join(backend_dir, "app/core/redis_cluster_manager.py"),
        os.path.join(backend_dir, "app/core/event_publisher.py"),
        os.path.join(backend_dir, "app/ai/sentiment_analysis.py"), 
        os.path.join(backend_dir, "app/ai/ml_model_registry.py"),
        os.path.join(backend_dir, "app/core/advanced_caching.py"),
    ]

    success_count = 0
    total_count = len(test_files)

    print("Testing Sprint 8 Microservices Components...")
    print("=" * 50)

    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                spec = importlib.util.spec_from_file_location("test_module", file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(f"✅ {file_path}")
                success_count += 1
            except Exception as e:
                print(f"❌ {file_path}: {e}")
        else:
            print(f"⚠️  {file_path}: File not found")

    print("=" * 50)
    print(f"Results: {success_count}/{total_count} components loaded successfully")

    return success_count == total_count


if __name__ == "__main__":
    success = test_sprint8_components()
    sys.exit(0 if success else 1)
