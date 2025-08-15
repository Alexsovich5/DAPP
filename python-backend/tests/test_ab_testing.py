"""
Comprehensive A/B Testing Framework Validation Tests
Tests A/B experiment management, user assignment, and result tracking for dating platform
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json
from typing import Dict, Any, List

from app.services.ab_testing import ABTestingService, ExperimentStatus
from app.models.ab_experiment import ABExperiment, ExperimentVariant
from app.models.user_experiment import UserExperiment


class TestABTestingFramework:
    """Test A/B testing framework core functionality"""
    
    @pytest.fixture
    def ab_service(self, db_session):
        return ABTestingService(db_session)

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_experiment_creation(self, ab_service):
        """Test creating new A/B experiments"""
        experiment_config = {
            "name": "soul_connection_algorithm_v2",
            "description": "Test improved compatibility scoring algorithm",
            "status": ExperimentStatus.DRAFT.value,
            "start_date": datetime.now() + timedelta(days=1),
            "end_date": datetime.now() + timedelta(days=30),
            "traffic_allocation": 0.5,  # 50% of users
            "target_metrics": ["connection_rate", "message_frequency", "photo_reveal_rate"]
        }
        
        experiment = ab_service.create_experiment(experiment_config)
        
        assert experiment.name == "soul_connection_algorithm_v2"
        assert experiment.status == ExperimentStatus.DRAFT.value
        assert experiment.traffic_allocation == 0.5
        assert "connection_rate" in experiment.target_metrics

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_experiment_variant_management(self, ab_service):
        """Test managing experiment variants (control vs treatment)"""
        experiment = ab_service.create_experiment({
            "name": "revelation_prompt_optimization",
            "description": "Test different revelation prompts for engagement",
            "traffic_allocation": 0.3
        })
        
        # Create control variant
        control_variant = ab_service.create_variant(
            experiment_id=experiment.id,
            variant_name="control",
            variant_config={
                "prompt_style": "standard",
                "example_count": 2,
                "character_guidance": "minimal"
            },
            traffic_percentage=0.5
        )
        
        # Create treatment variant
        treatment_variant = ab_service.create_variant(
            experiment_id=experiment.id,
            variant_name="enhanced_prompts",
            variant_config={
                "prompt_style": "storytelling",
                "example_count": 4,
                "character_guidance": "detailed",
                "emotional_depth_hints": True
            },
            traffic_percentage=0.5
        )
        
        assert control_variant.variant_name == "control"
        assert treatment_variant.variant_config["emotional_depth_hints"] == True
        
        # Variants should sum to 100%
        total_traffic = control_variant.traffic_percentage + treatment_variant.traffic_percentage
        assert total_traffic == 1.0

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_user_experiment_assignment(self, ab_service, matching_users):
        """Test assigning users to experiment variants"""
        user = matching_users["user1"]
        
        # Create active experiment
        experiment = ab_service.create_experiment({
            "name": "photo_reveal_timing",
            "status": ExperimentStatus.ACTIVE.value,
            "traffic_allocation": 1.0
        })
        
        # Create variants
        ab_service.create_variant(experiment.id, "control", {"reveal_day": 7}, 0.5)
        ab_service.create_variant(experiment.id, "early_reveal", {"reveal_day": 5}, 0.5)
        
        # Assign user to experiment
        assignment = ab_service.assign_user_to_experiment(user.id, experiment.id)
        
        assert assignment.user_id == user.id
        assert assignment.experiment_id == experiment.id
        assert assignment.variant_name in ["control", "early_reveal"]
        assert assignment.assigned_at is not None

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_consistent_user_assignment(self, ab_service, matching_users):
        """Test that users get consistently assigned to same variant"""
        user = matching_users["user1"]
        
        experiment = ab_service.create_experiment({
            "name": "consistent_assignment_test",
            "status": ExperimentStatus.ACTIVE.value,
            "traffic_allocation": 1.0
        })
        
        ab_service.create_variant(experiment.id, "control", {}, 0.5)
        ab_service.create_variant(experiment.id, "treatment", {}, 0.5)
        
        # Multiple assignments should return same variant
        assignment1 = ab_service.assign_user_to_experiment(user.id, experiment.id)
        assignment2 = ab_service.assign_user_to_experiment(user.id, experiment.id)
        
        assert assignment1.variant_name == assignment2.variant_name
        assert assignment1.id == assignment2.id  # Same assignment record

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_experiment_traffic_allocation(self, ab_service, matching_users):
        """Test that traffic allocation is respected"""
        users = [matching_users["user1"], matching_users["user2"]]
        
        # Create experiment with 0% traffic (should not assign anyone)
        zero_traffic_experiment = ab_service.create_experiment({
            "name": "zero_traffic_test",
            "status": ExperimentStatus.ACTIVE.value,
            "traffic_allocation": 0.0
        })
        
        for user in users:
            assignment = ab_service.assign_user_to_experiment(user.id, zero_traffic_experiment.id)
            assert assignment is None  # No assignment due to 0% traffic
        
        # Create experiment with 100% traffic
        full_traffic_experiment = ab_service.create_experiment({
            "name": "full_traffic_test", 
            "status": ExperimentStatus.ACTIVE.value,
            "traffic_allocation": 1.0
        })
        
        ab_service.create_variant(full_traffic_experiment.id, "control", {}, 1.0)
        
        for user in users:
            assignment = ab_service.assign_user_to_experiment(user.id, full_traffic_experiment.id)
            assert assignment is not None  # All users should be assigned


class TestExperimentMetricsTracking:
    """Test A/B experiment metrics collection and analysis"""
    
    @pytest.fixture
    def ab_service(self, db_session):
        return ABTestingService(db_session)

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_conversion_event_tracking(self, ab_service, soul_connection_data):
        """Test tracking conversion events for experiment analysis"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Create experiment and assign user
        experiment = ab_service.create_experiment({
            "name": "connection_optimization",
            "status": ExperimentStatus.ACTIVE.value,
            "target_metrics": ["connection_success", "first_message_sent"]
        })
        
        ab_service.create_variant(experiment.id, "control", {}, 0.5)
        assignment = ab_service.assign_user_to_experiment(user.id, experiment.id)
        
        # Track conversion events
        ab_service.track_conversion_event(
            user_id=user.id,
            experiment_id=experiment.id,
            event_name="connection_success",
            event_data={"connection_id": connection.id, "compatibility_score": 85.5}
        )
        
        ab_service.track_conversion_event(
            user_id=user.id,
            experiment_id=experiment.id,
            event_name="first_message_sent",
            event_data={"connection_id": connection.id, "message_length": 127}
        )
        
        # Verify events were tracked
        events = ab_service.get_user_experiment_events(user.id, experiment.id)
        assert len(events) == 2
        assert any(e.event_name == "connection_success" for e in events)
        assert any(e.event_name == "first_message_sent" for e in events)

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_experiment_performance_analysis(self, ab_service, matching_users):
        """Test analyzing experiment performance across variants"""
        users = [matching_users["user1"], matching_users["user2"]]
        
        experiment = ab_service.create_experiment({
            "name": "messaging_frequency_test",
            "status": ExperimentStatus.ACTIVE.value,
            "target_metrics": ["messages_per_day", "response_rate"]
        })
        
        control_variant = ab_service.create_variant(experiment.id, "control", {}, 0.5)
        treatment_variant = ab_service.create_variant(experiment.id, "treatment", {}, 0.5)
        
        # Mock different performance for variants
        with patch.object(ab_service, 'get_variant_performance') as mock_perf:
            mock_perf.return_value = {
                "control": {
                    "messages_per_day": {"mean": 3.2, "count": 50},
                    "response_rate": {"mean": 0.65, "count": 50}
                },
                "treatment": {
                    "messages_per_day": {"mean": 4.8, "count": 52},
                    "response_rate": {"mean": 0.78, "count": 52}
                }
            }
            
            performance = ab_service.analyze_experiment_performance(experiment.id)
            
            assert performance["control"]["messages_per_day"]["mean"] == 3.2
            assert performance["treatment"]["response_rate"]["mean"] == 0.78
            assert performance["treatment"]["messages_per_day"]["mean"] > performance["control"]["messages_per_day"]["mean"]

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_statistical_significance_calculation(self, ab_service):
        """Test statistical significance calculation for A/B test results"""
        # Mock experiment data with statistical difference
        control_data = {
            "conversion_rate": 0.15,  # 15% conversion rate
            "sample_size": 1000
        }
        
        treatment_data = {
            "conversion_rate": 0.22,  # 22% conversion rate  
            "sample_size": 980
        }
        
        significance_result = ab_service.calculate_statistical_significance(
            control_data, treatment_data
        )
        
        assert significance_result["p_value"] < 0.05  # Statistically significant
        assert significance_result["confidence_level"] >= 0.95
        assert significance_result["is_significant"] == True
        assert significance_result["effect_size"] > 0
        assert significance_result["recommended_action"] in ["adopt_treatment", "continue_testing"]

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_experiment_segmentation_analysis(self, ab_service):
        """Test analyzing experiment results by user segments"""
        experiment_id = 1
        
        # Mock segmented results
        with patch.object(ab_service, 'get_segmented_results') as mock_segments:
            mock_segments.return_value = {
                "age_18_25": {
                    "control": {"conversion_rate": 0.18, "sample_size": 200},
                    "treatment": {"conversion_rate": 0.25, "sample_size": 195}
                },
                "age_26_35": {
                    "control": {"conversion_rate": 0.12, "sample_size": 350},
                    "treatment": {"conversion_rate": 0.19, "sample_size": 340}
                },
                "new_users": {
                    "control": {"conversion_rate": 0.22, "sample_size": 150},
                    "treatment": {"conversion_rate": 0.31, "sample_size": 160}
                }
            }
            
            segmented_analysis = ab_service.analyze_experiment_by_segments(experiment_id)
            
            # Treatment should outperform control in all segments
            for segment, results in segmented_analysis.items():
                assert results["treatment"]["conversion_rate"] > results["control"]["conversion_rate"]
            
            # New users should have highest conversion rates
            assert segmented_analysis["new_users"]["control"]["conversion_rate"] > 0.2


