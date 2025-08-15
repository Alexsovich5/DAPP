import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from dataclasses import asdict

from app.services.user_journey_analytics import (
    UserJourneyAnalyticsService,
    JourneyStage,
    ConversionEvent,
    CohortType,
    UserJourney,
    ConversionFunnel,
    CohortAnalysis
)


class TestUserJourneyAnalyticsService:
    
    @pytest.fixture
    def mock_clickhouse(self):
        return Mock()
    
    @pytest.fixture
    def mock_redis(self):
        mock_redis = Mock()
        mock_redis.get = Mock()
        mock_redis.set = Mock()
        mock_redis.hgetall = Mock()
        mock_redis.hincrby = Mock()
        mock_redis.expire = Mock()
        return mock_redis
    
    @pytest.fixture
    def service(self, mock_clickhouse, mock_redis):
        return UserJourneyAnalyticsService(mock_clickhouse, mock_redis)
    
    @pytest.fixture
    def sample_user_journey(self):
        return UserJourney(
            user_id=123,
            journey_start=datetime.utcnow() - timedelta(days=5),
            current_stage=JourneyStage.DISCOVERY,
            completed_stages=[JourneyStage.REGISTRATION, JourneyStage.ONBOARDING],
            conversion_events=[
                {
                    "event_type": "signed_up",
                    "stage": "registration",
                    "timestamp": datetime.utcnow() - timedelta(days=5),
                    "data": {}
                }
            ],
            stage_durations={"registration": 1.0, "onboarding": 2.5},
            total_journey_time=120.0,
            is_active=True
        )
    
    @pytest.fixture
    def sample_event_data(self):
        return {
            "device_type": "mobile",
            "page_url": "/discovery",
            "user_agent": "Mozilla/5.0..."
        }

    def test_service_initialization(self, service):
        """Test service initialization with standard funnels"""
        assert len(service.standard_funnels) == 4
        assert "user_acquisition" in service.standard_funnels
        assert "matching_funnel" in service.standard_funnels
        assert "soul_before_skin" in service.standard_funnels
        assert "monetization" in service.standard_funnels
        
        # Test stage progressions
        assert service.stage_progressions[JourneyStage.REGISTRATION] == JourneyStage.ONBOARDING
        assert service.stage_progressions[JourneyStage.ONBOARDING] == JourneyStage.PROFILE_CREATION

    @pytest.mark.asyncio
    async def test_track_user_journey_event_new_user(self, service, mock_redis, sample_event_data):
        """Test tracking journey event for new user"""
        # Mock no existing journey
        mock_redis.get.return_value = None
        
        with patch.object(service, '_create_user_journey') as mock_create:
            with patch.object(service, '_update_user_journey') as mock_update:
                with patch.object(service, '_store_user_journey') as mock_store:
                    with patch.object(service, '_update_funnel_metrics') as mock_funnel:
                        mock_journey = Mock()
                        mock_create.return_value = mock_journey
                        
                        result = await service.track_user_journey_event(
                            123, "page_view", JourneyStage.REGISTRATION, sample_event_data
                        )
                        
                        assert result is True
                        mock_create.assert_called_once_with(123, JourneyStage.REGISTRATION)
                        mock_update.assert_called_once()
                        mock_store.assert_called_once()
                        mock_funnel.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_user_journey_event_existing_user(self, service, mock_redis, sample_user_journey, sample_event_data):
        """Test tracking journey event for existing user"""
        # Mock existing journey
        with patch.object(service, '_get_user_journey', return_value=sample_user_journey):
            with patch.object(service, '_update_user_journey') as mock_update:
                with patch.object(service, '_store_user_journey') as mock_store:
                    with patch.object(service, '_update_funnel_metrics') as mock_funnel:
                        result = await service.track_user_journey_event(
                            123, "profile_view", JourneyStage.DISCOVERY, sample_event_data
                        )
                        
                        assert result is True
                        mock_update.assert_called_once_with(
                            sample_user_journey, "profile_view", JourneyStage.DISCOVERY, sample_event_data
                        )

    @pytest.mark.asyncio
    async def test_track_user_journey_event_error(self, service, mock_redis):
        """Test journey event tracking error handling"""
        mock_redis.get.side_effect = Exception("Redis error")
        
        result = await service.track_user_journey_event(
            123, "error_event", JourneyStage.REGISTRATION, {}
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_conversion_funnel_analysis(self, service):
        """Test conversion funnel analysis"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        with patch.object(service, '_get_funnel_user_counts') as mock_counts:
            with patch.object(service, '_calculate_stage_timing') as mock_timing:
                mock_counts.return_value = {
                    "landing_page_view": 1000,
                    "sign_up_start": 800,
                    "sign_up_complete": 600,
                    "email_verification": 500,
                    "onboarding_complete": 400
                }
                mock_timing.return_value = {
                    "landing_page_view_to_sign_up_start": 2.5,
                    "sign_up_start_to_sign_up_complete": 1.0
                }
                
                result = await service.get_conversion_funnel_analysis(
                    "user_acquisition", start_date, end_date
                )
                
                assert isinstance(result, ConversionFunnel)
                assert result.funnel_name == "user_acquisition"
                assert len(result.stages) == 5
                assert "landing_page_view_to_sign_up_start" in result.conversion_rates
                assert result.user_counts["landing_page_view"] == 1000

    @pytest.mark.asyncio
    async def test_get_conversion_funnel_analysis_invalid_funnel(self, service):
        """Test conversion funnel analysis with invalid funnel name"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        with pytest.raises(ValueError, match="Unknown funnel"):
            await service.get_conversion_funnel_analysis(
                "invalid_funnel", start_date, end_date
            )

    @pytest.mark.asyncio
    async def test_get_conversion_funnel_analysis_error(self, service):
        """Test conversion funnel analysis error handling"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        with patch.object(service, '_get_funnel_user_counts') as mock_counts:
            mock_counts.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                await service.get_conversion_funnel_analysis(
                    "user_acquisition", start_date, end_date
                )

    @pytest.mark.asyncio
    async def test_perform_cohort_analysis_registration(self, service):
        """Test cohort analysis for registration cohorts"""
        start_date = datetime.utcnow() - timedelta(days=90)
        end_date = datetime.utcnow()
        
        with patch.object(service, '_analyze_registration_cohorts') as mock_analyze:
            mock_cohorts = [
                CohortAnalysis(
                    cohort_name="Registration 2024-01",
                    cohort_type=CohortType.REGISTRATION_DATE,
                    cohort_period="2024-01",
                    total_users=500,
                    retention_rates={"week_1": 0.75},
                    activity_metrics={"avg_sessions": 8.5},
                    revenue_metrics={"total_revenue": 2500.0}
                )
            ]
            mock_analyze.return_value = mock_cohorts
            
            result = await service.perform_cohort_analysis(
                CohortType.REGISTRATION_DATE, start_date, end_date
            )
            
            assert len(result) == 1
            assert result[0].cohort_name == "Registration 2024-01"
            assert result[0].total_users == 500

    @pytest.mark.asyncio
    async def test_perform_cohort_analysis_match_cohorts(self, service):
        """Test cohort analysis for match cohorts"""
        start_date = datetime.utcnow() - timedelta(days=90)
        end_date = datetime.utcnow()
        
        with patch.object(service, '_analyze_match_cohorts') as mock_analyze:
            mock_analyze.return_value = []
            
            result = await service.perform_cohort_analysis(
                CohortType.FIRST_MATCH_DATE, start_date, end_date
            )
            
            assert result == []
            mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_perform_cohort_analysis_error(self, service):
        """Test cohort analysis error handling"""
        start_date = datetime.utcnow() - timedelta(days=90)
        end_date = datetime.utcnow()
        
        with patch.object(service, '_analyze_registration_cohorts') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis error")
            
            result = await service.perform_cohort_analysis(
                CohortType.REGISTRATION_DATE, start_date, end_date
            )
            
            assert result == []

    @pytest.mark.asyncio
    async def test_get_user_journey_insights(self, service, sample_user_journey):
        """Test getting user journey insights"""
        with patch.object(service, '_get_user_journey', return_value=sample_user_journey):
            with patch.object(service, '_get_behavioral_insights') as mock_behavioral:
                with patch.object(service, '_generate_journey_recommendations') as mock_recommendations:
                    with patch.object(service, '_get_stage_performance_percentile') as mock_percentile:
                        mock_behavioral.return_value = {"engagement_pattern": "evening_active"}
                        mock_recommendations.return_value = [{"type": "engagement"}]
                        mock_percentile.return_value = 0.75
                        
                        result = await service.get_user_journey_insights(123)
                        
                        assert result["user_id"] == 123
                        assert result["journey_summary"]["current_stage"] == "discovery"
                        assert result["journey_summary"]["is_active"] is True
                        assert "behavioral_insights" in result
                        assert "recommendations" in result
                        assert "stage_performance" in result

    @pytest.mark.asyncio
    async def test_get_user_journey_insights_not_found(self, service):
        """Test getting insights for non-existent user journey"""
        with patch.object(service, '_get_user_journey', return_value=None):
            result = await service.get_user_journey_insights(123)
            
            assert result == {"error": "User journey not found"}

    @pytest.mark.asyncio
    async def test_get_user_journey_insights_error(self, service):
        """Test journey insights error handling"""
        with patch.object(service, '_get_user_journey') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            result = await service.get_user_journey_insights(123)
            
            assert result == {}

    @pytest.mark.asyncio
    async def test_identify_journey_bottlenecks(self, service):
        """Test identifying journey bottlenecks"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        with patch.object(service, 'get_conversion_funnel_analysis') as mock_funnel:
            with patch.object(service, '_analyze_stage_performance') as mock_stage:
                # Mock low conversion funnel
                mock_funnel_result = ConversionFunnel(
                    funnel_name="user_acquisition",
                    stages=["stage1", "stage2"],
                    conversion_rates={"stage1_to_stage2": 0.3},  # Low conversion
                    drop_off_rates={"stage1_to_stage2": 0.7},
                    user_counts={"stage1": 100, "stage2": 30},
                    avg_time_between_stages={},
                    analysis_period=(start_date, end_date)
                )
                mock_funnel.return_value = mock_funnel_result
                
                # Mock stage with excessive time
                mock_stage.return_value = {
                    "avg_time_spent": 50.0,
                    "expected_time": 20.0,
                    "user_count": 100
                }
                
                result = await service.identify_journey_bottlenecks(start_date, end_date)
                
                assert "funnel_bottlenecks" in result
                assert "stage_bottlenecks" in result
                assert "recommendations" in result
                assert "user_acquisition" in result["funnel_bottlenecks"]

    @pytest.mark.asyncio
    async def test_identify_journey_bottlenecks_error(self, service):
        """Test bottleneck identification error handling"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        with patch.object(service, 'get_conversion_funnel_analysis') as mock_funnel:
            mock_funnel.side_effect = Exception("Analysis error")
            
            result = await service.identify_journey_bottlenecks(start_date, end_date)
            
            assert result == {}

    @pytest.mark.asyncio
    async def test_get_real_time_funnel_metrics(self, service, mock_redis):
        """Test getting real-time funnel metrics"""
        # Mock Redis data
        mock_redis.hgetall.return_value = {
            b"stage1": b"100",
            b"stage2": b"80",
            b"stage3": b"60"
        }
        
        with patch.object(service, '_count_active_journeys', return_value=450):
            with patch.object(service, '_count_completed_journeys_today', return_value=25):
                with patch.object(service, '_get_avg_journey_time', return_value=72.5):
                    result = await service.get_real_time_funnel_metrics()
                    
                    assert "user_acquisition" in result
                    assert "summary" in result
                    assert result["summary"]["active_journeys"] == 450
                    assert result["summary"]["completed_journeys_today"] == 25

    @pytest.mark.asyncio
    async def test_get_real_time_funnel_metrics_empty_data(self, service, mock_redis):
        """Test real-time metrics with empty Redis data"""
        mock_redis.hgetall.return_value = {}
        
        with patch.object(service, '_count_active_journeys', return_value=0):
            with patch.object(service, '_count_completed_journeys_today', return_value=0):
                with patch.object(service, '_get_avg_journey_time', return_value=0.0):
                    result = await service.get_real_time_funnel_metrics()
                    
                    assert result["user_acquisition"] == {}
                    assert result["summary"]["active_journeys"] == 0

    @pytest.mark.asyncio
    async def test_get_real_time_funnel_metrics_error(self, service, mock_redis):
        """Test real-time metrics error handling"""
        mock_redis.hgetall.side_effect = Exception("Redis error")
        
        result = await service.get_real_time_funnel_metrics()
        
        assert result == {}

    @pytest.mark.asyncio
    async def test_generate_journey_report(self, service):
        """Test generating comprehensive journey report"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        with patch.object(service, '_count_users_in_period', return_value=1500):
            with patch.object(service, '_count_completed_journeys', return_value=450):
                with patch.object(service, 'get_conversion_funnel_analysis') as mock_funnel:
                    with patch.object(service, 'perform_cohort_analysis') as mock_cohort:
                        with patch.object(service, '_generate_user_segmentation') as mock_segment:
                            with patch.object(service, '_generate_report_recommendations') as mock_recommendations:
                                # Mock funnel analysis
                                mock_funnel.return_value = ConversionFunnel(
                                    funnel_name="test",
                                    stages=[],
                                    conversion_rates={},
                                    drop_off_rates={},
                                    user_counts={},
                                    avg_time_between_stages={},
                                    analysis_period=(start_date, end_date)
                                )
                                
                                mock_cohort.return_value = []
                                mock_segment.return_value = {"high_engagement": {"count": 300}}
                                mock_recommendations.return_value = ["recommendation1"]
                                
                                result = await service.generate_journey_report(start_date, end_date)
                                
                                assert "executive_summary" in result
                                assert "funnel_analysis" in result
                                assert "cohort_analysis" in result
                                assert "user_segmentation" in result
                                assert "recommendations" in result
                                assert result["executive_summary"]["total_users"] == 1500
                                assert result["executive_summary"]["completed_journeys"] == 450

    @pytest.mark.asyncio
    async def test_generate_journey_report_error(self, service):
        """Test journey report generation error handling"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        with patch.object(service, '_count_users_in_period') as mock_count:
            mock_count.side_effect = Exception("Database error")
            
            result = await service.generate_journey_report(start_date, end_date)
            
            assert result == {}

    @pytest.mark.asyncio
    async def test_get_user_journey_from_redis(self, service, mock_redis):
        """Test getting user journey from Redis"""
        journey_data = {
            'user_id': 123,
            'journey_start': datetime.utcnow().isoformat(),
            'current_stage': 'discovery',
            'completed_stages': ['registration', 'onboarding'],
            'conversion_events': [],
            'stage_durations': {},
            'total_journey_time': 48.0,
            'is_active': True
        }
        
        mock_redis.get.return_value = str(journey_data)
        
        with patch('builtins.eval', return_value=journey_data):
            result = await service._get_user_journey(123)
            
            assert result is not None
            assert result.user_id == 123

    @pytest.mark.asyncio
    async def test_get_user_journey_not_found(self, service, mock_redis):
        """Test getting non-existent user journey"""
        mock_redis.get.return_value = None
        
        result = await service._get_user_journey(123)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_journey_error(self, service, mock_redis):
        """Test user journey retrieval error handling"""
        mock_redis.get.side_effect = Exception("Redis error")
        
        result = await service._get_user_journey(123)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_create_user_journey(self, service):
        """Test creating new user journey"""
        result = await service._create_user_journey(123, JourneyStage.REGISTRATION)
        
        assert isinstance(result, UserJourney)
        assert result.user_id == 123
        assert result.current_stage == JourneyStage.REGISTRATION
        assert result.completed_stages == []
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_update_user_journey_same_stage(self, service, sample_user_journey):
        """Test updating user journey within same stage"""
        original_events_count = len(sample_user_journey.conversion_events)
        
        await service._update_user_journey(
            sample_user_journey, "profile_view", JourneyStage.DISCOVERY, {"page": "/profiles"}
        )
        
        # Should add conversion event but not change stage
        assert len(sample_user_journey.conversion_events) == original_events_count + 1
        assert sample_user_journey.current_stage == JourneyStage.DISCOVERY

    @pytest.mark.asyncio
    async def test_update_user_journey_stage_progression(self, service, sample_user_journey):
        """Test updating user journey with stage progression"""
        original_stage = sample_user_journey.current_stage
        
        await service._update_user_journey(
            sample_user_journey, "first_match", JourneyStage.MATCHING, {"match_id": 456}
        )
        
        # Should progress to new stage
        assert sample_user_journey.current_stage == JourneyStage.MATCHING
        assert original_stage in sample_user_journey.completed_stages

    @pytest.mark.asyncio
    async def test_store_user_journey(self, service, mock_redis, sample_user_journey):
        """Test storing user journey in Redis"""
        await service._store_user_journey(sample_user_journey)
        
        mock_redis.set.assert_called_once()
        args = mock_redis.set.call_args
        assert f"user_journey:{sample_user_journey.user_id}" in args[0]

    @pytest.mark.asyncio
    async def test_store_user_journey_error(self, service, mock_redis, sample_user_journey):
        """Test user journey storage error handling"""
        mock_redis.set.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception):
            await service._store_user_journey(sample_user_journey)

    @pytest.mark.asyncio
    async def test_update_funnel_metrics(self, service, mock_redis):
        """Test updating real-time funnel metrics"""
        await service._update_funnel_metrics(123, JourneyStage.DISCOVERY, "profile_view")
        
        # Should update metrics for relevant funnels
        mock_redis.hincrby.assert_called()
        mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_update_funnel_metrics_error(self, service, mock_redis):
        """Test funnel metrics update error handling"""
        mock_redis.hincrby.side_effect = Exception("Redis error")
        
        # Should not raise exception
        await service._update_funnel_metrics(123, JourneyStage.DISCOVERY, "profile_view")

    @pytest.mark.asyncio
    async def test_get_funnel_user_counts(self, service):
        """Test getting funnel user counts"""
        stages = ["stage1", "stage2", "stage3"]
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        result = await service._get_funnel_user_counts(stages, start_date, end_date)
        
        assert len(result) == 3
        assert result["stage1"] > result["stage2"] > result["stage3"]  # Funnel drop-off

    def test_calculate_conversion_rates(self, service):
        """Test conversion rate calculation"""
        user_counts = {"stage1": 1000, "stage2": 800, "stage3": 600}
        stages = ["stage1", "stage2", "stage3"]
        
        result = service._calculate_conversion_rates(user_counts, stages)
        
        assert result["stage1_to_stage2"] == 0.8  # 800/1000
        assert result["stage2_to_stage3"] == 0.75  # 600/800

    def test_calculate_conversion_rates_zero_counts(self, service):
        """Test conversion rate calculation with zero counts"""
        user_counts = {"stage1": 0, "stage2": 0}
        stages = ["stage1", "stage2"]
        
        result = service._calculate_conversion_rates(user_counts, stages)
        
        assert result["stage1_to_stage2"] == 0.0

    def test_calculate_drop_off_rates(self, service):
        """Test drop-off rate calculation"""
        user_counts = {"stage1": 1000, "stage2": 800, "stage3": 600}
        stages = ["stage1", "stage2", "stage3"]
        
        result = service._calculate_drop_off_rates(user_counts, stages)
        
        assert result["stage1_to_stage2"] == 0.2  # (1000-800)/1000
        assert result["stage2_to_stage3"] == 0.25  # (800-600)/800

    @pytest.mark.asyncio
    async def test_calculate_stage_timing(self, service):
        """Test stage timing calculation"""
        stages = ["stage1", "stage2", "stage3"]
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        result = await service._calculate_stage_timing(stages, start_date, end_date)
        
        assert "stage1_to_stage2" in result
        assert "stage2_to_stage3" in result
        assert all(isinstance(time, float) for time in result.values())

    @pytest.mark.asyncio
    async def test_analyze_registration_cohorts(self, service):
        """Test registration cohort analysis"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31)
        
        result = await service._analyze_registration_cohorts(start_date, end_date)
        
        assert len(result) == 3  # January, February, March
        assert all(isinstance(cohort, CohortAnalysis) for cohort in result)
        assert all(cohort.cohort_type == CohortType.REGISTRATION_DATE for cohort in result)

    @pytest.mark.asyncio
    async def test_analyze_match_cohorts_empty(self, service):
        """Test match cohort analysis (returns empty)"""
        start_date = datetime.utcnow() - timedelta(days=90)
        end_date = datetime.utcnow()
        
        result = await service._analyze_match_cohorts(start_date, end_date)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_get_behavioral_insights(self, service):
        """Test behavioral insights generation"""
        result = await service._get_behavioral_insights(123)
        
        assert "engagement_pattern" in result
        assert "preferred_features" in result
        assert "interaction_style" in result
        assert "response_time_avg_hours" in result

    @pytest.mark.asyncio
    async def test_generate_journey_recommendations_discovery(self, service, sample_user_journey):
        """Test journey recommendations for discovery stage"""
        sample_user_journey.current_stage = JourneyStage.DISCOVERY
        
        result = await service._generate_journey_recommendations(sample_user_journey)
        
        assert any("liking more profiles" in rec["message"] for rec in result)

    @pytest.mark.asyncio
    async def test_generate_journey_recommendations_incomplete_profile(self, service, sample_user_journey):
        """Test recommendations for incomplete profile"""
        sample_user_journey.completed_stages = [JourneyStage.REGISTRATION]  # Only 1 stage
        
        result = await service._generate_journey_recommendations(sample_user_journey)
        
        assert any("Complete your profile" in rec["message"] for rec in result)

    @pytest.mark.asyncio
    async def test_get_stage_performance_percentile(self, service):
        """Test stage performance percentile calculation"""
        result = await service._get_stage_performance_percentile("discovery", 48.0)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_analyze_stage_performance(self, service):
        """Test stage performance analysis"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        result = await service._analyze_stage_performance(JourneyStage.DISCOVERY, start_date, end_date)
        
        assert "avg_time_spent" in result
        assert "expected_time" in result
        assert "user_count" in result
        assert "completion_rate" in result

    def test_generate_bottleneck_recommendations(self, service):
        """Test bottleneck recommendation generation"""
        bottlenecks = {
            "stage_bottlenecks": {"discovery": {}},
            "funnel_bottlenecks": {"user_acquisition": {}}
        }
        
        result = service._generate_bottleneck_recommendations(bottlenecks)
        
        assert len(result) == 2
        assert any("stages" in rec for rec in result)
        assert any("funnels" in rec for rec in result)

    def test_generate_bottleneck_recommendations_empty(self, service):
        """Test bottleneck recommendations with no bottlenecks"""
        bottlenecks = {"stage_bottlenecks": {}, "funnel_bottlenecks": {}}
        
        result = service._generate_bottleneck_recommendations(bottlenecks)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_count_active_journeys(self, service):
        """Test counting active journeys"""
        result = await service._count_active_journeys()
        
        assert isinstance(result, int)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_count_completed_journeys_today(self, service):
        """Test counting completed journeys today"""
        result = await service._count_completed_journeys_today()
        
        assert isinstance(result, int)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_get_avg_journey_time(self, service):
        """Test getting average journey time"""
        result = await service._get_avg_journey_time()
        
        assert isinstance(result, float)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_generate_user_segmentation(self, service):
        """Test user segmentation generation"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        result = await service._generate_user_segmentation(start_date, end_date)
        
        assert "high_engagement" in result
        assert "moderate_engagement" in result
        assert "low_engagement" in result

    @pytest.mark.asyncio
    async def test_generate_report_recommendations(self, service):
        """Test report recommendation generation"""
        report = {"executive_summary": {"completion_rate": 0.3}}
        
        result = await service._generate_report_recommendations(report)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(rec, str) for rec in result)

    def test_journey_stage_enum(self):
        """Test JourneyStage enum values"""
        assert JourneyStage.REGISTRATION.value == "registration"
        assert JourneyStage.ONBOARDING.value == "onboarding"
        assert JourneyStage.PHOTO_REVEAL.value == "photo_reveal"

    def test_conversion_event_enum(self):
        """Test ConversionEvent enum values"""
        assert ConversionEvent.SIGNED_UP.value == "signed_up"
        assert ConversionEvent.FIRST_MATCH.value == "first_match"
        assert ConversionEvent.BECAME_SUBSCRIBER.value == "became_subscriber"

    def test_cohort_type_enum(self):
        """Test CohortType enum values"""
        assert CohortType.REGISTRATION_DATE.value == "registration_date"
        assert CohortType.FIRST_MATCH_DATE.value == "first_match_date"
        assert CohortType.SUBSCRIPTION_DATE.value == "subscription_date"

    def test_user_journey_dataclass(self):
        """Test UserJourney dataclass"""
        journey = UserJourney(
            user_id=123,
            journey_start=datetime.utcnow(),
            current_stage=JourneyStage.DISCOVERY,
            completed_stages=[],
            conversion_events=[],
            stage_durations={},
            total_journey_time=0.0
        )
        
        assert journey.user_id == 123
        assert journey.current_stage == JourneyStage.DISCOVERY
        assert journey.is_active is True  # Default value

    def test_conversion_funnel_dataclass(self):
        """Test ConversionFunnel dataclass"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        funnel = ConversionFunnel(
            funnel_name="test_funnel",
            stages=["stage1", "stage2"],
            conversion_rates={"stage1_to_stage2": 0.8},
            drop_off_rates={"stage1_to_stage2": 0.2},
            user_counts={"stage1": 100, "stage2": 80},
            avg_time_between_stages={"stage1_to_stage2": 24.0},
            analysis_period=(start_date, end_date)
        )
        
        assert funnel.funnel_name == "test_funnel"
        assert funnel.conversion_rates["stage1_to_stage2"] == 0.8

    def test_cohort_analysis_dataclass(self):
        """Test CohortAnalysis dataclass"""
        cohort = CohortAnalysis(
            cohort_name="Test Cohort",
            cohort_type=CohortType.REGISTRATION_DATE,
            cohort_period="2024-01",
            total_users=500,
            retention_rates={"week_1": 0.75},
            activity_metrics={"avg_sessions": 8.5},
            revenue_metrics={"total_revenue": 2500.0}
        )
        
        assert cohort.cohort_name == "Test Cohort"
        assert cohort.total_users == 500
        assert cohort.retention_rates["week_1"] == 0.75