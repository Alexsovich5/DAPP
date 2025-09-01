#!/usr/bin/env python3
"""
Test script to verify all imports work correctly for Sprint 8 microservices
"""

import sys
import importlib
import traceback

def test_import(module_name):
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

def main():
    """Test critical imports for Sprint 8"""
    print("Testing Sprint 8 microservices imports...")
    print("=" * 50)
    
    # Core imports
    core_modules = [
        "app.main",
        "app.core.database", 
        "app.core.auth",
        "app.core.redis_cluster_manager",
        "app.core.event_publisher",
        "app.ai.sentiment_analysis", 
        "app.ai.ml_model_registry",
        "app.core.advanced_caching"
    ]
    
    # API router imports  
    router_modules = [
        "app.api.v1.routers.auth",
        "app.api.v1.routers.users", 
        "app.api.v1.routers.profiles",
        "app.api.v1.routers.matches",
        "app.api.v1.routers.messages"
    ]
    
    failed_imports = []
    
    print("\nCore modules:")
    for module in core_modules:
        if not test_import(module):
            failed_imports.append(module)
    
    print("\nAPI router modules:")
    for module in router_modules:
        if not test_import(module):
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