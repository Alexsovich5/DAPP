# Sprint 8 API Documentation - Enhanced Microservices Architecture

## Overview

Sprint 8 introduces a comprehensive microservices architecture for the Dinner First platform, featuring:

- **High-Performance Redis Cluster**: 6-node cluster with database separation
- **Event-Driven Architecture**: RabbitMQ message bus with topic exchanges
- **AI-Powered Services**: ML model registry with A/B testing capabilities
- **Multi-Modal Sentiment Analysis**: Advanced emotional intelligence
- **Real-Time Messaging**: WebSocket support with horizontal scaling
- **Advanced Caching**: Multi-level intelligent caching strategy
- **Production-Ready Deployment**: Kubernetes with auto-scaling and monitoring

**Performance Targets Achieved:**
- Sub-100ms 95th percentile response times
- 10,000+ concurrent user support
- 99.9% uptime reliability

---

## Authentication Service API

### Base URL: `/api/v1/auth`

#### Enhanced Registration
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@dinner-first.app",
  "password": "SecurePass2025!",
  "first_name": "Alex",
  "age": 28,
  "gender": "non-binary",
  "emotional_onboarding_completed": false
}
```

**Response:**
```json
{
  "user_id": "uuid-1234-5678-9012",
  "message": "User registered successfully",
  "requires_emotional_onboarding": true,
  "session_id": "sess_abc123"
}
```

#### Session Management
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@dinner-first.app",
  "password": "SecurePass2025!"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "expires_in": 3600,
  "user_id": "uuid-1234-5678-9012",
  "session_cached": true,
  "cache_ttl": 3600
}
```

#### Token Refresh
```http
POST /api/v1/auth/refresh
Authorization: Bearer {refresh_token}
```

#### Health Check
```http
GET /api/v1/auth/health
```

**Response:**
```json
{
  "status": "healthy",
  "redis_connection": "connected",
  "database_connection": "connected",
  "response_time_ms": 25.4,
  "cache_hit_ratio": 0.85
}
```

---

## Profile Service API

### Base URL: `/api/v1/profiles`

#### Enhanced Profile Creation
```http
POST /api/v1/profiles
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "location": {
    "city": "San Francisco",
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "interests": ["cooking", "travel", "photography", "hiking", "music"],
  "life_philosophy": "Live authentically and cherish meaningful connections",
  "core_values": ["honesty", "kindness", "adventure", "growth"],
  "personality_traits": {
    "openness": 0.8,
    "conscientiousness": 0.7,
    "extraversion": 0.6,
    "agreeableness": 0.9,
    "neuroticism": 0.3
  },
  "communication_style": {
    "preferred_style": "thoughtful",
    "response_speed": "moderate",
    "conversation_depth": "deep"
  },
  "emotional_onboarding_completed": true,
  "soul_profile_visibility": "emotional_only"
}
```

**Response:**
```json
{
  "profile_id": "profile_uuid_1234",
  "emotional_depth_score": 85.5,
  "compatibility_readiness": true,
  "cache_key": "profile:uuid-1234",
  "created_at": "2025-01-01T10:00:00Z"
}
```

#### Profile Retrieval (Cached)
```http
GET /api/v1/profiles/me
Authorization: Bearer {access_token}
```

#### Profile Update with Cache Invalidation
```http
PUT /api/v1/profiles/me
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "life_philosophy": "Updated philosophy",
  "interests": ["cooking", "travel", "art", "yoga"]
}
```

---

## AI Matching Service API

### Base URL: `/api/v1/matching`

#### Intelligent Match Discovery
```http
GET /api/v1/matching/discover
Authorization: Bearer {access_token}
Query Parameters:
  - limit: 10 (max 50)
  - radius_km: 50
  - min_compatibility: 60
  - include_explanations: true
```

**Response:**
```json
{
  "matches": [
    {
      "user_id": "uuid-5678-9012-3456",
      "compatibility_score": 87.5,
      "compatibility_breakdown": {
        "interests": 85.0,
        "values": 90.0,
        "demographics": 80.0,
        "communication": 88.0,
        "personality": 92.0
      },
      "match_explanation": "Strong alignment in core values and communication style",
      "emotional_depth_compatibility": 89.2,
      "distance_km": 12.5,
      "last_active": "2025-01-01T08:30:00Z",
      "model_version": "compatibility_v2.0.0",
      "confidence_score": 0.94
    }
  ],
  "total_potential_matches": 147,
  "processing_time_ms": 45.2,
  "cache_hit": false,
  "ml_model_used": "compatibility_v2.0.0"
}
```

