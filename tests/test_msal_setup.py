"""
Quick test script to validate MSAL implementation locally

Run with:
    python3 test_msal_setup.py
"""

import sys
import asyncio

def test_imports():
    """Test all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        from app.providers.auth_msal import get_auth_msal, EntraIDAuthMSAL
        print("  ✅ auth_msal imports OK")
    except Exception as e:
        print(f"  ❌ auth_msal: {e}")
        return False
    
    try:
        from app.providers.dependencies import (
            get_current_user_id,
            get_graph_token,
            get_current_user_with_graph,
            get_current_user
        )
        print("  ✅ dependencies imports OK")
    except Exception as e:
        print(f"  ❌ dependencies: {e}")
        return False
    
    try:
        from app.providers.graph_client import (
            call_graph_api,
            get_user_profile,
            get_user_manager,
            send_email
        )
        print("  ✅ graph_client imports OK")
    except Exception as e:
        print(f"  ❌ graph_client: {e}")
        return False
    
    try:
        from app.routers.auth import router
        print("  ✅ auth router imports OK")
    except Exception as e:
        print(f"  ❌ auth router: {e}")
        return False
    
    return True


def test_msal_instance():
    """Test MSAL instance creation"""
    print("\n🧪 Testing MSAL instance...")
    
    try:
        from app.providers.auth_msal import get_auth_msal
        auth = get_auth_msal()
        
        # Check attributes
        assert hasattr(auth, 'tenant_id'), "Missing tenant_id"
        assert hasattr(auth, 'client_id'), "Missing client_id"
        assert hasattr(auth, 'msal_app'), "Missing msal_app"
        
        print("  ✅ MSAL instance created successfully")
        print(f"    - Tenant ID: {auth.tenant_id[:20]}..." if auth.tenant_id else "    - Tenant ID: (not configured)")
        print(f"    - Client ID: {auth.client_id[:20]}..." if auth.client_id else "    - Client ID: (not configured)")
        
        return True
    except Exception as e:
        print(f"  ❌ MSAL instance: {e}")
        return False


def test_auth_methods():
    """Test auth methods exist and are callable"""
    print("\n🧪 Testing auth methods...")
    
    try:
        from app.providers.auth_msal import get_auth_msal
        auth = get_auth_msal()
        
        # Check methods
        methods = [
            'get_authorize_url',
            'exchange_code_for_token',
            'refresh_access_token',
            'validate_token',
            'get_logout_url',
            'get_user_info_from_token'
        ]
        
        for method in methods:
            assert hasattr(auth, method), f"Missing method: {method}"
            assert callable(getattr(auth, method)), f"Not callable: {method}"
        
        print(f"  ✅ All {len(methods)} auth methods available")
        return True
    except Exception as e:
        print(f"  ❌ Auth methods: {e}")
        return False


def test_dependencies():
    """Test dependencies are FastAPI-compatible"""
    print("\n🧪 Testing FastAPI dependencies...")
    
    try:
        from fastapi import Depends
        from app.providers.dependencies import (
            get_current_user_id,
            get_graph_token,
            get_current_user_with_graph
        )
        
        # Just check they can be used with Depends()
        dep1 = Depends(get_current_user_id)
        dep2 = Depends(get_graph_token)
        dep3 = Depends(get_current_user_with_graph)
        
        print("  ✅ All dependencies are FastAPI-compatible")
        return True
    except Exception as e:
        print(f"  ❌ Dependencies: {e}")
        return False


async def test_graph_client():
    """Test graph_client functions are async and callable"""
    print("\n🧪 Testing graph_client...")
    
    try:
        from app.providers.graph_client import (
            call_graph_api,
            get_user_profile,
            get_user_manager,
            get_user_photo,
            get_user_groups,
            send_email
        )
        
        functions = {
            'call_graph_api': call_graph_api,
            'get_user_profile': get_user_profile,
            'get_user_manager': get_user_manager,
            'get_user_photo': get_user_photo,
            'get_user_groups': get_user_groups,
            'send_email': send_email,
        }
        
        for name, func in functions.items():
            assert callable(func), f"Not callable: {name}"
            # Check if async
            import inspect
            is_async = inspect.iscoroutinefunction(func)
            assert is_async, f"Not async: {name}"
        
        print(f"  ✅ All {len(functions)} graph functions are async and callable")
        return True
    except Exception as e:
        print(f"  ❌ Graph client: {e}")
        return False


def test_main_app():
    """Test FastAPI app loads without errors"""
    print("\n🧪 Testing FastAPI app startup...")
    
    try:
        from app.main import app
        
        # Check router is included
        routes = [route.path for route in app.routes]
        auth_routes = [r for r in routes if '/login' in r or '/getatoken' in r]
        
        assert len(auth_routes) > 0, "No auth routes found"
        
        print("  ✅ FastAPI app loaded successfully")
        print(f"    - Found {len(routes)} total routes")
        print(f"    - Found auth routes: {auth_routes}")
        
        return True
    except Exception as e:
        print(f"  ❌ FastAPI app: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 MSAL Implementation Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("MSAL Instance", test_msal_instance()))
    results.append(("Auth Methods", test_auth_methods()))
    results.append(("Dependencies", test_dependencies()))
    
    # Run async test
    try:
        asyncio.run(test_graph_client())
        results.append(("Graph Client", True))
    except Exception as e:
        print(f"❌ Graph Client: {e}")
        results.append(("Graph Client", False))
    
    results.append(("FastAPI App", test_main_app()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
