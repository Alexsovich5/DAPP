#!/usr/bin/env python3
"""
Test script to verify all imports work correctly for Sprint 8 microservices
"""

import importlib
import sys


def _test_import_module(module_name):
    """Test importing a module and return result"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name}: {e}")
        return False


def test_core_imports():
    """Test that core modules can be imported"""
    core_modules = [
        "app.main",
        "app.core.database",
        "app.core.auth_deps",
    ]

    failed_imports = []
    for module in core_modules:
        if not _test_import_module(module):
            failed_imports.append(module)

    assert len(failed_imports) == 0, f"Failed to import: {failed_imports}"


def test_api_router_imports():
    """Test that API router modules can be imported"""
    router_modules = [
        "app.api.v1.routers.auth_router",
        "app.api.v1.routers.users",
        "app.api.v1.routers.profiles",
        "app.api.v1.routers.matches",
    ]

    failed_imports = []
    for module in router_modules:
        if not _test_import_module(module):
            failed_imports.append(module)

    assert len(failed_imports) == 0, f"Failed to import: {failed_imports}"


def main():
    """Test critical imports for Sprint 8"""
    print("Testing Sprint 8 microservices imports...")
    print("=" * 50)

    # Core imports
    core_modules = [
        "app.main",
        "app.core.database",
        "app.core.auth_deps",
        "app.core.redis_cluster_manager",
        "app.core.event_publisher",
        "app.ai.sentiment_analysis",
        "app.ai.ml_model_registry",
        "app.core.advanced_caching",
    ]

    # API router imports
    router_modules = [
        "app.api.v1.routers.auth_router",
        "app.api.v1.routers.users",
        "app.api.v1.routers.profiles",
        "app.api.v1.routers.matches",
        "app.api.v1.routers.messages",
    ]

    failed_imports = []

    print("\nCore modules:")
    for module in core_modules:
        if not _test_import_module(module):
            failed_imports.append(module)

    print("\nAPI router modules:")
    for module in router_modules:
        if not _test_import_module(module):
            failed_imports.append(module)

    print("\n" + "=" * 50)
    if failed_imports:
        print(f"❌ {len(failed_imports)} imports failed:")
        for module in failed_imports:
            print(f"  - {module}")
        return 1
    else:
        print("✅ All imports successful!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