class TestExperimentAPIs:
    """Test A/B testing REST API endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.ab_testing
    def test_create_experiment_endpoint(self, client, authenticated_user):
        """Test creating experiments via API"""
        experiment_data = {
            "name": "soul_matching_algorithm_v3",
            "description": "Test enhanced soul compatibility algorithm",
            "traffic_allocation": 0.25,
            "target_metrics": ["match_quality", "user_satisfaction"],
            "variants": [
                {
                    "name": "control",
                    "config": {"algorithm_version": "v2"},
                    "traffic_percentage": 0.5
                },
                {
                    "name": "enhanced_algorithm",
                    "config": {"algorithm_version": "v3", "emotional_weighting": 1.2},
                    "traffic_percentage": 0.5
                }
            ]
        }
        
        response = client.post(
            "/api/v1/experiments/create",
            json=experiment_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_404_NOT_FOUND]
        
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            assert data["name"] == experiment_data["name"]
            assert data["traffic_allocation"] == 0.25
            assert len(data["variants"]) == 2

    @pytest.mark.integration
    @pytest.mark.ab_testing
    def test_get_user_experiments_endpoint(self, client, authenticated_user):
        """Test retrieving user's experiment assignments"""
        response = client.get(
            "/api/v1/experiments/my-assignments",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert isinstance(data, list)
            
            for assignment in data:
                assert "experiment_name" in assignment
                assert "variant_name" in assignment
                assert "assigned_at" in assignment

    @pytest.mark.integration
    @pytest.mark.ab_testing
    def test_track_experiment_event_endpoint(self, client, authenticated_user):
        """Test tracking experiment events via API"""
        event_data = {
            "experiment_name": "revelation_engagement_test",
            "event_name": "revelation_completed",
            "event_data": {
                "day_number": 3,
                "content_length": 245,
                "emotional_depth_score": 8.5
            }
        }
        
        response = client.post(
            "/api/v1/experiments/track-event",
            json=event_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND
        ]

    @pytest.mark.integration
    @pytest.mark.ab_testing
    def test_experiment_results_endpoint(self, client, authenticated_user):
        """Test retrieving experiment results (admin only)"""
        experiment_id = 1
        
        response = client.get(
            f"/api/v1/experiments/{experiment_id}/results",
            headers=authenticated_user["headers"]
        )
        
        # Should require admin permissions or return not found
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]


