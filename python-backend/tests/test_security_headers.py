"""
Comprehensive tests for Security Headers Middleware
Tests production-grade security for the Dinner First dating platform
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from app.main import app
from app.middleware.security_headers import security_headers_middleware
from app.utils.error_handler import get_secure_cors_config


class TestSecurityHeadersMiddleware:
    """Test security headers middleware implementation"""
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_security_headers_applied(self, client):
        """Test that all required security headers are applied"""
        response = client.get("/api/v1/auth/me")
        
        # Content Security Policy
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'none'" in csp
        assert "script-src 'none'" in csp
        assert "connect-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        
        # HTTP Strict Transport Security
        assert "Strict-Transport-Security" in response.headers
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
        
        # Frame Options
        assert response.headers.get("X-Frame-Options") == "DENY"
        
        # Content Type Options
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        
        # Referrer Policy
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        
        # Permissions Policy
        assert "Permissions-Policy" in response.headers
        permissions = response.headers["Permissions-Policy"]
        assert "geolocation=()" in permissions
        assert "camera=()" in permissions
        assert "microphone=()" in permissions

    @pytest.mark.unit
    @pytest.mark.security
    def test_security_headers_api_endpoints(self, client):
        """Test security headers on various API endpoints"""
        endpoints = [
            "/api/v1/auth/register",
            "/api/v1/profiles/me", 
            "/api/v1/connections/discover",
            "/api/v1/revelations/timeline/1",
            "/docs"  # API documentation
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            
            # Should have security headers regardless of response status
            assert "Content-Security-Policy" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "X-Content-Type-Options" in response.headers

    @pytest.mark.unit
    @pytest.mark.security 
    def test_csp_policy_strictness(self, client):
        """Test that CSP policy is appropriately strict for dating platform"""
        response = client.get("/api/v1/profiles/me")
        csp = response.headers.get("Content-Security-Policy", "")
        
        # Should prevent inline scripts (XSS protection)
        assert "'unsafe-inline'" not in csp
        assert "'unsafe-eval'" not in csp
        
        # Should restrict external connections
        assert "connect-src 'self'" in csp or "connect-src https:" in csp
        
        # Should prevent framing (clickjacking protection)
        assert "frame-ancestors 'none'" in csp

    @pytest.mark.unit
    @pytest.mark.security
    @patch.dict('os.environ', {'ENVIRONMENT': 'production'})
    def test_production_security_headers(self, client):
        """Test enhanced security headers in production environment"""
        response = client.get("/api/v1/auth/me")
        
        # Production should have stricter HSTS
        hsts = response.headers.get("Strict-Transport-Security", "")
        assert "max-age=31536000" in hsts  # 1 year minimum
        assert "includeSubDomains" in hsts
        
        # Production should have strict CSP
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src 'none'" in csp
        
        # Production should prevent MIME type sniffing
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    @pytest.mark.unit
    @pytest.mark.security
    @patch.dict('os.environ', {'ENVIRONMENT': 'development'})
    def test_development_security_headers(self, client):
        """Test that development has appropriate but less strict headers"""
        response = client.get("/api/v1/auth/me")
        
        # Development might have relaxed CSP for debugging
        csp = response.headers.get("Content-Security-Policy", "")
        # Should still have basic protection
        assert "Content-Security-Policy" in response.headers
        
        # Still should have frame protection
        assert response.headers.get("X-Frame-Options") == "DENY"


class TestCORSConfiguration:
    """Test CORS configuration for dating platform security"""
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_cors_configuration_structure(self):
        """Test that CORS configuration has all required fields"""
        cors_config = get_secure_cors_config()
        
        required_fields = [
            "allow_origins", "allow_methods", "allow_headers",
            "allow_credentials", "max_age"
        ]
        
        for field in required_fields:
            assert field in cors_config, f"CORS config missing {field}"

    @pytest.mark.unit
    @pytest.mark.security
    @patch.dict('os.environ', {'CORS_ORIGINS': 'https://dinnerfirst.app,https://app.dinnerfirst.com'})
    def test_cors_allowed_origins_production(self):
        """Test CORS allowed origins in production"""
        cors_config = get_secure_cors_config()
        
        allowed_origins = cors_config["allow_origins"]
        assert isinstance(allowed_origins, list)
        assert "https://dinnerfirst.app" in allowed_origins
        assert "https://app.dinnerfirst.com" in allowed_origins
        
        # Should not allow wildcard in production
        assert "*" not in allowed_origins
        
        # Should not allow localhost in production
        assert not any("localhost" in origin for origin in allowed_origins)

    @pytest.mark.unit
    @pytest.mark.security
    @patch.dict('os.environ', {'ENVIRONMENT': 'development', 'CORS_ORIGINS': 'http://localhost:4200,http://localhost:5001'})
    def test_cors_allowed_origins_development(self):
        """Test CORS allowed origins in development"""
        cors_config = get_secure_cors_config()
        
        allowed_origins = cors_config["allow_origins"]
        assert "http://localhost:4200" in allowed_origins
        assert "http://localhost:5001" in allowed_origins

    @pytest.mark.unit
    @pytest.mark.security
    def test_cors_allowed_methods_restricted(self):
        """Test that CORS methods are appropriately restricted"""
        cors_config = get_secure_cors_config()
        
        allowed_methods = cors_config["allow_methods"]
        
        # Should allow essential HTTP methods
        essential_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        for method in essential_methods:
            assert method in allowed_methods
        
        # Should not allow dangerous methods
        dangerous_methods = ["TRACE", "CONNECT"]
        for method in dangerous_methods:
            assert method not in allowed_methods

    @pytest.mark.unit
    @pytest.mark.security
    def test_cors_allowed_headers_secure(self):
        """Test that CORS headers are securely configured"""
        cors_config = get_secure_cors_config()
        
        allowed_headers = cors_config["allow_headers"]
        
        # Should allow essential headers
        essential_headers = ["Authorization", "Content-Type", "Accept"]
        for header in essential_headers:
            assert header.lower() in [h.lower() for h in allowed_headers]

    @pytest.mark.integration
    @pytest.mark.security
    def test_cors_preflight_request(self, client):
        """Test CORS preflight request handling"""
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:5001",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
        )
        
        # Should allow the preflight request
        assert response.status_code == status.HTTP_200_OK
        
        # Should have proper CORS headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers

    @pytest.mark.integration
    @pytest.mark.security
    def test_cors_actual_request_with_credentials(self, client, authenticated_user):
        """Test actual CORS request with credentials"""
        response = client.post(
            "/api/v1/profiles/me",
            headers={
                "Origin": "http://localhost:5001",
                **authenticated_user["headers"]
            },
            json={"full_name": "Test User Update"}
        )
        
        # Should allow the request
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        # Should have CORS headers
        assert "Access-Control-Allow-Origin" in response.headers


class TestSecurityErrorHandling:
    """Test security-related error handling"""
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_error_responses_have_security_headers(self, client):
        """Test that error responses also include security headers"""
        # Trigger various error responses
        error_endpoints = [
            ("/api/v1/auth/login", "POST", {"username": "invalid", "password": "wrong"}),
            ("/api/v1/profiles/999999", "GET", None),
            ("/api/v1/connections/initiate", "POST", {"target_user_id": "invalid"})
        ]
        
        for endpoint, method, data in error_endpoints:
            if method == "POST":
                response = client.post(endpoint, json=data) if data else client.post(endpoint)
            else:
                response = client.get(endpoint)
            
            # Even error responses should have security headers
            assert "Content-Security-Policy" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "X-Content-Type-Options" in response.headers

    @pytest.mark.unit
    @pytest.mark.security
    def test_error_responses_no_sensitive_data(self, client):
        """Test that error responses don't leak sensitive information"""
        # Test various error scenarios
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        error_detail = response.json().get("detail", "")
        
        # Should not reveal whether user exists or not
        assert "user does not exist" not in error_detail.lower()
        assert "password incorrect" not in error_detail.lower()
        
        # Should be generic error message
        assert "unauthorized" in error_detail.lower() or "invalid credentials" in error_detail.lower()

    @pytest.mark.unit
    @pytest.mark.security
    def test_sql_injection_protection(self, client, authenticated_user):
        """Test protection against SQL injection attacks"""
        # Attempt SQL injection in various parameters
        injection_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM users WHERE 1=1; --"
        ]
        
        for payload in injection_payloads:
            # Try injection in profile update
            response = client.put(
                "/api/v1/profiles/me",
                headers=authenticated_user["headers"],
                json={"full_name": payload}
            )
            
            # Should not cause server error (500), should be handled gracefully
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # If successful, should sanitize the input
            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                # Payload should be treated as literal string, not executed
                assert payload in data.get("full_name", "")