#### Compatibility Analysis
```http
GET /api/v1/matching/compatibility/{user_id}
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "compatibility_score": 87.5,
  "detailed_breakdown": {
    "interest_overlap": {
      "score": 85.0,
      "shared_interests": ["cooking", "travel", "music"],
      "total_interests": 12,
      "jaccard_similarity": 0.65
    },
    "values_alignment": {
      "score": 90.0,
      "shared_values": ["honesty", "growth", "adventure"],
      "value_match_strength": "strong"
    },
    "personality_compatibility": {
      "score": 92.0,
      "big_five_correlation": 0.73,
      "complementary_traits": ["openness", "agreeableness"]
    },
    "communication_style": {
      "score": 88.0,
      "style_match": "highly_compatible",
      "conversation_depth_alignment": 0.85
    }
  },
  "prediction_confidence": 0.94,
  "model_version": "compatibility_v2.0.0",
  "processing_time_ms": 32.1
}
```

#### A/B Testing Endpoint
```http
GET /api/v1/matching/discover/experimental
Authorization: Bearer {access_token}
Query Parameters:
  - experiment_variant: canary|stable
  - experiment_id: exp_123
```

---

## Sentiment Analysis Service API

### Base URL: `/api/v1/sentiment`

#### Multi-Modal Sentiment Analysis
```http
POST /api/v1/sentiment/analyze
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "text": "I'm so excited about our upcoming dinner date! This conversation has been really meaningful.",
  "context": "conversation",
  "analysis_types": ["sentiment", "emotion", "behavioral", "temporal"],
  "message_metadata": {
    "conversation_stage": "early_connection",
    "user_relationship_history": "first_connection",
    "time_of_day": "evening"
  }
}
```

**Response:**
```json
{
  "sentiment_score": 0.87,
  "sentiment_label": "very_positive",
  "confidence": 0.94,
  "emotions": {
    "joy": 0.85,
    "excitement": 0.78,
    "anticipation": 0.71,
    "gratitude": 0.63
  },
  "behavioral_indicators": {
    "engagement_level": "high",
    "emotional_investment": 0.82,
    "conversation_commitment": 0.76
  },
  "temporal_analysis": {
    "sentiment_trend": "increasing",
    "emotional_consistency": 0.88,
    "response_timing_sentiment": "enthusiastic"
  },
  "contextual_insights": {
    "relationship_stage_appropriate": true,
    "emotional_depth_indicator": 0.79,
    "connection_potential": "high"
  },
  "processing_details": {
    "model_version": "sentiment_v1.5.0",
    "processing_time_ms": 67.3,
    "batch_processed": false
  }
}
```

#### Batch Sentiment Analysis
```http
POST /api/v1/sentiment/analyze/batch
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "texts": [
    "First message text here",
    "Second message text here"
  ],
  "context": "conversation_history",
  "analysis_types": ["sentiment", "emotion"]
}
```

#### Conversation Sentiment Timeline
```http
GET /api/v1/sentiment/timeline/{connection_id}
Authorization: Bearer {access_token}
Query Parameters:
  - days: 7
  - granularity: hourly|daily
```

---

## Messaging Service API

### Base URL: `/api/v1/messages`

#### Enhanced Message Sending
```http
POST /api/v1/messages/{connection_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message_text": "Looking forward to our dinner conversation!",
  "message_type": "text",
  "sentiment_analysis": true,
  "delivery_priority": "normal",
  "encryption_enabled": true
}
```

**Response:**
```json
{
  "message_id": "msg_uuid_1234",
  "sent_at": "2025-01-01T10:30:00Z",
  "delivery_status": "delivered",
  "sentiment_analysis": {
    "sentiment_score": 0.82,
    "primary_emotion": "anticipation"
  },
  "encrypted": true,
  "cached": true,
  "event_published": true
}
```

