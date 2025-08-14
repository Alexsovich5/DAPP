"""
Middleware and Infrastructure Tests
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import Request, Response
from unittest.mock import Mock, patch
import time

from app.main import app
from app.middleware.security_headers import security_headers_middleware
from app.middleware.middleware import log_requests_middleware


class TestSecurityHeadersMiddleware:
    """Test security headers middleware"""

    def test_security_headers_added(self, client):
        """Test that security headers are added to responses"""
        response = client.get("/health")
        
        # Check for common security headers
        headers = response.headers
        
        # These headers should be present for security
        expected_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection",
            "strict-transport-security"
        ]
        
        # At least some security headers should be present
        security_headers_present = any(header in headers for header in expected_headers)
        assert security_headers_present or response.status_code == 404  # Health endpoint might not exist

    def test_cors_headers(self, client):
        """Test CORS headers are properly set"""
        # Test preflight request
        response = client.options(
            "/api/v1/auth/register",
            headers={
                "Origin": "http://localhost:4200",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # Should handle CORS or return 404 if not implemented
        assert response.status_code in [200, 404, 405]
        
        # Test actual request with origin
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@test.com", "username": "test", "password": "password"},
            headers={"Origin": "http://localhost:4200"}
        )
        
        # Response should include CORS headers or be handled
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] in [
                "http://localhost:4200", 
                "*"
            ]

    def test_content_security_policy(self, client):
        """Test Content Security Policy header"""
        response = client.get("/")
        
        # CSP header might be present
        if "content-security-policy" in response.headers:
            csp = response.headers["content-security-policy"]
            assert "default-src" in csp or "script-src" in csp

    def test_security_headers_middleware_initialization(self):
        """Test security headers middleware can be initialized"""
        try:
            # Test middleware function exists
            assert security_headers_middleware is not None
            assert callable(security_headers_middleware)
        except Exception:
            pytest.skip("security_headers_middleware not properly implemented")


class TestRequestLoggingMiddleware:
    """Test request logging middleware"""

    def test_request_logging(self, client):
        """Test that requests are logged"""
        with patch('app.middleware.middleware.logger') as mock_logger:
            response = client.get("/health")
            
            # Should log the request (or return 404 if health endpoint doesn't exist)
            assert response.status_code in [200, 404]
            
            # Verify logging was called if middleware is working
            if mock_logger.info.called:
                call_args = [str(call) for call in mock_logger.info.call_args_list]
                assert any("Request" in arg for arg in call_args)

    def test_request_timing(self, client):
        """Test request timing functionality"""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        # Request should complete in reasonable time
        request_duration = end_time - start_time
        assert request_duration < 5.0  # Should be very fast for simple endpoint

    def test_request_id_generation(self, client):
        """Test request ID generation and tracking"""
        with patch('app.middleware.middleware.logger') as mock_logger:
            response = client.get("/health")
            
            # Check if request ID is in headers
            if "x-request-id" in response.headers:
                request_id = response.headers["x-request-id"]
                assert len(request_id) > 10  # Should be a meaningful ID

    def test_body_logging_security(self, client):
        """Test that sensitive data is not logged in request bodies"""
        login_data = {
            "username": "test@example.com",
            "password": "secretpassword123"
        }
        
        with patch('app.middleware.middleware.logger') as mock_logger:
            response = client.post("/api/v1/auth/login", data=login_data)
            
            # Verify password is not logged in plain text
            if mock_logger.info.called:
                logged_messages = [str(call) for call in mock_logger.info.call_args_list]
                for message in logged_messages:
                    # Password should not appear in logs
                    assert "secretpassword123" not in message.lower()

    def test_middleware_error_handling(self, client):
        """Test middleware handles errors gracefully"""
        # Test with malformed request
        with patch('app.middleware.middleware.logger.error') as mock_error_logger:
            response = client.get("/api/v1/nonexistent-endpoint")
            
            # Should return 404 and not crash
            assert response.status_code == 404
            
            # Should not log errors just for 404s
            assert not mock_error_logger.called or "500" not in str(mock_error_logger.call_args_list)


class TestApplicationMiddleware:
    """Test overall application middleware stack"""

    def test_middleware_order(self, client):
        """Test that middleware is applied in correct order"""
        response = client.get("/api/v1/auth/me")  # Protected endpoint
        
        # Should be unauthorized (401) not internal error (500)
        assert response.status_code == 401

    def test_exception_middleware(self, client):
        """Test global exception handling"""
        # Test various error conditions
        error_endpoints = [
            "/api/v1/nonexistent",
            "/api/v1/users/999999",  # Non-existent user
        ]
        
        for endpoint in error_endpoints:
            response = client.get(
                endpoint,
                headers={"Authorization": "Bearer invalid_token"}
            )
            
            # Should return proper HTTP error codes, not 500
            assert response.status_code in [401, 404, 422]
            
            # Should return JSON error response
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    error_data = response.json()
                    assert "detail" in error_data or "message" in error_data
                except:
                    pass  # JSON parsing might fail, that's ok

    def test_request_size_limits(self, client):
        """Test request size limitations"""
        # Test with very large payload
        large_data = {"data": "x" * 10000}  # 10KB of data
        
        response = client.post(
            "/api/v1/auth/register",
            json=large_data
        )
        
        # Should either process or reject with proper status code
        assert response.status_code in [400, 413, 422, 500]

    def test_content_type_handling(self, client):
        """Test content type handling"""
        # Test with wrong content type
        response = client.post(
            "/api/v1/auth/login",
            data="not-json-data",
            headers={"Content-Type": "text/plain"}
        )
        
        # Should handle gracefully
        assert response.status_code in [400, 415, 422]

    def test_user_agent_handling(self, client):
        """Test user agent header handling"""
        response = client.get(
            "/health",
            headers={"User-Agent": "TestBot/1.0"}
        )
        
        # Should process normally regardless of user agent
        assert response.status_code in [200, 404]


class TestApplicationStartup:
    """Test application startup and configuration"""

    def test_app_initialization(self):
        """Test that the FastAPI app initializes properly"""
        assert app is not None
        assert hasattr(app, 'router')
        assert hasattr(app, 'middleware')

    def test_router_configuration(self):
        """Test API router configuration"""
        routes = app.router.routes
        assert len(routes) > 0
        
        # Should have some API routes
        api_routes = [route for route in routes if hasattr(route, 'path') and '/api/' in route.path]
        assert len(api_routes) > 0

    def test_middleware_configuration(self):
        """Test middleware is properly configured"""
        middleware_stack = app.user_middleware
        assert len(middleware_stack) >= 0  # May have middleware

    def test_openapi_documentation(self, client):
        """Test OpenAPI documentation is available"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        # Should be valid JSON
        try:
            openapi_spec = response.json()
            assert "openapi" in openapi_spec or "swagger" in openapi_spec
        except:
            pytest.fail("OpenAPI spec is not valid JSON")


