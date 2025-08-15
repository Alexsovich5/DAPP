"""
Unit tests for error handler utilities
Tests error handling and CORS origin logic without external dependencies
"""

import pytest
import os
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.utils.error_handler import (
    get_error_cors_origin,
    APIError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    CustomValidationError,
    BadRequestError,
    validation_error_handler,
    get_secure_cors_config
)


@pytest.mark.unit
class TestErrorCorsOrigin:
    """Test suite for CORS origin handling in error responses"""
    
    def test_get_cors_origin_exact_match(self):
        """Test CORS origin when request origin matches allowed origins"""
        # Mock request with specific origin
        request = Mock(spec=Request)
        request.headers = {"origin": "http://localhost:4200"}
        
        with patch.dict(os.environ, {
            "CORS_ORIGINS": "http://localhost:4200,http://localhost:5001",
            "ENVIRONMENT": "development"
        }):
            origin = get_error_cors_origin(request)
            assert origin == "http://localhost:4200"
    
    def test_get_cors_origin_no_match_returns_first(self):
        """Test CORS origin when request origin doesn't match, returns first allowed"""
        request = Mock(spec=Request)
        request.headers = {"origin": "http://unauthorized.com"}
        
        with patch.dict(os.environ, {
            "CORS_ORIGINS": "http://localhost:4200,http://localhost:5001",
            "ENVIRONMENT": "production"
        }):
            origin = get_error_cors_origin(request)
            assert origin == "http://localhost:4200"
    
    def test_get_cors_origin_development_mode(self):
        """Test CORS origin includes development origins in development mode"""
        request = Mock(spec=Request)
        request.headers = {"origin": "http://127.0.0.1:4200"}
        
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            origin = get_error_cors_origin(request)
            assert origin == "http://127.0.0.1:4200"
    
    def test_get_cors_origin_no_environment_vars(self):
        """Test CORS origin fallback when no environment variables set"""
        request = Mock(spec=Request)
        request.headers = {"origin": "http://unknown.com"}
        
        with patch.dict(os.environ, {}, clear=True):
            origin = get_error_cors_origin(request)
            assert origin == "http://localhost:4200"  # Fallback
    
    def test_get_cors_origin_empty_origin_header(self):
        """Test CORS origin when request has no origin header"""
        request = Mock(spec=Request)
        request.headers = {}
        
        with patch.dict(os.environ, {
            "CORS_ORIGINS": "http://localhost:4200"
        }):
            origin = get_error_cors_origin(request)
            assert origin == "http://localhost:4200"
    
    def test_get_cors_origin_environment_override(self):
        """Test CORS origin respects environment-specific settings"""
        request = Mock(spec=Request)
        request.headers = {"origin": "http://production.com"}
        
        with patch.dict(os.environ, {
            "CORS_ORIGINS": "http://production.com",
            "ENVIRONMENT": "production"
        }):
            origin = get_error_cors_origin(request)
            assert origin == "http://production.com"


@pytest.mark.unit
class TestAPIError:
    """Test suite for APIError exception class"""
    
    def test_api_error_basic_creation(self):
        """Test basic APIError creation"""
        error = APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request"
        )
        
        assert error.status_code == 400
        assert error.detail == "Bad request"
        assert error.headers is None
    
    def test_api_error_with_headers(self):
        """Test APIError creation with custom headers"""
        headers = {"X-Custom-Header": "test"}
        error = APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers=headers
        )
        
        assert error.status_code == 401
        assert error.detail == "Unauthorized"
        assert error.headers == headers
    
    def test_api_error_inheritance(self):
        """Test that APIError properly inherits from HTTPException"""
        error = APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error"
        )
        
        assert isinstance(error, HTTPException)
        assert isinstance(error, APIError)


