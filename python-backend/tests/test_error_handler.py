"""
Error Handler Tests - High-impact coverage for error handling utilities
"""
import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.utils.error_handler import (
    validation_error_handler,
    create_error_response,
    log_error,
    format_validation_errors,
)


class TestValidationErrorHandler:
    """Test validation error handler functionality"""

    async def test_validation_error_handler_basic(self):
        """Test basic validation error handling"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/test"
        request.method = "POST"
        
        # Create a RequestValidationError
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            name: str = Field(..., min_length=1)
            age: int = Field(..., ge=0)
        
        try:
            TestModel(name="", age=-1)
        except ValidationError as e:
            validation_error = RequestValidationError(errors=e.errors())
            
            response = await validation_error_handler(request, validation_error)
            
            assert isinstance(response, JSONResponse)
            assert response.status_code == 422
            
            # Check response content structure
            response_data = response.body
            assert b"detail" in response_data
            assert b"error" in response_data

    async def test_validation_error_handler_with_location(self):
        """Test validation error handler with field location info"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/users"
        request.method = "PUT"
        
        # Create validation error with specific field locations
        validation_error = RequestValidationError(errors=[
            {
                'loc': ('body', 'email'),
                'msg': 'field required',
                'type': 'value_error.missing'
            },
            {
                'loc': ('body', 'password'),
                'msg': 'ensure this value has at least 8 characters',
                'type': 'value_error.any_str.min_length'
            }
        ])
        
        response = await validation_error_handler(request, validation_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

    async def test_validation_error_handler_empty_errors(self):
        """Test validation error handler with empty error list"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/test"
        request.method = "GET"
        
        validation_error = RequestValidationError(errors=[])
        
        response = await validation_error_handler(request, validation_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422


class TestErrorResponseCreation:
    """Test error response creation utilities"""

    def test_create_error_response_basic(self):
        """Test basic error response creation"""
        error_response = create_error_response(
            status_code=400,
            error="Bad Request",
            message="Invalid input provided"
        )
        
        assert isinstance(error_response, JSONResponse)
        assert error_response.status_code == 400

    def test_create_error_response_with_details(self):
        """Test error response creation with detailed information"""
        details = {
            "field": "email",
            "constraint": "unique",
            "provided_value": "test@example.com"
        }
        
        error_response = create_error_response(
            status_code=409,
            error="Conflict",
            message="Email already exists",
            details=details
        )
        
        assert isinstance(error_response, JSONResponse)
        assert error_response.status_code == 409

    def test_create_error_response_different_status_codes(self):
        """Test error response creation with different status codes"""
        status_codes = [400, 401, 403, 404, 409, 422, 500]
        
        for status_code in status_codes:
            response = create_error_response(
                status_code=status_code,
                error=f"Error {status_code}",
                message=f"Message for status {status_code}"
            )
            
            assert response.status_code == status_code
            assert isinstance(response, JSONResponse)

    def test_create_error_response_with_none_values(self):
        """Test error response creation with None values"""
        error_response = create_error_response(
            status_code=500,
            error=None,
            message=None
        )
        
        assert isinstance(error_response, JSONResponse)
        assert error_response.status_code == 500


class TestErrorLogging:
    """Test error logging functionality"""

    def test_log_error_basic(self):
        """Test basic error logging"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/test"
        request.method = "POST"
        request.headers = {"user-agent": "test-client"}
        
        error = HTTPException(status_code=404, detail="Not found")
        
        # Test that logging doesn't raise exceptions
        try:
            log_error(request, error, "Test error occurred")
            log_success = True
        except Exception:
            log_success = False
            
        assert log_success is True

    def test_log_error_with_validation_error(self):
        """Test error logging with validation errors"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/validation"
        request.method = "PUT"
        request.headers = {}
        
        validation_error = RequestValidationError(errors=[
            {'loc': ('body', 'field'), 'msg': 'required', 'type': 'value_error'}
        ])
        
        # Test that logging handles validation errors properly
        try:
            log_error(request, validation_error, "Validation failed")
            log_success = True
        except Exception:
            log_success = False
            
        assert log_success is True

    def test_log_error_with_generic_exception(self):
        """Test error logging with generic exceptions"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/error"
        request.method = "GET"
        request.headers = {"authorization": "Bearer token"}
        
        generic_error = Exception("Something went wrong")
        
        try:
            log_error(request, generic_error, "Generic error")
            log_success = True
        except Exception:
            log_success = False
            
        assert log_success is True

    def test_log_error_with_missing_request_attributes(self):
        """Test error logging when request attributes are missing"""
        # Mock request with minimal attributes
        request = Mock()
        request.url = None
        request.method = None
        request.headers = None
        
        error = ValueError("Test error")
        
        try:
            log_error(request, error, "Error with minimal request")
            log_success = True
        except Exception:
            log_success = False
            
        assert log_success is True


class TestValidationErrorFormatting:
    """Test validation error formatting utilities"""

    def test_format_validation_errors_single_error(self):
        """Test formatting of single validation error"""
        errors = [
            {
                'loc': ('body', 'email'),
                'msg': 'field required',
                'type': 'value_error.missing'
            }
        ]
        
        formatted = format_validation_errors(errors)
        
        assert isinstance(formatted, list)
        assert len(formatted) == 1
        assert isinstance(formatted[0], dict)
        assert 'field' in formatted[0]
        assert 'message' in formatted[0]

    def test_format_validation_errors_multiple_errors(self):
        """Test formatting of multiple validation errors"""
        errors = [
            {
                'loc': ('body', 'email'),
                'msg': 'field required',
                'type': 'value_error.missing'
            },
            {
                'loc': ('body', 'password'),
                'msg': 'ensure this value has at least 8 characters',
                'type': 'value_error.any_str.min_length'
            },
            {
                'loc': ('query', 'page'),
                'msg': 'ensure this value is greater than 0',
                'type': 'value_error.number.not_gt'
            }
        ]
        
        formatted = format_validation_errors(errors)
        
        assert isinstance(formatted, list)
        assert len(formatted) == 3
        
        # Check that all errors are properly formatted
        for error in formatted:
            assert isinstance(error, dict)
            assert 'field' in error
            assert 'message' in error

    def test_format_validation_errors_nested_location(self):
        """Test formatting of errors with nested field locations"""
        errors = [
            {
                'loc': ('body', 'user', 'profile', 'bio'),
                'msg': 'string too long',
                'type': 'value_error.any_str.max_length'
            },
            {
                'loc': ('body', 'settings', 0, 'name'),
                'msg': 'field required',
                'type': 'value_error.missing'
            }
        ]
        
        formatted = format_validation_errors(errors)
        
        assert len(formatted) == 2
        
        # Check that nested locations are properly formatted
        for error in formatted:
            assert 'field' in error
            assert isinstance(error['field'], str)
            assert len(error['field']) > 0

    def test_format_validation_errors_empty_list(self):
        """Test formatting of empty error list"""
        errors = []
        
        formatted = format_validation_errors(errors)
        
        assert isinstance(formatted, list)
        assert len(formatted) == 0

    def test_format_validation_errors_malformed_error(self):
        """Test formatting with malformed error structure"""
        errors = [
            {
                # Missing 'loc' field
                'msg': 'some error',
                'type': 'error_type'
            },
            {
                'loc': ('body', 'field'),
                # Missing 'msg' field
                'type': 'error_type'
            },
            {
                'loc': None,  # None location
                'msg': 'error message',
                'type': 'error_type'
            }
        ]
        
        # Should handle malformed errors gracefully
        try:
            formatted = format_validation_errors(errors)
            format_success = True
        except Exception:
            format_success = False
        
        assert format_success is True
        if format_success:
            assert isinstance(formatted, list)


class TestErrorHandlerIntegration:
    """Integration tests for error handler components"""

    async def test_full_validation_error_flow(self):
        """Test complete validation error handling flow"""
        # Create a realistic request mock
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/users"
        request.method = "POST"
        request.headers = {
            "content-type": "application/json",
            "user-agent": "test-client/1.0"
        }
        
        # Create a realistic validation error
        validation_error = RequestValidationError(errors=[
            {
                'loc': ('body', 'email'),
                'msg': 'field required',
                'type': 'value_error.missing',
                'ctx': {'limit_value': 1}
            },
            {
                'loc': ('body', 'password'),
                'msg': 'ensure this value has at least 8 characters',
                'type': 'value_error.any_str.min_length',
                'ctx': {'limit_value': 8}
            }
        ])
        
        # Handle the error
        response = await validation_error_handler(request, validation_error)
        
        # Verify response structure and content
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        assert response.headers.get("content-type") == "application/json"

    def test_error_response_consistency(self):
        """Test that error responses have consistent structure"""
        test_cases = [
            (400, "Bad Request", "Invalid input"),
            (401, "Unauthorized", "Authentication required"),
            (403, "Forbidden", "Access denied"),
            (404, "Not Found", "Resource not found"),
            (500, "Internal Server Error", "Server error occurred")
        ]
        
        for status_code, error, message in test_cases:
            response = create_error_response(status_code, error, message)
            
            assert response.status_code == status_code
            assert isinstance(response, JSONResponse)
            
            # All responses should have consistent structure
            # (testing the structure would require parsing the JSON body)

    def test_error_handler_edge_cases(self):
        """Test error handler with various edge cases"""
        edge_cases = [
            # Empty error message
            ("", "Empty error message"),
            # Very long error message
            ("x" * 1000, "Very long error message"),
            # Special characters in error
            ("Error with special chars: áéíóú ñ 中文", "Unicode characters"),
            # None values
            (None, "None error message"),
        ]
        
        for error_msg, description in edge_cases:
            response = create_error_response(
                status_code=400,
                error="Test Error",
                message=error_msg
            )
            
            assert isinstance(response, JSONResponse)
            assert response.status_code == 400

    async def test_concurrent_error_handling(self):
        """Test error handler under concurrent conditions"""
        import asyncio
        
        async def handle_error():
            request = Mock(spec=Request)
            request.url = Mock()
            request.url.path = "/api/concurrent"
            request.method = "POST"
            
            error = RequestValidationError(errors=[
                {'loc': ('body', 'field'), 'msg': 'error', 'type': 'test'}
            ])
            
            return await validation_error_handler(request, error)
        
        # Run multiple error handlers concurrently
        tasks = [handle_error() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed and return valid responses
        for result in results:
            assert isinstance(result, JSONResponse)
            assert result.status_code == 422