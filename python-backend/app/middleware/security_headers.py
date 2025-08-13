"""
Security Headers Middleware for Dinner First API

Implements comprehensive security headers following OWASP recommendations
for web application security, specifically designed for a dating platform
handling sensitive user data.
"""

from fastapi import Request, Response
from typing import Callable
import os
import logging

logger = logging.getLogger(__name__)

# Environment-based configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DEVELOPMENT = ENVIRONMENT == "development"


async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    """
    Add comprehensive security headers to all API responses.
    
    Security headers implemented:
    - Content Security Policy (CSP)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security (HTTPS only)
    - Referrer-Policy
    - Permissions-Policy
    - X-Permitted-Cross-Domain-Policies
    """
    
    try:
        response = await call_next(request)
        
        # Content Security Policy - Restrictive for API
        # Prevents XSS attacks by controlling resource loading
        csp_directives = [
            "default-src 'none'",  # Block all by default
            "script-src 'none'",   # No scripts allowed in API responses
            "style-src 'none'",    # No styles in API responses
            "img-src 'none'",      # No images in API responses
            "font-src 'none'",     # No fonts in API responses
            "connect-src 'self'",  # Allow connections to same origin
            "media-src 'none'",    # No media files
            "object-src 'none'",   # No objects/embeds
            "child-src 'none'",    # No frames/workers
            "frame-ancestors 'none'",  # Cannot be framed
            "form-action 'none'",  # No forms in API responses
            "base-uri 'self'",     # Restrict base URI
            "manifest-src 'none'"  # No web app manifests
        ]
        
        # Development vs Production CSP
        if IS_DEVELOPMENT:
            # Allow localhost for development
            csp_directives[5] = "connect-src 'self' http://localhost:* ws://localhost:*"
        
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Prevent MIME type sniffing attacks
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking attacks - API should never be framed
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict Transport Security - HTTPS enforcement
        if IS_PRODUCTION:
            # 1 year HSTS with includeSubDomains and preload
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        elif request.headers.get("x-forwarded-proto") == "https":
            # Development with HTTPS proxy
            response.headers["Strict-Transport-Security"] = (
                "max-age=86400; includeSubDomains"
            )
        
        # Referrer Policy - Protect user privacy in dating app
        # Only send referrer for same-origin requests
        response.headers["Referrer-Policy"] = "same-origin"
        
        # Permissions Policy - Disable sensitive browser features
        # Critical for dating app privacy
        permissions_policy = [
            "geolocation=()",        # No location access through API
            "camera=()",             # No camera access through API  
            "microphone=()",         # No microphone access through API
            "payment=()",            # No payment API access
            "usb=()",                # No USB device access
            "magnetometer=()",       # No sensor access
            "gyroscope=()",          # No sensor access
            "accelerometer=()",      # No sensor access
            "ambient-light-sensor=()",  # No light sensor
            "autoplay=()",           # No autoplay
            "encrypted-media=()",    # No DRM content
            "fullscreen=()",         # No fullscreen API
            "picture-in-picture=()", # No PiP
            "screen-wake-lock=()",   # No wake lock
            "web-share=()",          # No web share API
        ]
        
        # Allow specific features only for same origin in development
        if IS_DEVELOPMENT:
            permissions_policy.extend([
                "geolocation=(self)",  # Allow for development testing
            ])
        
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)
        
        # Cross-domain policies - restrict cross-domain access
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # Server identification protection
        if "server" in response.headers:
            del response.headers["server"]  # Remove server header if present
        
        # Custom security headers for dating platform
        response.headers["X-Dating-Platform-Security"] = "soul-before-skin"
        
        # Cache control for sensitive API responses
        if "/api/" in str(request.url):
            # Prevent caching of API responses containing user data
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Log security headers application in development
        if IS_DEVELOPMENT and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Applied security headers to {request.method} {request.url.path}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in security headers middleware: {str(e)}")
        # Continue with original response if middleware fails
        response = await call_next(request)
        return response


def get_cors_origins() -> list[str]:
    """
    Get secure CORS origins based on environment.
    
    Returns:
        List of allowed origins with proper security configuration
    """
    base_origins = []
    
    if IS_DEVELOPMENT:
        # Development origins - specific ports only
        base_origins = [
            "http://localhost:4200",    # Angular dev server
            "http://localhost:5001",    # Angular alternate port
            "http://127.0.0.1:4200",   # IP-based access
            "http://127.0.0.1:5001",   # IP-based access
        ]
    
    # Production origins from environment
    env_origins = os.getenv("CORS_ORIGINS", "")
    if env_origins:
        production_origins = [origin.strip() for origin in env_origins.split(",")]
        
        # Validate production origins for security
        validated_origins = []
        for origin in production_origins:
            if IS_PRODUCTION:
                # In production, only allow HTTPS origins
                if origin.startswith("https://") or origin.startswith("http://localhost"):
                    validated_origins.append(origin)
                else:
                    logger.warning(f"Skipping non-HTTPS origin in production: {origin}")
            else:
                # Development allows HTTP
                validated_origins.append(origin)
        
        base_origins.extend(validated_origins)
    
    # Remove duplicates and log configuration
    origins = list(set(base_origins))
    logger.info(f"CORS origins configured for {ENVIRONMENT}: {origins}")
    
    return origins


def get_secure_cors_config() -> dict:
    """
    Get secure CORS configuration for FastAPI CORSMiddleware.
    
    Returns:
        Dictionary with secure CORS settings
    """
    return {
        "allow_origins": get_cors_origins(),
        "allow_credentials": True,  # Required for JWT authentication
        "allow_methods": [
            "GET", 
            "POST", 
            "PUT", 
            "DELETE", 
            "OPTIONS",
            "PATCH"  # For partial updates
        ],
        "allow_headers": [
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization",  # JWT tokens
            "X-Requested-With",
            "X-CSRF-Token",  # CSRF protection
            "Cache-Control",
            "Pragma"
        ],
        "expose_headers": [
            "Content-Range",
            "X-Content-Range", 
            "X-Total-Count",  # For pagination
            "X-Dating-Platform-Security"  # Custom header
        ],
        "max_age": 600,  # 10 minutes preflight cache
    }