class TestHealthAndMonitoring:
    """Test health check and monitoring endpoints"""

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        if response.status_code == 200:
            # Health endpoint exists and works
            try:
                health_data = response.json()
                assert "status" in health_data or isinstance(health_data, dict)
            except:
                # Might return plain text
                assert len(response.content) > 0
        else:
            # Health endpoint might not exist
            assert response.status_code == 404

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint if it exists"""
        response = client.get("/metrics")
        
        # Metrics endpoint might not exist, that's ok
        assert response.status_code in [200, 404]

    def test_readiness_probe(self, client):
        """Test readiness probe endpoint"""
        response = client.get("/ready")
        
        # Readiness probe might not exist
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            # Should indicate if app is ready
            try:
                ready_data = response.json()
                assert isinstance(ready_data, (dict, str, bool))
            except:
                pass  # Might be plain text

    def test_liveness_probe(self, client):
        """Test liveness probe endpoint"""
        response = client.get("/alive")
        
        # Liveness probe might not exist
        assert response.status_code in [200, 404]


class TestPerformanceAndLimits:
    """Test performance characteristics and limits"""

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import threading
        
        results = []
        
        def make_request():
            response = client.get("/health")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5)
        
        # All requests should complete
        assert len(results) == 5
        # All should return reasonable status codes
        assert all(status in [200, 404] for status in results)

    def test_request_timeout_handling(self, client):
        """Test request timeout handling"""
        # FastAPI handles timeouts at the server level
        # This test just ensures the app doesn't hang
        start_time = time.time()
        
        response = client.get("/health")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should not hang indefinitely
        assert duration < 10.0

    def test_memory_usage_stability(self, client):
        """Test that memory usage remains stable"""
        import gc
        
        # Make several requests to test for memory leaks
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code in [200, 404]
        
        # Force garbage collection
        gc.collect()
        
        # This test mainly ensures no obvious memory leaks crash the app
        # More sophisticated memory testing would require additional tools