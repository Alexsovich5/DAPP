-- ClickHouse Analytics Database Initialization for Dinner1
-- Optimized tables for high-volume analytics and real-time insights

-- ================================
-- USER BEHAVIOR TRACKING
-- ================================

-- User events table for all user interactions
CREATE TABLE IF NOT EXISTS user_events (
    event_id UUID DEFAULT generateUUIDv4(),
    user_id UInt32,
    session_id String,
    event_type LowCardinality(String),
    event_category LowCardinality(String),
    page_url String,
    referrer String,
    user_agent String,
    ip_address IPv4,
    country LowCardinality(String),
    city String,
    device_type LowCardinality(String),
    browser LowCardinality(String),
    os LowCardinality(String),
    properties Map(String, String),
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user_id, timestamp)
TTL date + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- Page views for user journey analysis
CREATE TABLE IF NOT EXISTS page_views (
    page_view_id UUID DEFAULT generateUUIDv4(),
    user_id UInt32,
    session_id String,
    page_url String,
    page_title String,
    referrer String,
    time_on_page UInt32,
    scroll_depth UInt8,
    exit_page Bool DEFAULT false,
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user_id, timestamp)
TTL date + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- ================================
-- DATING PLATFORM SPECIFIC EVENTS
-- ================================

-- Profile interactions (views, likes, matches)
CREATE TABLE IF NOT EXISTS profile_interactions (
    interaction_id UUID DEFAULT generateUUIDv4(),
    viewer_user_id UInt32,
    viewed_user_id UInt32,
    interaction_type LowCardinality(String), -- 'view', 'like', 'pass', 'super_like'
    from_recommendation Bool DEFAULT false,
    compatibility_score Float32,
    interaction_duration UInt32, -- seconds spent viewing profile
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, viewer_user_id, timestamp)
TTL date + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- Matching events and outcomes
CREATE TABLE IF NOT EXISTS matching_events (
    match_id UUID DEFAULT generateUUIDv4(),
    user1_id UInt32,
    user2_id UInt32,
    match_type LowCardinality(String), -- 'mutual_like', 'super_match', 'compatibility_match'
    compatibility_score Float32,
    algorithm_version String,
    conversation_started Bool DEFAULT false,
    first_message_time Nullable(DateTime64(3)),
    conversation_length UInt32 DEFAULT 0, -- number of messages
    date_planned Bool DEFAULT false,
    date_completed Bool DEFAULT false,
    match_dissolved Bool DEFAULT false,
    dissolution_reason LowCardinality(String),
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user1_id, timestamp)
TTL date + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- Message events
CREATE TABLE IF NOT EXISTS message_events (
    message_id UUID DEFAULT generateUUIDv4(),
    sender_id UInt32,
    recipient_id UInt32,
    match_id UInt32,
    message_length UInt16,
    message_type LowCardinality(String), -- 'text', 'emoji', 'photo', 'voice', 'revelation'
    is_first_message Bool DEFAULT false,
    response_time_seconds UInt32,
    read_time Nullable(DateTime64(3)),
    flagged_inappropriate Bool DEFAULT false,
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, sender_id, timestamp)
TTL date + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- ================================
-- SOUL BEFORE SKIN SPECIFIC ANALYTICS
-- ================================

-- Revelation tracking
CREATE TABLE IF NOT EXISTS revelation_events (
    revelation_id UUID DEFAULT generateUUIDv4(),
    user_id UInt32,
    match_id UInt32,
    revelation_day UInt8, -- 1-7
    revelation_type LowCardinality(String),
    content_length UInt16,
    response_received Bool DEFAULT false,
    response_time_hours Nullable(UInt32),
    rating Nullable(UInt8), -- 1-5 rating from recipient
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user_id, timestamp)
TTL date + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- Photo reveal events
CREATE TABLE IF NOT EXISTS photo_reveal_events (
    reveal_id UUID DEFAULT generateUUIDv4(),
    user_id UInt32,
    match_id UInt32,
    day_of_reveal UInt8,
    mutual_consent Bool,
    continued_conversation Bool DEFAULT false,
    date_planned_after Bool DEFAULT false,
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user_id, timestamp)
TTL date + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- ================================
-- BUSINESS METRICS
-- ================================

-- User lifecycle events
CREATE TABLE IF NOT EXISTS user_lifecycle (
    event_id UUID DEFAULT generateUUIDv4(),
    user_id UInt32,
    lifecycle_stage LowCardinality(String), -- 'registered', 'onboarded', 'active', 'engaged', 'premium', 'churned'
    previous_stage LowCardinality(String),
    days_in_previous_stage UInt16,
    trigger_event String,
    user_age_days UInt16,
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user_id, timestamp)
TTL date + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- Subscription and revenue events
CREATE TABLE IF NOT EXISTS revenue_events (
    transaction_id UUID DEFAULT generateUUIDv4(),
    user_id UInt32,
    event_type LowCardinality(String), -- 'subscription', 'purchase', 'refund', 'chargeback'
    product_type LowCardinality(String), -- 'premium_monthly', 'premium_yearly', 'super_likes', 'boosts'
    amount_cents UInt32,
    currency LowCardinality(String),
    payment_method LowCardinality(String),
    subscription_length_days Nullable(UInt16),
    is_trial Bool DEFAULT false,
    is_renewal Bool DEFAULT false,
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user_id, timestamp)
TTL date + INTERVAL 7 YEAR -- Keep financial data longer
SETTINGS index_granularity = 8192;

