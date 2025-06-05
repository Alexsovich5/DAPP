from fastapi import Request
import time
import logging
from typing import Callable
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def log_requests_middleware(request: Request, call_next: Callable):
    """
    Middleware to log all requests with detailed information for debugging
    """
    # Generate a unique request ID for tracking
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Log initial request information
    log_message = (
        f"Request {request_id} started: " f"{request.method} {request.url.path}"
    )
    logger.info(log_message)

    # Get request body if it exists (for better debugging)
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            # Clone the request body stream to inspect without consuming it
            body_bytes = await request.body()
            # Reset the body for downstream handlers
            request._body = body_bytes
            try:
                body = json.loads(body_bytes)
                logger.info(f"Request {request_id} body: {json.dumps(body)}")
            except Exception:
                logger.info(f"Request {request_id} body: [non-JSON data]")
        except Exception as e:
            logger.error(f"Error parsing request body: {str(e)}")

    # Log headers (useful for debugging auth and content-type issues)
    headers = dict(request.headers)
    # Remove sensitive headers
    if "authorization" in headers:
        headers["authorization"] = "Bearer [REDACTED]"
    logger.info(f"Request {request_id} headers: {json.dumps(headers)}")

    # Process the request
    try:
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response status
        log_message = (
            f"Request {request_id} completed: {response.status_code} "
            f"in {process_time:.3f}s"
        )
        logger.info(log_message)

        # Log detailed information for 400 errors
        if response.status_code == 400:
            logger.error(
                f"Bad Request (400) for {request.url.path}: "
                "Check request payload format"
            )

        return response
    except Exception as e:
        # Log exceptions
        process_time = time.time() - start_time
        logger.error(f"Request {request_id} failed after {process_time:.3f}s: {str(e)}")
        raise