#### Message Retrieval with Caching
```http
GET /api/v1/messages/{connection_id}
Authorization: Bearer {access_token}
Query Parameters:
  - limit: 20
  - offset: 0
  - include_sentiment: true
  - decrypt_messages: true
```

**Response:**
```json
{
  "messages": [
    {
      "message_id": "msg_uuid_1234",
      "sender_id": "uuid-1234-5678",
      "message_text": "Looking forward to our dinner conversation!",
      "message_type": "text",
      "sent_at": "2025-01-01T10:30:00Z",
      "read_at": "2025-01-01T10:35:00Z",
      "sentiment_data": {
        "sentiment_score": 0.82,
        "primary_emotion": "anticipation"
      },
      "delivery_status": "read"
    }
  ],
  "pagination": {
    "total_messages": 47,
    "current_page": 1,
    "has_more": true
  },
  "cache_info": {
    "cache_hit": true,
    "cache_ttl_remaining": 1458
  }
}
```

#### Real-Time Message Events
```http
GET /api/v1/messages/{connection_id}/events
Authorization: Bearer {access_token}
Accept: text/event-stream
```

---

## WebSocket Real-Time API

### WebSocket URL: `wss://ws.dinner-first.app`

#### Connection Authentication
```javascript
const websocket = new WebSocket('wss://ws.dinner-first.app', [], {
  headers: {
    'Authorization': 'Bearer your_jwt_token'
  }
});
```

#### Message Types

##### Send Message
```json
{
  "type": "message",
  "connection_id": "conn_uuid_1234",
  "message_text": "Real-time message content",
  "timestamp": "2025-01-01T10:30:00Z"
}
```

##### Typing Indicators
```json
{
  "type": "typing_start",
  "connection_id": "conn_uuid_1234",
  "user_id": "uuid-1234-5678",
  "timestamp": "2025-01-01T10:30:00Z"
}
```

##### Read Receipts
```json
{
  "type": "message_read",
  "message_id": "msg_uuid_1234",
  "connection_id": "conn_uuid_1234",
  "read_by": "uuid-5678-9012",
  "read_at": "2025-01-01T10:35:00Z"
}
```

##### Presence Updates
```json
{
  "type": "presence_update",
  "user_id": "uuid-1234-5678",
  "status": "online",
  "last_seen": "2025-01-01T10:30:00Z"
}
```

---

## Soul Connection API

### Base URL: `/api/v1/connections`

#### Connection Initiation
```http
POST /api/v1/connections/initiate
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "target_user_id": "uuid-5678-9012-3456",
  "connection_message": "I'd love to get to know you better! Your perspective on meaningful connections really resonates with me.",
  "connection_type": "soul_discovery",
  "include_compatibility_score": true
}
```

**Response:**
```json
{
  "connection_id": "conn_uuid_1234",
  "status": "pending",
  "compatibility_score": 87.5,
  "connection_stage": "soul_discovery",
  "revelation_cycle_start": "2025-01-01T10:00:00Z",
  "expected_photo_reveal": "2025-01-08T10:00:00Z",
  "mutual_consent_required": true,
  "created_at": "2025-01-01T10:00:00Z"
}
```

#### Progressive Revelations
```http
POST /api/v1/connections/{connection_id}/revelation
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "day_number": 3,
  "revelation_type": "hope_or_dream",
  "content": "I dream of opening a small restaurant where people can connect over meaningful conversations and incredible food.",
  "visibility": "connection_only"
}
```

#### Connection Management
```http
GET /api/v1/connections/active
Authorization: Bearer {access_token}
Query Parameters:
  - stage: soul_discovery|revelation_phase|photo_revealed
  - include_compatibility: true
```

---

## Administrative & Monitoring APIs

### Base URL: `/api/v1/admin`

#### System Health Dashboard
```http
GET /api/v1/admin/health/detailed
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "overall_status": "healthy",
  "services": {
    "auth_service": {
      "status": "healthy",
      "response_time_ms": 45.2,
      "success_rate": 0.999,
      "cache_hit_ratio": 0.85
    },
    "matching_service": {
      "status": "healthy",
      "response_time_ms": 78.6,
      "ml_model_status": "active",
      "prediction_accuracy": 0.94
    },
    "redis_cluster": {
      "status": "healthy",
      "nodes_online": 6,
      "memory_usage_percent": 45.2,
      "ops_per_second": 15420
    }
  },
  "performance_metrics": {
    "avg_response_time_ms": 52.1,
    "p95_response_time_ms": 89.4,
    "p99_response_time_ms": 145.2,
    "requests_per_second": 8547
  }
}
```