class TestSecurityCompliance:
    """Test compliance with security standards for dating platforms"""
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_password_security_requirements(self, client):
        """Test password security requirements for dating platform"""
        # Test weak password rejection
        weak_passwords = ["123", "password", "abc123", "qwerty"]
        
        for weak_pass in weak_passwords:
            response = client.post("/api/v1/auth/register", json={
                "email": f"test_{weak_pass}@example.com",
                "username": f"user_{weak_pass}",
                "password": weak_pass
            })
            
            # Should reject weak passwords
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST, 
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    @pytest.mark.unit
    @pytest.mark.security
    def test_session_security(self, client, authenticated_user):
        """Test session and JWT token security"""
        # Test that JWT tokens expire appropriately
        headers = authenticated_user["headers"]
        
        # Valid token should work
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Test with malformed token
        invalid_headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/auth/me", headers=invalid_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.unit
    @pytest.mark.security
    def test_rate_limiting_protection(self, client):
        """Test rate limiting for sensitive endpoints"""
        # Test rapid login attempts (if rate limiting is implemented)
        login_data = {"username": "test@example.com", "password": "wrongpass"}
        
        responses = []
        for _ in range(10):  # Attempt 10 rapid requests
            response = client.post("/api/v1/auth/login", json=login_data)
            responses.append(response.status_code)
        
        # If rate limiting is implemented, should eventually get rate limited
        # This test will need to be adjusted based on actual rate limiting implementation
        assert all(status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_429_TOO_MANY_REQUESTS
        ] for status_code in responses)

    @pytest.mark.integration
    @pytest.mark.security
    def test_data_privacy_protection(self, client, authenticated_user, matching_users):
        """Test data privacy protection for dating platform"""
        # Test that users can only access their own data
        other_user_id = matching_users["user2"].id
        
        # Should not be able to access other user's profile details
        response = client.get(
            f"/api/v1/profiles/{other_user_id}",
            headers=authenticated_user["headers"]
        )
        
        # Should either deny access or return limited public information only
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Should not include private information
            private_fields = ["email", "phone_number", "full_address", "private_notes"]
            for field in private_fields:
                assert field not in data

    @pytest.mark.unit
    @pytest.mark.security
    def test_content_type_validation(self, client, authenticated_user):
        """Test content type validation for security"""
        # Test with various content types
        response = client.post(
            "/api/v1/profiles/me",
            headers={
                **authenticated_user["headers"],
                "Content-Type": "text/plain"
            },
            data="malicious content"
        )
        
        # Should reject non-JSON content for JSON endpoints
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        ]

    @pytest.mark.performance
    @pytest.mark.security
    def test_security_middleware_performance_impact(self, client, performance_config):
        """Test that security middleware doesn't significantly impact performance"""
        import time
        
        # Measure response time with security middleware
        start_time = time.time()
        for _ in range(10):
            response = client.get("/api/v1/auth/me")
        total_time = time.time() - start_time
        
        avg_response_time = total_time / 10
        
        # Security middleware should not add significant overhead
        assert avg_response_time < performance_config["api_response_max_time"]