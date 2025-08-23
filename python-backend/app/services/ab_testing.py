# A/B Testing Framework for Dinner First
# Feature optimization and experimentation platform

# import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import redis
from clickhouse_driver import Client
from scipy import stats

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class VariantType(Enum):
    CONTROL = "control"
    TREATMENT = "treatment"


class MetricType(Enum):
    CONVERSION = "conversion"  # Binary outcome (0 or 1)
    CONTINUOUS = "continuous"  # Numerical value
    COUNT = "count"  # Count of events
    DURATION = "duration"  # Time-based metrics


@dataclass
class ExperimentVariant:
    variant_id: str
    name: str
    variant_type: VariantType
    traffic_allocation: float  # 0.0 to 1.0
    configuration: Dict[str, Any]
    description: Optional[str] = None


@dataclass
class Experiment:
    experiment_id: str
    name: str
    description: str
    hypothesis: str
    primary_metric: str
    secondary_metrics: List[str]
    variants: List[ExperimentVariant]
    target_audience: Dict[str, Any]
    status: ExperimentStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    minimum_sample_size: int
    confidence_level: float  # 0.95 for 95% confidence
    minimum_effect_size: float
    created_by: int
    created_at: datetime
    updated_at: datetime


@dataclass
class UserAssignment:
    assignment_id: str
    user_id: int
    experiment_id: str
    variant_id: str
    assigned_at: datetime
    is_active: bool = True


@dataclass
class ExperimentEvent:
    event_id: str
    user_id: int
    experiment_id: str
    variant_id: str
    event_type: str
    metric_name: str
    metric_value: float
    timestamp: datetime
    properties: Dict[str, Any]