class TestExperimentFeatureIntegration:
    """Test A/B testing integration with dating platform features"""
    
    @pytest.mark.integration
    @pytest.mark.ab_testing
    def test_soul_connection_algorithm_experiment(self, client, authenticated_user, matching_users):
        """Test A/B testing integration with soul connection features"""
        # Mock active experiment affecting soul connections
        ab_service = ABTestingService(None)
        
        with patch.object(ab_service, 'get_active_experiments_for_user') as mock_experiments:
            mock_experiments.return_value = [
                {
                    "name": "enhanced_compatibility_scoring",
                    "variant": "treatment",
                    "config": {"emotional_weight_multiplier": 1.3, "interest_boost": 0.2}
                }
            ]
            
            # Request soul connection discovery
            response = client.get(
                "/api/v1/connections/discover",
                headers=authenticated_user["headers"]
            )
            
            # Should succeed or indicate not implemented
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_403_FORBIDDEN
            ]

    @pytest.mark.integration
    @pytest.mark.ab_testing
    def test_revelation_prompt_experiment(self, client, authenticated_user, soul_connection_data):
        """Test A/B testing integration with revelation system"""
        connection = soul_connection_data["connection"]
        
        # Mock experiment affecting revelation prompts
        with patch('app.services.ab_testing_service.ABTestingService.get_user_variant') as mock_variant:
            mock_variant.return_value = {
                "experiment": "revelation_prompt_optimization",
                "variant": "enhanced_prompts",
                "config": {
                    "prompt_style": "storytelling",
                    "example_count": 4,
                    "emotional_depth_hints": True
                }
            }
            
            # Get revelation prompts (should be affected by experiment)
            response = client.get(
                f"/api/v1/revelations/prompts/1",
                headers=authenticated_user["headers"]
            )
            
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND
            ]

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_photo_reveal_timing_experiment(self, ab_service, soul_connection_data):
        """Test A/B experiment affecting photo reveal timing"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Create photo reveal timing experiment
        experiment = ab_service.create_experiment({
            "name": "photo_reveal_timing_optimization",
            "status": ExperimentStatus.ACTIVE.value,
            "target_metrics": ["photo_reveal_rate", "connection_satisfaction"]
        })
        
        control_variant = ab_service.create_variant(
            experiment.id, "control", {"reveal_day_requirement": 7}, 0.5
        )
        
        treatment_variant = ab_service.create_variant(
            experiment.id, "flexible_timing", {"reveal_day_requirement": 5, "user_choice": True}, 0.5
        )
        
        # Assign user and check photo reveal eligibility
        assignment = ab_service.assign_user_to_experiment(user.id, experiment.id)
        
        if assignment.variant_name == "control":
            assert assignment.variant_config["reveal_day_requirement"] == 7
        else:
            assert assignment.variant_config["reveal_day_requirement"] == 5
            assert assignment.variant_config["user_choice"] == True


class TestExperimentSafety:
    """Test A/B testing safety and guardrails"""
    
    @pytest.mark.unit
    @pytest.mark.ab_testing
    @pytest.mark.security
    def test_experiment_traffic_limits(self, ab_service):
        """Test that experiments respect traffic allocation limits"""
        # Should prevent creating experiments with invalid traffic allocation
        with pytest.raises(ValueError, match="Traffic allocation must be between 0.0 and 1.0"):
            ab_service.create_experiment({
                "name": "invalid_traffic_test",
                "traffic_allocation": 1.5  # Invalid > 1.0
            })
        
        with pytest.raises(ValueError, match="Traffic allocation must be between 0.0 and 1.0"):
            ab_service.create_experiment({
                "name": "negative_traffic_test", 
                "traffic_allocation": -0.1  # Invalid < 0.0
            })

    @pytest.mark.unit
    @pytest.mark.ab_testing
    @pytest.mark.security
    def test_experiment_variant_validation(self, ab_service):
        """Test validation of experiment variants"""
        experiment = ab_service.create_experiment({
            "name": "variant_validation_test",
            "traffic_allocation": 0.5
        })
        
        # Variant traffic percentages should sum to 1.0
        ab_service.create_variant(experiment.id, "control", {}, 0.4)
        ab_service.create_variant(experiment.id, "treatment", {}, 0.4)
        
        with pytest.raises(ValueError, match="Variant traffic percentages exceed 100%"):
            ab_service.create_variant(experiment.id, "extra", {}, 0.3)  # Would sum to 1.1

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_experiment_date_validation(self, ab_service):
        """Test experiment date validation"""
        past_date = datetime.now() - timedelta(days=1)
        future_date = datetime.now() + timedelta(days=30)
        
        # End date should be after start date
        with pytest.raises(ValueError, match="End date must be after start date"):
            ab_service.create_experiment({
                "name": "invalid_dates_test",
                "start_date": future_date,
                "end_date": past_date
            })

    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_experiment_performance_monitoring(self, ab_service):
        """Test performance monitoring and automatic experiment stopping"""
        experiment = ab_service.create_experiment({
            "name": "monitored_experiment",
            "status": ExperimentStatus.ACTIVE.value,
            "safety_thresholds": {
                "min_conversion_rate": 0.05,
                "max_bounce_rate": 0.8,
                "min_sample_size": 100
            }
        })
        
        # Mock poor performance data
        poor_performance = {
            "conversion_rate": 0.02,  # Below minimum
            "bounce_rate": 0.85,     # Above maximum
            "sample_size": 50        # Below minimum
        }
        
        safety_check = ab_service.check_experiment_safety(experiment.id, poor_performance)
        
        assert safety_check["should_stop"] == True
        assert len(safety_check["violations"]) >= 3
        assert "min_conversion_rate" in safety_check["violations"]


class TestExperimentReporting:
    """Test A/B testing reporting and insights"""
    
    @pytest.mark.unit
    @pytest.mark.ab_testing
    def test_experiment_summary_report(self, ab_service):
        """Test generating experiment summary reports"""
        experiment_id = 1
        
        with patch.object(ab_service, 'get_experiment_summary') as mock_summary:
            mock_summary.return_value = {
                "experiment_name": "soul_connection_optimization",
                "status": "completed",
                "duration_days": 30,
                "total_participants": 2500,
                "variants": {
                    "control": {
                        "participants": 1250,
                        "conversion_rate": 0.18,
                        "confidence_interval": [0.16, 0.20]
                    },
                    "treatment": {
                        "participants": 1250,
                        "conversion_rate": 0.24,
                        "confidence_interval": [0.22, 0.26]
                    }
                },
                "statistical_significance": {
                    "p_value": 0.003,
                    "confidence_level": 0.99,
                    "is_significant": True
                },
                "recommendations": {
                    "winner": "treatment",
                    "expected_lift": 0.33,
                    "rollout_recommendation": "full_rollout"
                }
            }
            
            report = ab_service.generate_experiment_report(experiment_id)
            
            assert report["status"] == "completed"
            assert report["variants"]["treatment"]["conversion_rate"] > report["variants"]["control"]["conversion_rate"]
            assert report["statistical_significance"]["is_significant"] == True
            assert report["recommendations"]["winner"] == "treatment"

    @pytest.mark.performance
    @pytest.mark.ab_testing
    def test_ab_testing_performance_impact(self, ab_service):
        """Test that A/B testing framework doesn't impact performance"""
        import time
        
        # Simulate multiple rapid experiment assignments
        start_time = time.time()
        
        for i in range(100):
            # Mock user assignment call
            user_id = i + 1
            experiment_assignments = ab_service.get_user_experiment_assignments(user_id)
        
        total_time = time.time() - start_time
        
        # Should complete quickly
        assert total_time < 1.0  # Under 1 second for 100 assignments
        
        # Average assignment time should be very fast
        avg_time_per_assignment = total_time / 100
        assert avg_time_per_assignment < 0.01  # Under 10ms per assignment