@pytest.mark.unit
class TestSpecificErrorClasses:
    """Test suite for specific error classes"""
    
    def test_not_found_error(self):
        """Test NotFoundError creation"""
        error = NotFoundError()
        assert error.status_code == 404
        assert error.detail == "Resource not found"
        
        error_custom = NotFoundError("Custom not found message")
        assert error_custom.detail == "Custom not found message"
    
    def test_unauthorized_error(self):
        """Test UnauthorizedError creation"""
        error = UnauthorizedError()
        assert error.status_code == 401
        assert error.detail == "Not authenticated"
        assert error.headers["WWW-Authenticate"] == "Bearer"
        
        error_custom = UnauthorizedError("Custom auth message")
        assert error_custom.detail == "Custom auth message"
    
    def test_forbidden_error(self):
        """Test ForbiddenError creation"""
        error = ForbiddenError()
        assert error.status_code == 403
        assert error.detail == "Permission denied"
        
        error_custom = ForbiddenError("Custom forbidden message")
        assert error_custom.detail == "Custom forbidden message"
    
    def test_custom_validation_error(self):
        """Test CustomValidationError creation"""
        error = CustomValidationError()
        assert error.status_code == 422
        assert error.detail == "Validation error"
        
        error_custom = CustomValidationError("Custom validation message")
        assert error_custom.detail == "Custom validation message"
    
    def test_bad_request_error(self):
        """Test BadRequestError creation"""
        error = BadRequestError()
        assert error.status_code == 400
        assert error.detail == "Bad request"
        
        error_custom = BadRequestError("Custom bad request message")
        assert error_custom.detail == "Custom bad request message"


@pytest.mark.unit
class TestValidationErrorHandling:
    """Test suite for validation error handling"""
    
    @pytest.mark.asyncio
    async def test_validation_error_handler_basic(self):
        """Test validation_error_handler creates proper response"""
        request = Mock(spec=Request)
        request.headers = {"origin": "http://localhost:4200"}
        
        error = Mock(spec=ValidationError)
        error.errors.return_value = [
            {
                "loc": ("email",),
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
        
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:4200"}):
            response = await validation_error_handler(request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:4200"
    
    @pytest.mark.asyncio
    async def test_validation_error_handler_multiple_errors(self):
        """Test validation_error_handler with multiple validation errors"""
        request = Mock(spec=Request)
        request.headers = {"origin": "http://localhost:4200"}
        
        error = Mock(spec=ValidationError)
        error.errors.return_value = [
            {
                "loc": ("email",),
                "msg": "field required", 
                "type": "value_error.missing"
            },
            {
                "loc": ("password",),
                "msg": "ensure this value has at least 8 characters",
                "type": "value_error.any_str.min_length"
            }
        ]
        
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:4200"}):
            response = await validation_error_handler(request, error)
        
        assert response.status_code == 422
        assert "Access-Control-Allow-Origin" in response.headers
    
    @pytest.mark.asyncio
    async def test_validation_error_handler_nested_fields(self):
        """Test validation_error_handler with nested field errors"""
        request = Mock(spec=Request)
        request.headers = {"origin": "http://localhost:4200"}
        
        error = Mock(spec=ValidationError)
        error.errors.return_value = [
            {
                "loc": ("user", "profile", "email"),
                "msg": "invalid email format",
                "type": "value_error.email"
            }
        ]
        
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:4200"}):
            response = await validation_error_handler(request, error)
        
        assert response.status_code == 422
        # Check that nested field path is properly formatted
        assert "user -> profile -> email" in response.body.decode()


@pytest.mark.unit
class TestSecureCorsConfig:
    """Test suite for secure CORS configuration"""
    
    def test_get_secure_cors_config(self):
        """Test get_secure_cors_config returns proper configuration"""
        config = get_secure_cors_config()
        
        assert "allow_origins" in config
        assert "allow_credentials" in config
        assert "allow_methods" in config
        assert "allow_headers" in config
        assert "expose_headers" in config
        
        # Check specific values
        assert config["allow_credentials"] is True
        assert "http://localhost:4200" in config["allow_origins"]
        assert "GET" in config["allow_methods"]
        assert "Authorization" in config["allow_headers"]


@pytest.mark.unit
@pytest.mark.security
class TestErrorHandlerEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_cors_origin_with_malformed_env_var(self):
        """Test CORS origin handling with malformed environment variable"""
        request = Mock(spec=Request)
        request.headers = {"origin": "http://localhost:4200"}
        
        with patch.dict(os.environ, {"CORS_ORIGINS": ",,http://localhost:4200,,"}):
            origin = get_error_cors_origin(request)
            # Should handle empty strings in split result
            assert origin == "http://localhost:4200"
    
    def test_api_error_with_complex_detail(self):
        """Test APIError with complex detail object"""
        detail = {
            "message": "Complex error",
            "errors": ["error1", "error2"],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        error = APIError(
            status_code=400,
            detail=detail
        )
        
        assert error.detail == detail
        assert error.status_code == 400
    
    def test_cors_origin_empty_environment(self):
        """Test CORS origin with completely empty environment"""
        request = Mock(spec=Request)
        request.headers = {"origin": "http://unknown.com"}
        
        with patch.dict(os.environ, {}, clear=True):
            origin = get_error_cors_origin(request)
            assert origin == "http://localhost:4200"  # Should use fallback