"""DAPP business metrics + setup helper for Prometheus exposition.

All metrics are registered against the default prometheus_client REGISTRY,
which is what prometheus_fastapi_instrumentator exposes at /metrics. Other
prometheus_client metrics elsewhere in the codebase (cache_*, events_*,
sentiment_*, ml_*) appear in the same exposition automatically.
"""

from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# ---- Counters ---------------------------------------------------------------

users_registered_total = Counter(
    "dapp_users_registered_total",
    "Total successful user registrations.",
)

emotional_onboarding_completed_total = Counter(
    "dapp_emotional_onboarding_completed_total",
    "Total successful completions of the emotional-onboarding flow.",
)

soul_connections_initiated_total = Counter(
    "dapp_soul_connections_initiated_total",
    "Total soul connections initiated (POST /soul-connections/initiate).",
)

revelations_sent_total = Counter(
    "dapp_revelations_sent_total",
    "Total daily revelations created, by day_number (1-7).",
    labelnames=("day_number",),
)

messages_sent_total = Counter(
    "dapp_messages_sent_total",
    "Total messages sent successfully.",
)

login_attempts_total = Counter(
    "dapp_login_attempts_total",
    "Login attempts, labeled by result (success|failure).",
    labelnames=("result",),
)

# ---- Gauges -----------------------------------------------------------------

soul_connections_active = Gauge(
    "dapp_soul_connections_active",
    "Current count of soul connections in non-terminal stages.",
)

# ---- Histograms -------------------------------------------------------------

compatibility_calc_seconds = Histogram(
    "dapp_compatibility_calc_seconds",
    "Time spent in CompatibilityCalculator.calculate_overall_compatibility.",
    buckets=(0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

# ---- Setup ------------------------------------------------------------------


def setup_observability(app: FastAPI) -> None:
    """Mount /metrics on the given FastAPI app and enable HTTP middleware.

    Call once during app startup, after CORS middleware. Excludes /metrics,
    /health, and the health-router endpoints from request instrumentation
    so dashboards aren't dominated by polling traffic.
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/health", "/api/health", "/api/v1/health"],
    )
    instrumentator.instrument(app).expose(
        app, endpoint="/metrics", include_in_schema=False
    )
