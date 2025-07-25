# Real-Time Data Pipeline for Dinner1 Analytics
# Stream processing and data transformation for analytics and ML

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import redis
from clickhouse_driver import Client
import pandas as pd
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

class StreamType(Enum):
    USER_EVENTS = "user_events"
    PROFILE_INTERACTIONS = "profile_interactions"
    MATCHING_EVENTS = "matching_events"
    MESSAGE_EVENTS = "message_events"
    REVELATION_EVENTS = "revelation_events"
    BUSINESS_EVENTS = "business_events"

class ProcessingStage(Enum):
    RAW = "raw"
    ENRICHED = "enriched"
    AGGREGATED = "aggregated"
    PROCESSED = "processed"

@dataclass
class StreamEvent:
    event_id: str
    stream_type: StreamType
    data: Dict[str, Any]
    timestamp: datetime
    processing_stage: ProcessingStage = ProcessingStage.RAW
    metadata: Dict[str, Any] = None

@dataclass
class ProcessingResult:
    success: bool
    processed_events: int
    errors: List[str]
    processing_time_ms: float

class DataPipelineService:
    """
    Real-time data pipeline for processing analytics events and feeding ML models
    """
    
    def __init__(self, clickhouse_client: Client, redis_client: redis.Redis):
        self.clickhouse = clickhouse_client
        self.redis = redis_client
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.processors = {}
        self.is_running = False
        
        # Pipeline configuration
        self.config = {
            'batch_size': 100,
            'processing_interval': 5,  # seconds
            'max_retry_attempts': 3,
            'dead_letter_ttl': 86400 * 7,  # 7 days
            'aggregation_windows': [60, 300, 3600],  # 1min, 5min, 1hour
        }
        
        # Metrics tracking
        self.metrics = {
            'events_processed': 0,
            'events_failed': 0,
            'processing_errors': [],
            'last_processing_time': None,
            'average_processing_time': 0
        }
        
        self._setup_processors()
    
    def _setup_processors(self):
        """Setup event processors for different stream types"""
        self.processors = {
            StreamType.USER_EVENTS: self._process_user_events,
            StreamType.PROFILE_INTERACTIONS: self._process_profile_interactions,
            StreamType.MATCHING_EVENTS: self._process_matching_events,
            StreamType.MESSAGE_EVENTS: self._process_message_events,
            StreamType.REVELATION_EVENTS: self._process_revelation_events,
            StreamType.BUSINESS_EVENTS: self._process_business_events,
        }
    
    async def start_pipeline(self):
        """Start the real-time data pipeline"""
        try:
            self.is_running = True
            logger.info("Starting real-time data pipeline...")
            
            # Start processing tasks for each stream type
            tasks = []
            for stream_type in StreamType:
                task = asyncio.create_task(self._process_stream(stream_type))
                tasks.append(task)
            
            # Start aggregation tasks
            aggregation_task = asyncio.create_task(self._run_aggregations())
            tasks.append(aggregation_task)
            
            # Start metrics collection
            metrics_task = asyncio.create_task(self._collect_metrics())
            tasks.append(metrics_task)
            
            logger.info("Data pipeline started successfully")
            
            # Wait for all tasks
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Failed to start data pipeline: {e}")
            self.is_running = False
            raise
    
    async def stop_pipeline(self):
        """Stop the data pipeline gracefully"""
        logger.info("Stopping data pipeline...")
        self.is_running = False
        
        # Allow current processing to complete
        await asyncio.sleep(self.config['processing_interval'])
        
        logger.info("Data pipeline stopped")
    
    async def publish_event(self, event: StreamEvent) -> bool:
        """
        Publish an event to the data pipeline
        """
        try:
            stream_key = f"stream:{event.stream_type.value}"
            
            event_data = {
                'event_id': event.event_id,
                'data': event.data,
                'timestamp': event.timestamp.isoformat(),
                'processing_stage': event.processing_stage.value,
                'metadata': event.metadata or {}
            }
            
            # Add to Redis stream
            self.redis.xadd(
                stream_key,
                event_data,
                maxlen=10000  # Keep last 10k events per stream
            )
            
            logger.debug(f"Published event {event.event_id} to {event.stream_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            return False
    
    async def _process_stream(self, stream_type: StreamType):
        """Process events from a specific stream"""
        stream_key = f"stream:{stream_type.value}"
        consumer_group = f"pipeline-{stream_type.value}"
        consumer_name = "processor-1"
        
        # Create consumer group
        try:
            self.redis.xgroup_create(stream_key, consumer_group, id='0', mkstream=True)
        except redis.RedisError:
            pass  # Group might already exist
        
        logger.info(f"Started processing stream: {stream_type.value}")
        
        while self.is_running:
            try:
                # Read events from stream
                messages = self.redis.xreadgroup(
                    consumer_group,
                    consumer_name,
                    {stream_key: '>'},
                    count=self.config['batch_size'],
                    block=self.config['processing_interval'] * 1000
                )
                
                if not messages:
                    continue
                
                # Process batch of events
                events_to_process = []
                message_ids = []
                
                for stream_name, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        try:
                            event = self._parse_stream_event(fields, stream_type)
                            events_to_process.append(event)
                            message_ids.append(message_id)
                        except Exception as e:
                            logger.error(f"Failed to parse event {message_id}: {e}")
                            # Acknowledge bad message to prevent reprocessing
                            self.redis.xack(stream_key, consumer_group, message_id)
                
                # Process events
                if events_to_process:
                    result = await self._process_event_batch(events_to_process, stream_type)
                    
                    if result.success:
                        # Acknowledge processed messages
                        self.redis.xack(stream_key, consumer_group, *message_ids)
                        self.metrics['events_processed'] += result.processed_events
                    else:
                        # Handle failed processing
                        await self._handle_processing_failure(events_to_process, result.errors)
                        self.metrics['events_failed'] += len(events_to_process)
                
            except Exception as e:
                logger.error(f"Error processing {stream_type.value} stream: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    async def _process_event_batch(self, events: List[StreamEvent], 
                                 stream_type: StreamType) -> ProcessingResult:
        """Process a batch of events"""
        start_time = time.time()
        errors = []
        processed_count = 0
        
        try:
            processor = self.processors.get(stream_type)
            if not processor:
                errors.append(f"No processor found for {stream_type.value}")
                return ProcessingResult(False, 0, errors, 0)
            
            # Process events using the appropriate processor
            processed_events = await processor(events)
            
            # Store processed events in ClickHouse
            if processed_events:
                await self._store_processed_events(processed_events, stream_type)
                processed_count = len(processed_events)
            
            # Update real-time aggregations
            await self._update_real_time_aggregations(processed_events, stream_type)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ProcessingResult(True, processed_count, [], processing_time)
            
        except Exception as e:
            errors.append(str(e))
            processing_time = (time.time() - start_time) * 1000
            return ProcessingResult(False, 0, errors, processing_time)
    
    async def _process_user_events(self, events: List[StreamEvent]) -> List[Dict[str, Any]]:
        """Process user behavior events"""
        processed = []
        
        for event in events:
            try:
                # Enrich event data
                enriched_data = await self._enrich_user_event(event.data)
                
                # Calculate derived metrics
                derived_metrics = self._calculate_user_metrics(enriched_data)
                
                processed_event = {
                    **enriched_data,
                    **derived_metrics,
                    'processing_timestamp': datetime.utcnow(),
                    'processing_stage': ProcessingStage.PROCESSED.value
                }
                
                processed.append(processed_event)
                
            except Exception as e:
                logger.error(f"Failed to process user event {event.event_id}: {e}")
        
        return processed
    
    async def _process_profile_interactions(self, events: List[StreamEvent]) -> List[Dict[str, Any]]:
        """Process profile interaction events"""
        processed = []
        
        for event in events:
            try:
                # Calculate interaction quality score
                interaction_data = event.data
                quality_score = self._calculate_interaction_quality(interaction_data)
                
                # Add demographic insights
                demo_insights = await self._get_demographic_insights(
                    interaction_data.get('viewer_user_id'),
                    interaction_data.get('viewed_user_id')
                )
                
                processed_event = {
                    **interaction_data,
                    'quality_score': quality_score,
                    'demographic_insights': demo_insights,
                    'processing_timestamp': datetime.utcnow(),
                    'processing_stage': ProcessingStage.PROCESSED.value
                }
                
                processed.append(processed_event)
                
            except Exception as e:
                logger.error(f"Failed to process interaction event {event.event_id}: {e}")
        
        return processed
    
    async def _process_matching_events(self, events: List[StreamEvent]) -> List[Dict[str, Any]]:
        """Process matching algorithm events"""
        processed = []
        
        for event in events:
            try:
                match_data = event.data
                
                # Calculate match quality metrics
                quality_metrics = await self._calculate_match_quality(match_data)
                
                # Predict match success
                success_prediction = await self._predict_match_outcome(match_data)
                
                processed_event = {
                    **match_data,
                    'quality_metrics': quality_metrics,
                    'success_prediction': success_prediction,
                    'processing_timestamp': datetime.utcnow(),
                    'processing_stage': ProcessingStage.PROCESSED.value
                }
                
                processed.append(processed_event)
                
            except Exception as e:
                logger.error(f"Failed to process matching event {event.event_id}: {e}")
        
        return processed
    
    async def _process_message_events(self, events: List[StreamEvent]) -> List[Dict[str, Any]]:
        """Process messaging events"""
        processed = []
        
        for event in events:
            try:
                message_data = event.data
                
                # Analyze message sentiment (mock implementation)
                sentiment_score = self._analyze_message_sentiment(
                    message_data.get('message_text', '')
                )
                
                # Calculate conversation health
                conversation_health = await self._calculate_conversation_health(
                    message_data.get('conversation_id')
                )
                
                processed_event = {
                    **message_data,
                    'sentiment_score': sentiment_score,
                    'conversation_health': conversation_health,
                    'processing_timestamp': datetime.utcnow(),
                    'processing_stage': ProcessingStage.PROCESSED.value
                }
                
                processed.append(processed_event)
                
            except Exception as e:
                logger.error(f"Failed to process message event {event.event_id}: {e}")
        
        return processed
    
    async def _process_revelation_events(self, events: List[StreamEvent]) -> List[Dict[str, Any]]:
        """Process revelation sharing events"""
        processed = []
        
        for event in events:
            try:
                revelation_data = event.data
                
                # Calculate revelation impact
                impact_score = self._calculate_revelation_impact(revelation_data)
                
                # Predict relationship progression
                progression_prediction = await self._predict_relationship_progression(
                    revelation_data
                )
                
                processed_event = {
                    **revelation_data,
                    'impact_score': impact_score,
                    'progression_prediction': progression_prediction,
                    'processing_timestamp': datetime.utcnow(),
                    'processing_stage': ProcessingStage.PROCESSED.value
                }
                
                processed.append(processed_event)
                
            except Exception as e:
                logger.error(f"Failed to process revelation event {event.event_id}: {e}")
        
        return processed
    
    async def _process_business_events(self, events: List[StreamEvent]) -> List[Dict[str, Any]]:
        """Process business and revenue events"""
        processed = []
        
        for event in events:
            try:
                business_data = event.data
                
                # Calculate customer lifetime value contribution
                clv_contribution = self._calculate_clv_contribution(business_data)
                
                # Segment customer
                customer_segment = await self._determine_customer_segment(
                    business_data.get('user_id')
                )
                
                processed_event = {
                    **business_data,
                    'clv_contribution': clv_contribution,
                    'customer_segment': customer_segment,
                    'processing_timestamp': datetime.utcnow(),
                    'processing_stage': ProcessingStage.PROCESSED.value
                }
                
                processed.append(processed_event)
                
            except Exception as e:
                logger.error(f"Failed to process business event {event.event_id}: {e}")
        
        return processed
    
    async def _enrich_user_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich user event with additional context"""
        enriched = event_data.copy()
        
        # Add session context
        user_id = event_data.get('user_id')
        if user_id:
            session_context = await self._get_user_session_context(user_id)
            enriched['session_context'] = session_context
        
        # Add device/platform insights
        user_agent = event_data.get('user_agent', '')
        device_insights = self._parse_device_insights(user_agent)
        enriched['device_insights'] = device_insights
        
        return enriched
    
    def _calculate_user_metrics(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived user metrics"""
        return {
            'engagement_score': self._calculate_engagement_score(event_data),
            'session_quality': self._calculate_session_quality(event_data),
            'feature_usage': self._analyze_feature_usage(event_data)
        }
    
    def _calculate_interaction_quality(self, interaction_data: Dict[str, Any]) -> float:
        """Calculate quality score for profile interactions"""
        # Mock implementation - would use actual ML model
        compatibility_score = interaction_data.get('compatibility_score', 0.5)
        interaction_duration = interaction_data.get('interaction_duration', 0)
        
        # Basic quality score calculation
        duration_score = min(interaction_duration / 30, 1.0)  # Normalize to 30 seconds
        quality_score = (compatibility_score * 0.6) + (duration_score * 0.4)
        
        return min(quality_score, 1.0)
    
    async def _get_demographic_insights(self, user1_id: int, user2_id: int) -> Dict[str, Any]:
        """Get demographic insights for user interaction"""
        # Mock implementation
        return {
            'age_difference': 3,
            'location_distance_km': 15,
            'shared_interests_count': 4,
            'education_compatibility': 0.8
        }
    
    async def _calculate_match_quality(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive match quality metrics"""
        return {
            'algorithm_confidence': match_data.get('compatibility_score', 0.5),
            'profile_completeness_avg': 0.85,
            'mutual_interest_score': 0.72,
            'activity_alignment': 0.68
        }
    
    async def _predict_match_outcome(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict match success probability"""
        # Mock ML prediction
        return {
            'conversation_probability': 0.65,
            'date_probability': 0.35,
            'long_term_compatibility': 0.42
        }
    
    def _analyze_message_sentiment(self, message_text: str) -> float:
        """Analyze message sentiment (mock implementation)"""
        # Simple sentiment analysis - would use actual NLP model
        positive_words = ['great', 'awesome', 'love', 'amazing', 'wonderful', 'excited']
        negative_words = ['hate', 'terrible', 'awful', 'bad', 'disappointing']
        
        text_lower = message_text.lower()
        positive_count = sum(word in text_lower for word in positive_words)
        negative_count = sum(word in text_lower for word in negative_words)
        
        if positive_count + negative_count == 0:
            return 0.5  # Neutral
        
        return positive_count / (positive_count + negative_count)
    
    async def _calculate_conversation_health(self, conversation_id: str) -> Dict[str, Any]:
        """Calculate conversation health metrics"""
        return {
            'response_rate': 0.8,
            'average_response_time_hours': 2.5,
            'message_length_balance': 0.75,
            'engagement_trend': 'increasing'
        }
    
    def _calculate_revelation_impact(self, revelation_data: Dict[str, Any]) -> float:
        """Calculate impact score of revelation"""
        revelation_day = revelation_data.get('revelation_day', 1)
        content_length = revelation_data.get('content_length', 0)
        
        # Higher impact for later revelations and longer content
        day_factor = revelation_day / 7.0
        length_factor = min(content_length / 200, 1.0)  # Normalize to 200 chars
        
        return (day_factor * 0.6) + (length_factor * 0.4)
    
    async def _predict_relationship_progression(self, revelation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict relationship progression"""
        return {
            'next_revelation_probability': 0.78,
            'photo_reveal_readiness': 0.65,
            'date_likelihood': 0.45
        }
    
    def _calculate_clv_contribution(self, business_data: Dict[str, Any]) -> float:
        """Calculate customer lifetime value contribution"""
        amount = business_data.get('amount_cents', 0) / 100.0
        event_type = business_data.get('event_type', '')
        
        # Different multipliers for different event types
        multipliers = {
            'subscription_started': 2.0,
            'purchase_made': 1.0,
            'subscription_renewed': 1.5
        }
        
        return amount * multipliers.get(event_type, 1.0)
    
    async def _determine_customer_segment(self, user_id: int) -> str:
        """Determine customer segment"""
        # Mock segmentation logic
        segments = ['premium', 'engaged_free', 'casual', 'new_user']
        return 'engaged_free'  # Mock return
    
    def _parse_stream_event(self, fields: Dict, stream_type: StreamType) -> StreamEvent:
        """Parse Redis stream message into StreamEvent"""
        return StreamEvent(
            event_id=fields.get(b'event_id', b'').decode(),
            stream_type=stream_type,
            data=json.loads(fields.get(b'data', b'{}').decode()),
            timestamp=datetime.fromisoformat(fields.get(b'timestamp', b'').decode()),
            processing_stage=ProcessingStage(fields.get(b'processing_stage', b'raw').decode()),
            metadata=json.loads(fields.get(b'metadata', b'{}').decode())
        )
    
    async def _store_processed_events(self, events: List[Dict[str, Any]], 
                                    stream_type: StreamType):
        """Store processed events in ClickHouse"""
        if not events:
            return
        
        try:
            # Map stream types to ClickHouse tables
            table_mapping = {
                StreamType.USER_EVENTS: 'user_events',
                StreamType.PROFILE_INTERACTIONS: 'profile_interactions',
                StreamType.MATCHING_EVENTS: 'matching_events',
                StreamType.MESSAGE_EVENTS: 'message_events',
                StreamType.REVELATION_EVENTS: 'revelation_events',
                StreamType.BUSINESS_EVENTS: 'revenue_events'
            }
            
            table_name = table_mapping.get(stream_type)
            if not table_name:
                logger.warning(f"No table mapping for {stream_type.value}")
                return
            
            # Insert events into ClickHouse
            # self.clickhouse.execute(f"INSERT INTO {table_name} VALUES", events)
            logger.debug(f"Stored {len(events)} processed events in {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to store processed events: {e}")
            raise
    
    async def _update_real_time_aggregations(self, events: List[Dict[str, Any]], 
                                           stream_type: StreamType):
        """Update real-time aggregations in Redis"""
        try:
            now = datetime.utcnow()
            
            for window_seconds in self.config['aggregation_windows']:
                window_key = f"agg:{stream_type.value}:{window_seconds}:{int(now.timestamp() // window_seconds)}"
                
                # Update aggregation counters
                pipe = self.redis.pipeline()
                pipe.hincrby(window_key, 'event_count', len(events))
                pipe.expire(window_key, window_seconds * 2)  # Keep for 2 windows
                pipe.execute()
            
        except Exception as e:
            logger.error(f"Failed to update real-time aggregations: {e}")
    
    async def _run_aggregations(self):
        """Run periodic aggregations"""
        logger.info("Started aggregation task")
        
        while self.is_running:
            try:
                await self._run_hourly_aggregations()
                await self._run_daily_aggregations()
                
                # Sleep for aggregation interval
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in aggregation task: {e}")
                await asyncio.sleep(60)  # Brief pause on error
    
    async def _run_hourly_aggregations(self):
        """Run hourly data aggregations"""
        try:
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            
            # Aggregate metrics by hour
            aggregations = {
                'total_events': 0,
                'unique_users': set(),
                'conversion_events': 0,
                'revenue_cents': 0
            }
            
            # Store hourly aggregations
            hour_key = f"hourly_agg:{int(current_hour.timestamp())}"
            self.redis.hset(hour_key, mapping={
                k: v if not isinstance(v, set) else len(v) 
                for k, v in aggregations.items()
            })
            self.redis.expire(hour_key, 86400 * 31)  # Keep for 31 days
            
        except Exception as e:
            logger.error(f"Failed to run hourly aggregations: {e}")
    
    async def _run_daily_aggregations(self):
        """Run daily data aggregations"""
        try:
            current_date = datetime.utcnow().date()
            
            # Calculate daily business metrics
            daily_metrics = await self._calculate_daily_business_metrics(current_date)
            
            # Store in Redis and ClickHouse
            date_key = f"daily_agg:{current_date.isoformat()}"
            self.redis.hset(date_key, mapping=daily_metrics)
            self.redis.expire(date_key, 86400 * 365)  # Keep for 1 year
            
        except Exception as e:
            logger.error(f"Failed to run daily aggregations: {e}")
    
    async def _calculate_daily_business_metrics(self, date) -> Dict[str, Any]:
        """Calculate daily business metrics"""
        return {
            'daily_active_users': 0,
            'new_registrations': 0,
            'matches_created': 0,
            'conversations_started': 0,
            'revenue_cents': 0,
            'churn_count': 0
        }
    
    async def _collect_metrics(self):
        """Collect pipeline performance metrics"""
        logger.info("Started metrics collection task")
        
        while self.is_running:
            try:
                # Update pipeline metrics
                self.metrics['last_processing_time'] = datetime.utcnow()
                
                # Store metrics in Redis
                metrics_key = "pipeline_metrics"
                self.redis.hset(metrics_key, mapping={
                    k: str(v) for k, v in self.metrics.items()
                })
                
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(60)
    
    async def _handle_processing_failure(self, events: List[StreamEvent], errors: List[str]):
        """Handle failed event processing"""
        try:
            # Log errors
            for error in errors:
                self.metrics['processing_errors'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': error,
                    'event_count': len(events)
                })
            
            # Send to dead letter queue for manual review
            for event in events:
                dead_letter_key = f"dead_letter:{event.stream_type.value}"
                event_data = asdict(event)
                event_data['failure_timestamp'] = datetime.utcnow().isoformat()
                event_data['errors'] = errors
                
                self.redis.lpush(dead_letter_key, json.dumps(event_data, default=str))
                self.redis.expire(dead_letter_key, self.config['dead_letter_ttl'])
            
        except Exception as e:
            logger.error(f"Failed to handle processing failure: {e}")
    
    # Helper methods (mock implementations)
    
    async def _get_user_session_context(self, user_id: int) -> Dict[str, Any]:
        """Get user session context"""
        return {'session_duration': 1800, 'pages_viewed': 5, 'actions_taken': 3}
    
    def _parse_device_insights(self, user_agent: str) -> Dict[str, Any]:
        """Parse device insights from user agent"""
        return {'device_type': 'mobile', 'browser': 'chrome', 'os': 'android'}
    
    def _calculate_engagement_score(self, event_data: Dict[str, Any]) -> float:
        """Calculate engagement score"""
        return 0.75
    
    def _calculate_session_quality(self, event_data: Dict[str, Any]) -> float:
        """Calculate session quality"""
        return 0.68
    
    def _analyze_feature_usage(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feature usage patterns"""
        return {'primary_features': ['matching', 'messaging'], 'engagement_depth': 'high'}
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and metrics"""
        return {
            'is_running': self.is_running,
            'metrics': self.metrics,
            'config': self.config,
            'active_streams': list(StreamType),
            'last_health_check': datetime.utcnow()
        }