-- ================================
-- SAFETY AND MODERATION ANALYTICS
-- ================================

-- Safety events tracking
CREATE TABLE IF NOT EXISTS safety_events (
    event_id UUID DEFAULT generateUUIDv4(),
    reported_user_id UInt32,
    reporter_user_id UInt32,
    event_type LowCardinality(String), -- 'report', 'block', 'warning', 'suspension', 'ban'
    category LowCardinality(String), -- 'harassment', 'fake_profile', 'inappropriate_content'
    severity LowCardinality(String), -- 'low', 'medium', 'high', 'critical'
    automated_action Bool,
    moderator_id Nullable(UInt32),
    resolution_time_hours Nullable(UInt32),
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, reported_user_id, timestamp)
TTL date + INTERVAL 3 YEAR
SETTINGS index_granularity = 8192;

-- Content moderation events
CREATE TABLE IF NOT EXISTS moderation_events (
    moderation_id UUID DEFAULT generateUUIDv4(),
    user_id UInt32,
    content_type LowCardinality(String), -- 'profile', 'message', 'photo', 'revelation'
    content_id String,
    moderation_result LowCardinality(String), -- 'approved', 'flagged', 'blocked', 'manual_review'
    confidence_score Float32,
    violation_types Array(LowCardinality(String)),
    automated Bool,
    review_time_seconds UInt32,
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user_id, timestamp)
TTL date + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- ================================
-- A/B TESTING FRAMEWORK
-- ================================

-- Experiment assignments
CREATE TABLE IF NOT EXISTS experiment_assignments (
    assignment_id UUID DEFAULT generateUUIDv4(),
    user_id UInt32,
    experiment_id String,
    variant LowCardinality(String),
    assignment_date Date,
    is_active Bool DEFAULT true,
    timestamp DateTime64(3) DEFAULT now64()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(assignment_date)
ORDER BY (assignment_date, experiment_id, user_id)
TTL assignment_date + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- Experiment events
CREATE TABLE IF NOT EXISTS experiment_events (
    event_id UUID DEFAULT generateUUIDv4(),
    user_id UInt32,
    experiment_id String,
    variant LowCardinality(String),
    event_type LowCardinality(String),
    metric_name String,
    metric_value Float64,
    properties Map(String, String),
    timestamp DateTime64(3) DEFAULT now64(),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, experiment_id, user_id, timestamp)
TTL date + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- ================================
-- MATERIALIZED VIEWS FOR REAL-TIME METRICS
-- ================================

-- Daily active users
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_active_users_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY date
AS SELECT
    date,
    uniqExact(user_id) as daily_active_users
FROM user_events
WHERE event_type != 'heartbeat'
GROUP BY date;

-- Hourly matching metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_matching_metrics_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, hour)
AS SELECT
    date,
    toHour(timestamp) as hour,
    count(*) as total_matches,
    countIf(conversation_started) as matches_with_conversation,
    countIf(date_planned) as matches_with_date_planned,
    avg(compatibility_score) as avg_compatibility_score
FROM matching_events
GROUP BY date, hour;

-- Real-time conversion funnel
CREATE MATERIALIZED VIEW IF NOT EXISTS conversion_funnel_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY date
AS SELECT
    date,
    countIf(lifecycle_stage = 'registered') as registrations,
    countIf(lifecycle_stage = 'onboarded') as completed_onboarding,
    countIf(lifecycle_stage = 'active') as became_active,
    countIf(lifecycle_stage = 'engaged') as became_engaged,
    countIf(lifecycle_stage = 'premium') as became_premium
FROM user_lifecycle
GROUP BY date;

-- ================================
-- INDEXES FOR OPTIMIZATION
-- ================================

-- Optimize user event queries
ALTER TABLE user_events ADD INDEX idx_event_type event_type TYPE set(1000) GRANULARITY 1;
ALTER TABLE user_events ADD INDEX idx_user_session (user_id, session_id) TYPE bloom_filter(0.01) GRANULARITY 1;

-- Optimize profile interaction queries
ALTER TABLE profile_interactions ADD INDEX idx_interaction_type interaction_type TYPE set(100) GRANULARITY 1;
ALTER TABLE profile_interactions ADD INDEX idx_compatibility compatibility_score TYPE minmax GRANULARITY 1;

-- Optimize matching queries
ALTER TABLE matching_events ADD INDEX idx_match_type match_type TYPE set(100) GRANULARITY 1;
ALTER TABLE matching_events ADD INDEX idx_conversation_started conversation_started TYPE set(2) GRANULARITY 1;

-- ================================
-- PRIVACY COMPLIANCE FUNCTIONS
-- ================================

-- Function to anonymize user data (GDPR compliance)
CREATE OR REPLACE FUNCTION anonymize_user_events(target_user_id UInt32)
RETURNS String
AS $$
BEGIN
    -- This would be implemented in application code
    -- ClickHouse doesn't support complex stored procedures
    RETURN 'Use application layer for GDPR compliance';
END;
$$;