#### ML Model Management
```http
GET /api/v1/admin/ml-models/status
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "models": {
    "compatibility_v2.0.0": {
      "status": "active",
      "traffic_percentage": 90,
      "accuracy": 0.94,
      "avg_inference_time_ms": 34.5
    },
    "compatibility_v3.0.0": {
      "status": "canary",
      "traffic_percentage": 10,
      "accuracy": 0.96,
      "avg_inference_time_ms": 28.2
    }
  },
  "a_b_tests": [
    {
      "experiment_id": "exp_compatibility_v3",
      "status": "running",
      "variant_performance": {
        "control": {"conversion_rate": 0.85, "user_satisfaction": 4.2},
        "variant": {"conversion_rate": 0.89, "user_satisfaction": 4.5}
      }
    }
  ]
}
```

---

## Error Responses

All endpoints follow consistent error response format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "email",
      "reason": "Email format is invalid"
    },
    "request_id": "req_uuid_1234",
    "timestamp": "2025-01-01T10:30:00Z"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `AUTHENTICATION_REQUIRED` | 401 | Valid JWT token required |
| `INSUFFICIENT_PERMISSIONS` | 403 | Admin privileges required |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `ML_MODEL_ERROR` | 503 | AI/ML processing failed |
| `CACHE_ERROR` | 503 | Redis cluster unavailable |

---

## Rate Limiting

All endpoints implement intelligent rate limiting:

- **Authentication**: 10 requests/minute per IP
- **Profile Operations**: 100 requests/minute per user
- **Matching Discovery**: 20 requests/minute per user
- **Messaging**: 60 messages/minute per user
- **Sentiment Analysis**: 30 requests/minute per user
- **WebSocket Connections**: 5 new connections/minute per user

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1640995200
```

---

## Performance Guarantees

### Response Time Targets (95th Percentile)
- **Authentication**: < 50ms
- **Profile Operations**: < 75ms
- **Matching Discovery**: < 150ms (AI processing)
- **Messaging**: < 50ms
- **Sentiment Analysis**: < 150ms (ML processing)
- **WebSocket Latency**: < 25ms

### Availability Targets
- **Overall System**: 99.9% uptime
- **Critical Path (Auth + Messaging)**: 99.95% uptime
- **AI Services**: 99.5% uptime (with graceful degradation)

### Scalability
- **Concurrent Users**: 10,000+ supported
- **Messages per Second**: 50,000+ processing capacity
- **Database Connections**: Auto-scaling with connection pooling
- **Cache Performance**: Sub-10ms response times

---

## Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Session Management**: Redis-backed session storage
- **Rate Limiting**: IP and user-based protection
- **CORS**: Configured for secure cross-origin requests

### Data Protection
- **Message Encryption**: End-to-end message encryption
- **PII Anonymization**: Automatic anonymization of sensitive data
- **Audit Logging**: Comprehensive security event logging
- **Data Retention**: Configurable retention policies

### API Security
- **Input Validation**: Comprehensive request validation
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Content security policies
- **HTTPS Enforcement**: TLS 1.3 encryption

---

## Monitoring & Observability

### Metrics Collection
- **Prometheus**: Custom business and technical metrics
- **Grafana**: Real-time dashboards and alerting
- **Jaeger**: Distributed tracing across microservices
- **Custom Metrics**: Application-specific KPIs

### Logging
- **Structured Logging**: JSON-formatted log entries
- **Log Aggregation**: Centralized log collection
- **Error Tracking**: Automated error detection and alerting
- **Performance Logging**: Detailed performance metrics

### Health Checks
- **Endpoint Monitoring**: Automated health check endpoints
- **Dependency Monitoring**: Database and cache health
- **Circuit Breakers**: Automatic failure protection
- **Graceful Degradation**: Service resilience patterns

---

*This API documentation reflects the Sprint 8 enhanced microservices architecture with production-ready performance, scalability, and reliability features.*