class ABTestingService:
    """
    Comprehensive A/B testing framework for dating platform optimization
    """

    def __init__(self, clickhouse_client: Client, redis_client: redis.Redis):
        self.clickhouse = clickhouse_client
        self.redis = redis_client

        # Predefined experiments for dating platform
        self.platform_experiments = {
            "matching_algorithm_v2": {
                "name": "Enhanced Matching Algorithm",
                "description": "Test improved compatibility scoring algorithm",
                "primary_metric": "match_rate",
            },
            "revelation_timeline": {
                "name": "Revelation Timeline Optimization",
                "description": "Test different revelation schedules",
                "primary_metric": "photo_reveal_rate",
            },
            "onboarding_flow": {
                "name": "Streamlined Onboarding",
                "description": "Test simplified onboarding process",
                "primary_metric": "onboarding_completion_rate",
            },
            "message_prompts": {
                "name": "Conversation Starter Prompts",
                "description": "Test AI-generated conversation starters",
                "primary_metric": "first_message_rate",
            },
        }

    async def create_experiment(self, experiment_data: Dict[str, Any]) -> str:
        """
        Create a new A/B test experiment
        """
        try:
            experiment_id = str(uuid.uuid4())

            # Validate experiment configuration
            self._validate_experiment(experiment_data)

            # Create experiment object
            experiment = Experiment(
                experiment_id=experiment_id,
                name=experiment_data["name"],
                description=experiment_data["description"],
                hypothesis=experiment_data["hypothesis"],
                primary_metric=experiment_data["primary_metric"],
                secondary_metrics=experiment_data.get("secondary_metrics", []),
                variants=[
                    ExperimentVariant(**variant)
                    for variant in experiment_data["variants"]
                ],
                target_audience=experiment_data.get("target_audience", {}),
                status=ExperimentStatus.DRAFT,
                start_date=None,
                end_date=None,
                minimum_sample_size=experiment_data.get("minimum_sample_size", 1000),
                confidence_level=experiment_data.get("confidence_level", 0.95),
                minimum_effect_size=experiment_data.get("minimum_effect_size", 0.05),
                created_by=experiment_data["created_by"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Store experiment in database
            await self._store_experiment(experiment)

            # Cache experiment configuration
            await self._cache_experiment_config(experiment)

            logger.info(f"Created experiment {experiment_id}: {experiment.name}")
            return experiment_id

        except Exception as e:
            logger.error(f"Failed to create experiment: {e}")
            raise

    async def start_experiment(self, experiment_id: str) -> bool:
        """
        Start an A/B test experiment
        """
        try:
            experiment = await self._get_experiment(experiment_id)

            if experiment.status != ExperimentStatus.DRAFT:
                raise ValueError(
                    f"Cannot start experiment in {experiment.status} status"
                )

            # Validate experiment is ready to start
            await self._validate_experiment_ready(experiment)

            # Update experiment status
            experiment.status = ExperimentStatus.ACTIVE
            experiment.start_date = datetime.utcnow()
            experiment.updated_at = datetime.utcnow()

            # Update in database
            await self._update_experiment(experiment)

            # Initialize real-time tracking
            await self._initialize_experiment_tracking(experiment)

            logger.info(f"Started experiment {experiment_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start experiment {experiment_id}: {e}")
            return False

    async def assign_user_to_experiment(
        self, user_id: int, experiment_id: str
    ) -> Optional[str]:
        """
        Assign a user to an experiment variant
        """
        try:
            # Check if user is already assigned
            existing_assignment = await self._get_user_assignment(
                user_id, experiment_id
            )
            if existing_assignment:
                return existing_assignment.variant_id

            experiment = await self._get_experiment(experiment_id)

            if experiment.status != ExperimentStatus.ACTIVE:
                return None

            # Check if user meets target audience criteria
            if not await self._user_meets_criteria(user_id, experiment.target_audience):
                return None

            # Assign to variant based on traffic allocation
            variant_id = self._determine_variant(user_id, experiment)

            # Create assignment record
            assignment = UserAssignment(
                assignment_id=str(uuid.uuid4()),
                user_id=user_id,
                experiment_id=experiment_id,
                variant_id=variant_id,
                assigned_at=datetime.utcnow(),
            )

            # Store assignment
            await self._store_user_assignment(assignment)

            # Track assignment event
            await self._track_assignment_event(assignment)

            return variant_id

        except Exception as e:
            logger.error(
                f"Failed to assign user {user_id} to experiment {experiment_id}: {e}"
            )
            return None

    async def track_experiment_event(
        self,
        user_id: int,
        experiment_id: str,
        event_type: str,
        metric_name: str,
        metric_value: float,
        properties: Dict[str, Any] = None,
    ) -> bool:
        """
        Track an event for A/B test analysis
        """
        try:
            # Get user's variant assignment
            assignment = await self._get_user_assignment(user_id, experiment_id)
            if not assignment or not assignment.is_active:
                return False

            # Create event record
            event = ExperimentEvent(
                event_id=str(uuid.uuid4()),
                user_id=user_id,
                experiment_id=experiment_id,
                variant_id=assignment.variant_id,
                event_type=event_type,
                metric_name=metric_name,
                metric_value=metric_value,
                timestamp=datetime.utcnow(),
                properties=properties or {},
            )

            # Store event
            await self._store_experiment_event(event)

            # Update real-time metrics
            await self._update_real_time_metrics(event)

            return True

        except Exception as e:
            logger.error(f"Failed to track experiment event: {e}")
            return False

    async def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get statistical analysis results for an experiment
        """
        try:
            experiment = await self._get_experiment(experiment_id)

            # Get raw data for analysis
            variant_data = await self._get_variant_data(experiment_id)

            # Perform statistical analysis
            results = await self._analyze_experiment_results(experiment, variant_data)

            return results

        except Exception as e:
            logger.error(f"Failed to get experiment results for {experiment_id}: {e}")
            return {}

    async def track_conversion_event(
        self,
        user_id: int,
        experiment_id: str,
        metric_name: str,
        conversion_value: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Track a conversion event for A/B testing analysis

        Args:
            user_id: ID of the user who converted
            experiment_id: ID of the experiment
            metric_name: Name of the metric being tracked
            conversion_value: Value of the conversion (default 1.0 for binary)
            properties: Additional event properties

        Returns:
            bool: True if event was tracked successfully
        """
        try:
            # Get user's variant assignment
            assignment_key = f"user_assignment:{user_id}:{experiment_id}"
            assignment_data = self.redis.get(assignment_key)

            if not assignment_data:
                logger.warning(
                    f"No assignment found for user {user_id} in experiment {experiment_id}"
                )
                return False

            assignment = json.loads(assignment_data)
            variant_id = assignment["variant_id"]

            # Create conversion event
            event = ExperimentEvent(
                event_id=str(uuid.uuid4()),
                user_id=user_id,
                experiment_id=experiment_id,
                variant_id=variant_id,
                event_type="conversion",
                metric_name=metric_name,
                metric_value=conversion_value,
                properties=properties or {},
                timestamp=datetime.utcnow(),
            )

            # Store event
            await self._store_experiment_event(event)

            # Update real-time metrics
            await self._update_real_time_metrics(event)

            logger.info(
                f"Tracked conversion event: {metric_name}={conversion_value} for user {user_id}, experiment {experiment_id}, variant {variant_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to track conversion event: {e}")
            return False

    async def calculate_statistical_significance(
        self, experiment_id: str, metric_name: str, confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Calculate statistical significance for an experiment's primary metric

        Args:
            experiment_id: ID of the experiment
            metric_name: Name of the metric to analyze
            confidence_level: Confidence level for statistical test (default 0.95)

        Returns:
            Dict containing statistical analysis results
        """
        try:
            experiment = await self._get_experiment(experiment_id)
            variant_data = await self._get_variant_data(experiment_id)

            if not variant_data:
                return {
                    "statistically_significant": False,
                    "reason": "Insufficient data",
                    "p_value": 1.0,
                    "confidence_level": confidence_level,
                }

            # Get control variant data
            control_variant = next(
                v for v in experiment.variants if v.variant_type == VariantType.CONTROL
            )
            control_data = variant_data.get(control_variant.variant_id, {})
            control_conversions = control_data.get(f"{metric_name}_conversions", 0)
            control_exposures = control_data.get("exposures", 0)

            if control_exposures == 0:
                return {
                    "statistically_significant": False,
                    "reason": "No control group data",
                    "p_value": 1.0,
                    "confidence_level": confidence_level,
                }

            results = {
                "experiment_id": experiment_id,
                "metric_name": metric_name,
                "confidence_level": confidence_level,
                "control_variant": {
                    "variant_id": control_variant.variant_id,
                    "conversions": control_conversions,
                    "exposures": control_exposures,
                    "conversion_rate": (
                        control_conversions / control_exposures
                        if control_exposures > 0
                        else 0
                    ),
                },
                "treatment_results": [],
                "overall_significance": False,
            }

            # Test each treatment variant against control
            for variant in experiment.variants:
                if variant.variant_type == VariantType.TREATMENT:
                    treatment_data = variant_data.get(variant.variant_id, {})
                    treatment_conversions = treatment_data.get(
                        f"{metric_name}_conversions", 0
                    )
                    treatment_exposures = treatment_data.get("exposures", 0)

                    if treatment_exposures > 0:
                        # Perform statistical test
                        z_stat, p_value = self._two_proportion_z_test(
                            treatment_conversions,
                            treatment_exposures,
                            control_conversions,
                            control_exposures,
                        )

                        # Calculate confidence interval and lift
                        treatment_rate = treatment_conversions / treatment_exposures
                        control_rate = control_conversions / control_exposures
                        lift = (
                            ((treatment_rate - control_rate) / control_rate)
                            if control_rate > 0
                            else 0
                        )

                        ci_lower, ci_upper = self._confidence_interval(
                            treatment_conversions, treatment_exposures, confidence_level
                        )

                        is_significant = p_value < (1 - confidence_level)

                        treatment_result = {
                            "variant_id": variant.variant_id,
                            "variant_name": variant.name,
                            "conversions": treatment_conversions,
                            "exposures": treatment_exposures,
                            "conversion_rate": treatment_rate,
                            "lift": lift,
                            "p_value": p_value,
                            "z_statistic": z_stat,
                            "statistically_significant": is_significant,
                            "confidence_interval": [ci_lower, ci_upper],
                            "sample_size_adequate": treatment_exposures
                            >= experiment.minimum_sample_size,
                        }

                        results["treatment_results"].append(treatment_result)

                        if is_significant:
                            results["overall_significance"] = True

            return results

        except Exception as e:
            logger.error(f"Failed to calculate statistical significance: {e}")
            return {
                "statistically_significant": False,
                "reason": f"Analysis error: {str(e)}",
                "p_value": 1.0,
                "confidence_level": confidence_level,
            }

    async def analyze_experiment_performance(
        self, experiment_id: str, include_secondary_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive performance analysis of an experiment

        Args:
            experiment_id: ID of the experiment to analyze
            include_secondary_metrics: Whether to include secondary metrics analysis

        Returns:
            Dict containing comprehensive experiment performance analysis
        """
        try:
            experiment = await self._get_experiment(experiment_id)
            variant_data = await self._get_variant_data(experiment_id)

            # Get overall experiment health
            total_users = sum(
                data.get("exposures", 0) for data in variant_data.values()
            )

            # Calculate experiment duration
            experiment_duration = None
            if experiment.start_date:
                end_date = experiment.end_date or datetime.utcnow()
                experiment_duration = (end_date - experiment.start_date).days

            # Primary metric analysis
            primary_analysis = await self.calculate_statistical_significance(
                experiment_id, experiment.primary_metric
            )

            analysis_results = {
                "experiment_id": experiment_id,
                "experiment_name": experiment.name,
                "status": experiment.status.value,
                "analysis_timestamp": datetime.utcnow(),
                "experiment_health": {
                    "total_participants": total_users,
                    "duration_days": experiment_duration,
                    "minimum_sample_size_met": total_users
                    >= experiment.minimum_sample_size,
                    "traffic_allocation_balanced": self._check_traffic_balance(
                        variant_data, experiment
                    ),
                },
                "primary_metric_analysis": primary_analysis,
                "secondary_metrics_analysis": [],
                "variant_performance": [],
                "recommendations": [],
            }

            # Analyze secondary metrics if requested
            if include_secondary_metrics and experiment.secondary_metrics:
                for metric in experiment.secondary_metrics:
                    secondary_analysis = await self.calculate_statistical_significance(
                        experiment_id, metric
                    )
                    analysis_results["secondary_metrics_analysis"].append(
                        {"metric_name": metric, "analysis": secondary_analysis}
                    )

            # Detailed variant performance
            for variant in experiment.variants:
                variant_stats = variant_data.get(variant.variant_id, {})
                exposures = variant_stats.get("exposures", 0)

                # Calculate conversion rates for all metrics
                metrics = {}
                all_metrics = [experiment.primary_metric] + (
                    experiment.secondary_metrics or []
                )

                for metric in all_metrics:
                    conversions = variant_stats.get(f"{metric}_conversions", 0)
                    metrics[metric] = {
                        "conversions": conversions,
                        "conversion_rate": (
                            conversions / exposures if exposures > 0 else 0
                        ),
                    }

                variant_performance = {
                    "variant_id": variant.variant_id,
                    "variant_name": variant.name,
                    "variant_type": variant.variant_type.value,
                    "exposures": exposures,
                    "traffic_allocation": variant.traffic_allocation,
                    "actual_traffic_percentage": (
                        (exposures / total_users) if total_users > 0 else 0
                    ),
                    "metrics": metrics,
                    "sample_size_adequate": exposures >= experiment.minimum_sample_size,
                }

                analysis_results["variant_performance"].append(variant_performance)

            # Generate actionable recommendations
            analysis_results["recommendations"] = (
                self._generate_experiment_recommendations(analysis_results, experiment)
            )

            return analysis_results

        except Exception as e:
            logger.error(f"Failed to analyze experiment performance: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "experiment_id": experiment_id,
                "analysis_timestamp": datetime.utcnow(),
            }

    def _check_traffic_balance(
        self, variant_data: Dict[str, Any], experiment: Experiment
    ) -> bool:
        """Check if traffic allocation is reasonably balanced"""
        total_exposures = sum(
            data.get("exposures", 0) for data in variant_data.values()
        )

        if total_exposures == 0:
            return False

        for variant in experiment.variants:
            actual_percentage = (
                variant_data.get(variant.variant_id, {}).get("exposures", 0)
                / total_exposures
            )
            expected_percentage = variant.traffic_allocation

            # Allow 10% deviation from expected allocation
            if abs(actual_percentage - expected_percentage) > 0.1:
                return False

        return True

    def _generate_experiment_recommendations(
        self, analysis_results: Dict[str, Any], experiment: Experiment
    ) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        health = analysis_results["experiment_health"]
        primary_analysis = analysis_results["primary_metric_analysis"]

        # Sample size recommendations
        if not health["minimum_sample_size_met"]:
            recommendations.append(
                f"Continue experiment - need {experiment.minimum_sample_size - health['total_participants']} more participants"
            )

        # Traffic balance recommendations
        if not health["traffic_allocation_balanced"]:
            recommendations.append(
                "Review traffic allocation - significant imbalance detected between variants"
            )

        # Statistical significance recommendations
        if primary_analysis.get("overall_significance"):
            # Find best performing variant
            best_variant = None
            best_lift = 0

            for result in primary_analysis.get("treatment_results", []):
                if result["statistically_significant"] and result["lift"] > best_lift:
                    best_lift = result["lift"]
                    best_variant = result["variant_name"]

            if best_variant and best_lift >= experiment.minimum_effect_size:
                recommendations.append(
                    f"Implement '{best_variant}' - shows {best_lift:.1%} improvement with statistical significance"
                )
            elif best_variant:
                recommendations.append(
                    f"Consider implementing '{best_variant}' - statistically significant but below minimum effect size threshold"
                )
        else:
            if health["minimum_sample_size_met"]:
                recommendations.append(
                    "No statistically significant difference detected - consider ending experiment or extending duration"
                )

        # Duration recommendations
        if health["duration_days"] and health["duration_days"] > 30:
            recommendations.append(
                "Experiment has been running for over 30 days - consider concluding to avoid seasonal effects"
            )

        return recommendations

    async def _validate_experiment(self, experiment_data: Dict[str, Any]):
        """Validate experiment configuration"""
        required_fields = [
            "name",
            "description",
            "hypothesis",
            "primary_metric",
            "variants",
        ]

        for field in required_fields:
            if field not in experiment_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate variants
        variants = experiment_data["variants"]
        if len(variants) < 2:
            raise ValueError("Experiment must have at least 2 variants")

        total_allocation = sum(v.get("traffic_allocation", 0) for v in variants)
        if abs(total_allocation - 1.0) > 0.01:
            raise ValueError("Traffic allocation must sum to 1.0")

        # Ensure one control variant
        control_count = sum(1 for v in variants if v.get("variant_type") == "control")
        if control_count != 1:
            raise ValueError("Experiment must have exactly one control variant")

    async def _store_experiment(self, experiment: Experiment):
        """Store experiment in ClickHouse"""
        try:
            experiment_data = {
                "experiment_id": experiment.experiment_id,
                "name": experiment.name,
                "description": experiment.description,
                "hypothesis": experiment.hypothesis,
                "primary_metric": experiment.primary_metric,
                "secondary_metrics": experiment.secondary_metrics,
                "variants": [asdict(v) for v in experiment.variants],
                "target_audience": experiment.target_audience,
                "status": experiment.status.value,
                "minimum_sample_size": experiment.minimum_sample_size,
                "confidence_level": experiment.confidence_level,
                "minimum_effect_size": experiment.minimum_effect_size,
                "created_by": experiment.created_by,
                "created_at": experiment.created_at,
                "updated_at": experiment.updated_at,
            }

            # Store in experiments table (this would need to be created)
            # For now, store in Redis as JSON
            self.redis.hset(
                "experiments",
                experiment.experiment_id,
                json.dumps(experiment_data, default=str),
            )

        except Exception as e:
            logger.error(f"Failed to store experiment: {e}")
            raise

    async def _get_experiment(self, experiment_id: str) -> Experiment:
        """Retrieve experiment from storage"""
        try:
            experiment_json = self.redis.hget("experiments", experiment_id)
            if not experiment_json:
                raise ValueError(f"Experiment {experiment_id} not found")

            experiment_data = json.loads(experiment_json)

            # Convert back to Experiment object
            experiment = Experiment(
                experiment_id=experiment_data["experiment_id"],
                name=experiment_data["name"],
                description=experiment_data["description"],
                hypothesis=experiment_data["hypothesis"],
                primary_metric=experiment_data["primary_metric"],
                secondary_metrics=experiment_data["secondary_metrics"],
                variants=[
                    ExperimentVariant(
                        variant_id=v["variant_id"],
                        name=v["name"],
                        variant_type=VariantType(v["variant_type"]),
                        traffic_allocation=v["traffic_allocation"],
                        configuration=v["configuration"],
                        description=v.get("description"),
                    )
                    for v in experiment_data["variants"]
                ],
                target_audience=experiment_data["target_audience"],
                status=ExperimentStatus(experiment_data["status"]),
                start_date=(
                    datetime.fromisoformat(experiment_data["start_date"])
                    if experiment_data.get("start_date")
                    else None
                ),
                end_date=(
                    datetime.fromisoformat(experiment_data["end_date"])
                    if experiment_data.get("end_date")
                    else None
                ),
                minimum_sample_size=experiment_data["minimum_sample_size"],
                confidence_level=experiment_data["confidence_level"],
                minimum_effect_size=experiment_data["minimum_effect_size"],
                created_by=experiment_data["created_by"],
                created_at=datetime.fromisoformat(experiment_data["created_at"]),
                updated_at=datetime.fromisoformat(experiment_data["updated_at"]),
            )

            return experiment

        except Exception as e:
            logger.error(f"Failed to get experiment {experiment_id}: {e}")
            raise

    def _determine_variant(self, user_id: int, experiment: Experiment) -> str:
        """Determine which variant a user should be assigned to"""
        # Use user ID as seed for consistent assignment
        import hashlib

        seed = int(
            hashlib.md5(f"{user_id}_{experiment.experiment_id}".encode()).hexdigest()[
                :8
            ],
            16,
        )
        random_value = (seed % 10000) / 10000.0  # 0.0 to 1.0

        cumulative_allocation = 0.0
        for variant in experiment.variants:
            cumulative_allocation += variant.traffic_allocation
            if random_value <= cumulative_allocation:
                return variant.variant_id

        # Fallback to control variant
        control_variant = next(
            v for v in experiment.variants if v.variant_type == VariantType.CONTROL
        )
        return control_variant.variant_id

    async def _get_user_assignment(
        self, user_id: int, experiment_id: str
    ) -> Optional[UserAssignment]:
        """Get user's current assignment for an experiment"""
        try:
            assignment_key = f"assignment:{experiment_id}:{user_id}"
            assignment_json = self.redis.get(assignment_key)

            if assignment_json:
                assignment_data = json.loads(assignment_json)
                return UserAssignment(**assignment_data)

            return None

        except Exception as e:
            logger.error(f"Failed to get user assignment: {e}")
            return None

    async def _store_user_assignment(self, assignment: UserAssignment):
        """Store user assignment"""
        try:
            assignment_key = (
                f"assignment:{assignment.experiment_id}:{assignment.user_id}"
            )
            assignment_data = asdict(assignment)

            self.redis.set(
                assignment_key,
                json.dumps(assignment_data, default=str),
                ex=86400 * 90,  # 90 days expiry
            )

            # Also store in ClickHouse for analysis
            assignment_record = {
                "assignment_id": assignment.assignment_id,
                "user_id": assignment.user_id,
                "experiment_id": assignment.experiment_id,
                "variant": assignment.variant_id,
                "assignment_date": assignment.assigned_at.date(),
                "is_active": assignment.is_active,
                "timestamp": assignment.assigned_at,
            }

            self.clickhouse.execute(
                "INSERT INTO experiment_assignments VALUES", [assignment_record]
            )

        except Exception as e:
            logger.error(f"Failed to store user assignment: {e}")
            raise

    async def _store_experiment_event(self, event: ExperimentEvent):
        """Store experiment event in ClickHouse"""
        try:
            event_data = {
                "event_id": event.event_id,
                "user_id": event.user_id,
                "experiment_id": event.experiment_id,
                "variant": event.variant_id,
                "event_type": event.event_type,
                "metric_name": event.metric_name,
                "metric_value": event.metric_value,
                "properties": event.properties,
                "timestamp": event.timestamp,
                "date": event.timestamp.date(),
            }

            self.clickhouse.execute(
                "INSERT INTO experiment_events VALUES", [event_data]
            )

        except Exception as e:
            logger.error(f"Failed to store experiment event: {e}")
            raise

    async def _analyze_experiment_results(
        self, experiment: Experiment, variant_data: Dict
    ) -> Dict[str, Any]:
        """Perform statistical analysis on experiment results"""
        try:
            results = {
                "experiment_id": experiment.experiment_id,
                "experiment_name": experiment.name,
                "status": experiment.status.value,
                "analysis_timestamp": datetime.utcnow(),
                "variants": [],
                "statistical_significance": False,
                "confidence_level": experiment.confidence_level,
                "recommendation": "Continue experiment",
            }

            # Get control variant data
            control_variant = next(
                v for v in experiment.variants if v.variant_type == VariantType.CONTROL
            )
            control_data = variant_data.get(control_variant.variant_id, {})

            for variant in experiment.variants:
                variant_stats = variant_data.get(variant.variant_id, {})

                # Calculate conversion rate for primary metric
                conversions = variant_stats.get(
                    f"{experiment.primary_metric}_conversions", 0
                )
                exposures = variant_stats.get("exposures", 0)
                conversion_rate = conversions / exposures if exposures > 0 else 0

                variant_result = {
                    "variant_id": variant.variant_id,
                    "variant_name": variant.name,
                    "variant_type": variant.variant_type.value,
                    "exposures": exposures,
                    "conversions": conversions,
                    "conversion_rate": conversion_rate,
                    "confidence_interval": None,
                    "statistical_significance": False,
                    "lift": 0.0,
                }

                # Statistical test against control (if this is a treatment variant)
                if variant.variant_type == VariantType.TREATMENT and control_data:
                    control_conversions = control_data.get(
                        f"{experiment.primary_metric}_conversions", 0
                    )
                    control_exposures = control_data.get("exposures", 0)

                    if control_exposures > 0 and exposures > 0:
                        # Perform two-proportion z-test
                        z_stat, p_value = self._two_proportion_z_test(
                            conversions,
                            exposures,
                            control_conversions,
                            control_exposures,
                        )

                        # Calculate confidence interval
                        ci_lower, ci_upper = self._confidence_interval(
                            conversions, exposures, experiment.confidence_level
                        )

                        # Calculate lift
                        control_rate = control_conversions / control_exposures
                        lift = (
                            (conversion_rate - control_rate) / control_rate
                            if control_rate > 0
                            else 0
                        )

                        variant_result.update(
                            {
                                "confidence_interval": [ci_lower, ci_upper],
                                "statistical_significance": p_value
                                < (1 - experiment.confidence_level),
                                "lift": lift,
                                "p_value": p_value,
                                "z_statistic": z_stat,
                            }
                        )

                        if variant_result["statistical_significance"]:
                            results["statistical_significance"] = True

                results["variants"].append(variant_result)

            # Generate recommendation
            results["recommendation"] = self._generate_recommendation(
                results, experiment
            )

            return results

        except Exception as e:
            logger.error(f"Failed to analyze experiment results: {e}")
            return {}

    def _two_proportion_z_test(
        self, x1: int, n1: int, x2: int, n2: int
    ) -> Tuple[float, float]:
        """Perform two-proportion z-test"""
        try:
            p1 = x1 / n1
            p2 = x2 / n2

            # Pooled proportion
            p_pool = (x1 + x2) / (n1 + n2)

            # Standard error
            se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))

            # Z-statistic
            z = (p1 - p2) / se if se > 0 else 0

            # Two-tailed p-value
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))

            return z, p_value

        except (ZeroDivisionError, ValueError):
            return 0.0, 1.0

    def _confidence_interval(
        self, conversions: int, exposures: int, confidence_level: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval for conversion rate"""
        try:
            if exposures == 0:
                return 0.0, 0.0

            p = conversions / exposures
            z_score = stats.norm.ppf(1 - (1 - confidence_level) / 2)

            se = np.sqrt(p * (1 - p) / exposures)
            margin_of_error = z_score * se

            ci_lower = max(0, p - margin_of_error)
            ci_upper = min(1, p + margin_of_error)

            return ci_lower, ci_upper

        except (ZeroDivisionError, ValueError):
            return 0.0, 0.0

    def _generate_recommendation(self, results: Dict, experiment: Experiment) -> str:
        """Generate recommendation based on results"""
        if not results["statistical_significance"]:
            sample_sizes = [v["exposures"] for v in results["variants"]]
            min_sample_size = min(sample_sizes) if sample_sizes else 0

            if min_sample_size < experiment.minimum_sample_size:
                return "Continue experiment - insufficient sample size"
            else:
                return "No statistically significant difference detected"

        # Find best performing treatment variant
        treatment_variants = [
            v for v in results["variants"] if v["variant_type"] == "treatment"
        ]

        if treatment_variants:
            best_variant = max(treatment_variants, key=lambda x: x["conversion_rate"])

            if best_variant["lift"] > experiment.minimum_effect_size:
                return f"Implement {best_variant['variant_name']} - significant improvement detected"
            else:
                return (
                    "Effect size below minimum threshold - consider ending experiment"
                )

        return "Continue monitoring"

    async def _get_variant_data(self, experiment_id: str) -> Dict[str, Any]:
        """Get aggregated data for each variant"""
        try:
            # This would query ClickHouse for experiment data
            # For now, return mock data structure
            query = """
            SELECT
                variant,
                count(DISTINCT user_id) as exposures,
                countIf(metric_name = %(primary_metric)s AND metric_value > 0) as conversions
            FROM experiment_events
            WHERE experiment_id = %(experiment_id)s
            GROUP BY variant
            """

            # Placeholder for actual ClickHouse query
            return {}

        except Exception as e:
            logger.error(f"Failed to get variant data: {e}")
            return {}

    async def _user_meets_criteria(
        self, user_id: int, target_audience: Dict[str, Any]
    ) -> bool:
        """Check if user meets experiment targeting criteria"""
        # Implement targeting logic based on user attributes
        # For now, return True (no targeting)
        return True

    async def _cache_experiment_config(self, experiment: Experiment):
        """Cache experiment configuration for fast lookup"""
        config_key = f"experiment_config:{experiment.experiment_id}"
        config = {
            "status": experiment.status.value,
            "variants": [asdict(v) for v in experiment.variants],
        }

        self.redis.set(config_key, json.dumps(config, default=str), ex=3600)

    async def _initialize_experiment_tracking(self, experiment: Experiment):
        """Initialize real-time tracking for experiment"""
        # Set up real-time counters in Redis
        for variant in experiment.variants:
            self.redis.hset(
                f"experiment_metrics:{experiment.experiment_id}",
                f"{variant.variant_id}_exposures",
                0,
            )
            self.redis.hset(
                f"experiment_metrics:{experiment.experiment_id}",
                f"{variant.variant_id}_conversions",
                0,
            )

    async def _update_real_time_metrics(self, event: ExperimentEvent):
        """Update real-time experiment metrics"""
        metrics_key = f"experiment_metrics:{event.experiment_id}"

        # Increment conversion counter if this is a conversion event
        if event.metric_value > 0:
            self.redis.hincrby(metrics_key, f"{event.variant_id}_conversions", 1)

    async def _track_assignment_event(self, assignment: UserAssignment):
        """Track user assignment as an event"""
        self.redis.hincrby(
            f"experiment_metrics:{assignment.experiment_id}",
            f"{assignment.variant_id}_exposures",
            1,
        )

    async def _validate_experiment_ready(self, experiment: Experiment):
        """Validate experiment is ready to start"""
        # Check that all required configurations are in place
        # For now, just check basic requirements
        if not experiment.variants:
            raise ValueError("Experiment has no variants")

        if not experiment.primary_metric:
            raise ValueError("Experiment has no primary metric defined")

    async def _update_experiment(self, experiment: Experiment):
        """Update experiment in storage"""
        await self._store_experiment(experiment)
        await self._cache_experiment_config(experiment)
