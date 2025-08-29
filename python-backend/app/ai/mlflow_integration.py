"""
MLflow Integration Module for Dinner First AI Infrastructure

Provides comprehensive experiment tracking, model versioning, and lifecycle management
integration with MLflow for the dating platform's AI/ML systems.

Features:
- Experiment and run management
- Model registry integration
- A/B testing framework
- Performance tracking
- Automated model deployment
- Artifact management
"""

import json
import logging
import pickle
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import mlflow
import mlflow.pytorch
import mlflow.sklearn
import mlflow.tensorflow
import numpy as np
import pandas as pd
from app.core.config import settings
from app.core.event_publisher import event_publisher
from app.core.redis_cluster import redis_cluster_manager
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient
from pydantic import BaseModel, Field
from sklearn.base import BaseEstimator

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"


class RunStatus(str, Enum):
    RUNNING = "RUNNING"
    SCHEDULED = "SCHEDULED"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    KILLED = "KILLED"


class ModelStage(str, Enum):
    NONE = "None"
    STAGING = "Staging"
    PRODUCTION = "Production"
    ARCHIVED = "Archived"


class ExperimentConfig(BaseModel):
    experiment_name: str
    description: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    artifact_location: Optional[str] = None


class RunConfig(BaseModel):
    run_name: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    nested: bool = False


class ModelMetrics(BaseModel):
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None
    mse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    custom_metrics: Dict[str, float] = Field(default_factory=dict)


class ABTestConfig(BaseModel):
    test_name: str
    model_a_version: str
    model_b_version: str
    traffic_split: float = 0.5
    success_metric: str
    duration_days: int = 14
    minimum_sample_size: int = 1000
    statistical_significance_threshold: float = 0.05


class MLflowExperimentManager:
    """Manages MLflow experiments and runs for AI model development"""

    def __init__(self):
        self.client = MlflowClient()
        self.redis_client = redis_cluster_manager

        # Configure MLflow
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)

    async def create_experiment(self, config: ExperimentConfig) -> str:
        """Create a new MLflow experiment"""
        try:
            experiment_id = mlflow.create_experiment(
                name=config.experiment_name,
                artifact_location=config.artifact_location,
                tags=config.tags,
            )

            # Cache experiment metadata
            await self._cache_experiment_metadata(experiment_id, config)

            logger.info(
                f"Created MLflow experiment: {
                    config.experiment_name} (ID: {experiment_id})"
            )
            return experiment_id

        except MlflowException as e:
            if "already exists" in str(e):
                experiment = mlflow.get_experiment_by_name(config.experiment_name)
                return experiment.experiment_id
            raise

    async def start_run(self, experiment_id: str, config: RunConfig) -> str:
        """Start a new MLflow run"""
        run = mlflow.start_run(
            experiment_id=experiment_id,
            run_name=config.run_name,
            nested=config.nested,
            tags=config.tags,
        )

        # Cache run metadata
        await self._cache_run_metadata(run.info.run_id, experiment_id, config)

        logger.info(f"Started MLflow run: {run.info.run_id}")
        return run.info.run_id

    async def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics to the current MLflow run"""
        for metric_name, value in metrics.items():
            mlflow.log_metric(metric_name, value, step=step)

    async def log_params(self, params: Dict[str, Any]):
        """Log parameters to the current MLflow run"""
        mlflow.log_params(params)

    async def log_artifacts(self, local_path: str, artifact_path: Optional[str] = None):
        """Log artifacts to the current MLflow run"""
        mlflow.log_artifacts(local_path, artifact_path)

    async def log_model(
        self, model: Any, artifact_path: str, model_type: str = "sklearn", **kwargs
    ):
        """Log a model to the current MLflow run"""
        if model_type == "sklearn":
            mlflow.sklearn.log_model(model, artifact_path, **kwargs)
        elif model_type == "pytorch":
            mlflow.pytorch.log_model(model, artifact_path, **kwargs)
        elif model_type == "tensorflow":
            mlflow.tensorflow.log_model(model, artifact_path, **kwargs)
        else:
            mlflow.log_artifact(model, artifact_path)

    async def end_run(self, status: RunStatus = RunStatus.FINISHED):
        """End the current MLflow run"""
        mlflow.end_run(status=status.value)

    async def _cache_experiment_metadata(
        self, experiment_id: str, config: ExperimentConfig
    ):
        """Cache experiment metadata in Redis"""
        metadata = {
            "experiment_id": experiment_id,
            "name": config.experiment_name,
            "description": config.description,
            "tags": config.tags,
            "created_at": datetime.utcnow().isoformat(),
        }

        await self.redis_client.set(
            f"mlflow:experiment:{experiment_id}",
            json.dumps(metadata),
            ex=86400,  # 24 hours
        )

    async def _cache_run_metadata(
        self, run_id: str, experiment_id: str, config: RunConfig
    ):
        """Cache run metadata in Redis"""
        metadata = {
            "run_id": run_id,
            "experiment_id": experiment_id,
            "run_name": config.run_name,
            "tags": config.tags,
            "created_at": datetime.utcnow().isoformat(),
        }

        await self.redis_client.set(
            f"mlflow:run:{run_id}", json.dumps(metadata), ex=86400  # 24 hours
        )


class MLflowModelRegistry:
    """Manages model registration and versioning in MLflow"""

    def __init__(self):
        self.client = MlflowClient()
        self.redis_client = redis_cluster_manager

    async def register_model(
        self,
        model_uri: str,
        name: str,
        description: Optional[str] = None,
        tags: Dict[str, str] = None,
    ) -> str:
        """Register a model in the MLflow model registry"""
        try:
            model_version = mlflow.register_model(
                model_uri=model_uri, name=name, tags=tags
            )

            if description:
                self.client.update_model_version(
                    name=name, version=model_version.version, description=description
                )

            # Cache model version metadata
            await self._cache_model_version_metadata(name, model_version.version)

            logger.info(f"Registered model: {name} v{model_version.version}")
            return model_version.version

        except Exception as e:
            logger.error(f"Error registering model {name}: {e}")
            raise

    async def promote_model(self, name: str, version: str, stage: ModelStage):
        """Promote a model version to a specific stage"""
        try:
            self.client.transition_model_version_stage(
                name=name, version=version, stage=stage.value
            )

            # Update cache
            await self._update_model_stage_cache(name, version, stage)

            # Publish event
            await event_publisher.publish(
                "model.promoted",
                {
                    "model_name": name,
                    "version": version,
                    "stage": stage.value,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Promoted model {name} v{version} to {stage.value}")

        except Exception as e:
            logger.error(f"Error promoting model {name} v{version}: {e}")
            raise

    async def get_latest_version(
        self, name: str, stage: ModelStage = None
    ) -> Optional[str]:
        """Get the latest version of a model, optionally filtered by stage"""
        try:
            cache_key = f"mlflow:latest_version: {name}: {
                stage.value if stage else 'any'} "
            cached_version = await self.redis_client.get(cache_key)

            if cached_version:
                return cached_version

            versions = self.client.get_latest_versions(
                name=name, stages=[stage.value] if stage else None
            )

            if versions:
                latest_version = versions[0].version
                # 5 minutes
                await self.redis_client.set(cache_key, latest_version, ex=300)
                return latest_version

            return None

        except Exception as e:
            logger.error(f"Error getting latest version for model {name}: {e}")
            return None

    async def load_model(
        self, name: str, version: str = None, stage: ModelStage = None
    ):
        """Load a model from the MLflow model registry"""
        try:
            if version:
                model_uri = f"models:/{name}/{version}"
            elif stage:
                model_uri = f"models:/{name}/{stage.value}"
            else:
                # Get latest version
                latest_version = await self.get_latest_version(name)
                if not latest_version:
                    raise ValueError(f"No versions found for model {name}")
                model_uri = f"models:/{name}/{latest_version}"

            # Try to load from cache first
            cache_key = f"mlflow:model:{model_uri}"
            cached_model = await self.redis_client.get(cache_key)

            if cached_model:
                return pickle.loads(cached_model)

            # Load model from MLflow
            model = mlflow.sklearn.load_model(model_uri)

            # Cache model for future use (with TTL)
            await self.redis_client.set(
                cache_key, pickle.dumps(model), ex=3600  # 1 hour
            )

            return model

        except Exception as e:
            logger.error(f"Error loading model {name}: {e}")
            raise

    async def _cache_model_version_metadata(self, name: str, version: str):
        """Cache model version metadata in Redis"""
        model_version = self.client.get_model_version(name, version)

        metadata = {
            "name": name,
            "version": version,
            "creation_timestamp": model_version.creation_timestamp,
            "current_stage": model_version.current_stage,
            "description": model_version.description,
            "run_id": model_version.run_id,
            "source": model_version.source,
        }

        await self.redis_client.set(
            f"mlflow:model_version:{name}:{version}",
            json.dumps(metadata, default=str),
            ex=86400,  # 24 hours
        )

    async def _update_model_stage_cache(
        self, name: str, version: str, stage: ModelStage
    ):
        """Update model stage in cache"""
        cache_key = f"mlflow:model_version:{name}:{version}"
        cached_data = await self.redis_client.get(cache_key)

        if cached_data:
            metadata = json.loads(cached_data)
            metadata["current_stage"] = stage.value
            metadata["last_updated"] = datetime.utcnow().isoformat()

            await self.redis_client.set(
                cache_key, json.dumps(metadata), ex=86400  # 24 hours
            )


class ABTestingFramework:
    """A/B testing framework for model experiments"""

    def __init__(self):
        self.redis_client = redis_cluster_manager
        self.model_registry = MLflowModelRegistry()

    async def create_ab_test(self, config: ABTestConfig) -> str:
        """Create a new A/B test configuration"""
        test_id = f"ab_test_{
            config.test_name}_{
            datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        test_config = {
            "test_id": test_id,
            "test_name": config.test_name,
            "model_a_version": config.model_a_version,
            "model_b_version": config.model_b_version,
            "traffic_split": config.traffic_split,
            "success_metric": config.success_metric,
            "duration_days": config.duration_days,
            "minimum_sample_size": config.minimum_sample_size,
            "statistical_significance_threshold": config.statistical_significance_threshold,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (
                datetime.utcnow() + timedelta(days=config.duration_days)
            ).isoformat(),
            "status": "active",
            "results": {
                "model_a_metrics": {},
                "model_b_metrics": {},
                "sample_sizes": {"model_a": 0, "model_b": 0},
                "statistical_significance": None,
            },
        }

        # Store A/B test configuration
        await self.redis_client.set(
            f"ab_test:config:{test_id}",
            json.dumps(test_config),
            ex=86400 * config.duration_days * 2,  # Keep for twice the duration
        )

        # Add to active tests list
        await self.redis_client.sadd("ab_tests:active", test_id)

        logger.info(f"Created A/B test: {test_id}")
        return test_id

    async def get_model_for_user(self, test_id: str, user_id: str) -> Tuple[str, str]:
        """Get the assigned model version for a specific user in an A/B test"""
        # Check if user is already assigned
        assignment_key = f"ab_test:assignment:{test_id}:{user_id}"
        assigned_model = await self.redis_client.get(assignment_key)

        if assigned_model:
            return json.loads(assigned_model)

        # Get test configuration
        config = await self._get_ab_test_config(test_id)
        if not config:
            raise ValueError(f"A/B test {test_id} not found")

        # Determine assignment based on user ID hash
        import hashlib

        user_hash = int(hashlib.md5(f"{test_id}:{user_id}".encode()).hexdigest(), 16)
        assignment_bucket = (user_hash % 100) / 100.0

        if assignment_bucket < config["traffic_split"]:
            model_version = config["model_a_version"]
            model_variant = "model_a"
        else:
            model_version = config["model_b_version"]
            model_variant = "model_b"

        # Store assignment
        assignment = {"model_version": model_version, "variant": model_variant}
        await self.redis_client.set(
            assignment_key, json.dumps(assignment), ex=86400 * config["duration_days"]
        )

        return model_version, model_variant

    async def record_outcome(
        self,
        test_id: str,
        user_id: str,
        outcome_value: float,
        outcome_type: str = "conversion",
    ):
        """Record an outcome for A/B test analysis"""
        # Get user's model assignment
        assignment_key = f"ab_test:assignment:{test_id}:{user_id}"
        assignment = await self.redis_client.get(assignment_key)

        if not assignment:
            logger.warning(f"No assignment found for user {user_id} in test {test_id}")
            return

        assignment_data = json.loads(assignment)
        variant = assignment_data["variant"]

        # Record outcome
        outcome_data = {
            "user_id": user_id,
            "variant": variant,
            "outcome_value": outcome_value,
            "outcome_type": outcome_type,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store individual outcome
        await self.redis_client.lpush(
            f"ab_test:outcomes:{test_id}:{variant}", json.dumps(outcome_data)
        )

        # Update aggregate metrics
        await self._update_ab_test_metrics(
            test_id, variant, outcome_value, outcome_type
        )

    async def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get current results of an A/B test"""
        config = await self._get_ab_test_config(test_id)
        if not config:
            return {}

        # Get outcomes for both variants
        model_a_outcomes = await self._get_variant_outcomes(test_id, "model_a")
        model_b_outcomes = await self._get_variant_outcomes(test_id, "model_b")

        # Calculate statistics
        results = await self._calculate_ab_test_statistics(
            model_a_outcomes, model_b_outcomes, config["success_metric"]
        )

        return {
            "test_id": test_id,
            "test_name": config["test_name"],
            "status": config["status"],
            "model_a_version": config["model_a_version"],
            "model_b_version": config["model_b_version"],
            "results": results,
            "start_time": config["start_time"],
            "end_time": config["end_time"],
        }

    async def _get_ab_test_config(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get A/B test configuration"""
        config_data = await self.redis_client.get(f"ab_test:config:{test_id}")
        return json.loads(config_data) if config_data else None

    async def _get_variant_outcomes(
        self, test_id: str, variant: str
    ) -> List[Dict[str, Any]]:
        """Get all outcomes for a specific variant"""
        outcomes_data = await self.redis_client.lrange(
            f"ab_test:outcomes:{test_id}:{variant}", 0, -1
        )
        return [json.loads(outcome) for outcome in outcomes_data]

    async def _update_ab_test_metrics(
        self, test_id: str, variant: str, outcome_value: float, outcome_type: str
    ):
        """Update aggregate metrics for A/B test"""
        metrics_key = f"ab_test:metrics:{test_id}:{variant}"

        # Get current metrics
        current_metrics = await self.redis_client.get(metrics_key)
        if current_metrics:
            metrics = json.loads(current_metrics)
        else:
            metrics = {"total_samples": 0, "total_value": 0.0, "conversions": 0}

        # Update metrics
        metrics["total_samples"] += 1
        metrics["total_value"] += outcome_value
        if outcome_value > 0:  # Assuming positive values are conversions
            metrics["conversions"] += 1

        metrics["conversion_rate"] = metrics["conversions"] / metrics["total_samples"]
        metrics["average_value"] = metrics["total_value"] / metrics["total_samples"]

        # Store updated metrics
        await self.redis_client.set(metrics_key, json.dumps(metrics))

    async def _calculate_ab_test_statistics(
        self,
        model_a_outcomes: List[Dict],
        model_b_outcomes: List[Dict],
        success_metric: str,
    ) -> Dict[str, Any]:
        """Calculate statistical significance of A/B test results"""
        # Extract values for statistical analysis
        a_values = [outcome["outcome_value"] for outcome in model_a_outcomes]
        b_values = [outcome["outcome_value"] for outcome in model_b_outcomes]

        if not a_values or not b_values:
            return {"status": "insufficient_data"}

        # Calculate basic statistics
        a_mean = np.mean(a_values)
        b_mean = np.mean(b_values)
        a_std = np.std(a_values, ddof=1)
        b_std = np.std(b_values, ddof=1)

        # Perform t-test
        from scipy.stats import ttest_ind

        t_stat, p_value = ttest_ind(a_values, b_values)

        # Calculate confidence interval for the difference
        diff = b_mean - a_mean
        se_diff = np.sqrt((a_std**2 / len(a_values)) + (b_std**2 / len(b_values)))
        ci_lower = diff - 1.96 * se_diff
        ci_upper = diff + 1.96 * se_diff

        return {
            "model_a": {
                "sample_size": len(a_values),
                "mean": a_mean,
                "std": a_std,
                "conversion_rate": sum(1 for v in a_values if v > 0) / len(a_values),
            },
            "model_b": {
                "sample_size": len(b_values),
                "mean": b_mean,
                "std": b_std,
                "conversion_rate": sum(1 for v in b_values if v > 0) / len(b_values),
            },
            "statistical_test": {
                "t_statistic": t_stat,
                "p_value": p_value,
                "significant": p_value < 0.05,
                "confidence_interval": [ci_lower, ci_upper],
                "lift": (diff / a_mean) * 100 if a_mean != 0 else 0,
            },
            "status": "significant" if p_value < 0.05 else "not_significant",
        }


class MLflowIntegration:
    """Main integration class for MLflow functionality"""

    def __init__(self):
        self.experiment_manager = MLflowExperimentManager()
        self.model_registry = MLflowModelRegistry()
        self.ab_testing = ABTestingFramework()

    async def initialize(self):
        """Initialize MLflow integration"""
        try:
            # Set up default experiment
            default_experiment_config = ExperimentConfig(
                experiment_name="dinner_first_default",
                description="Default experiment for Dinner First AI models",
                tags={"project": "dinner_first", "environment": "production"},
            )

            await self.experiment_manager.create_experiment(default_experiment_config)
            logger.info("MLflow integration initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MLflow integration: {e}")
            raise

    async def create_model_experiment(
        self, model_name: str, description: str = None
    ) -> str:
        """Create a new experiment for model development"""
        experiment_config = ExperimentConfig(
            experiment_name=f"dinner_first_{model_name}",
            description=description or f"Experiment for {model_name} model development",
            tags={"project": "dinner_first", "model": model_name},
        )

        return await self.experiment_manager.create_experiment(experiment_config)

    async def train_and_register_model(
        self,
        model: BaseEstimator,
        model_name: str,
        experiment_id: str,
        training_data: pd.DataFrame,
        test_data: pd.DataFrame,
        hyperparameters: Dict[str, Any],
        model_metrics: ModelMetrics,
    ) -> str:
        """Train a model and register it in MLflow"""

        run_config = RunConfig(
            run_name=f"{model_name}_training_{
                datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            tags={
                "model_type": type(model).__name__,
                "training_date": datetime.utcnow().isoformat(),
            },
        )

        run_id = await self.experiment_manager.start_run(experiment_id, run_config)

        try:
            # Log hyperparameters
            await self.experiment_manager.log_params(hyperparameters)

            # Log dataset info
            await self.experiment_manager.log_params(
                {
                    "training_samples": len(training_data),
                    "test_samples": len(test_data),
                    "features": list(training_data.columns),
                }
            )

            # Log metrics
            metrics_dict = model_metrics.dict(exclude_none=True)
            await self.experiment_manager.log_metrics(metrics_dict)

            # Log model
            await self.experiment_manager.log_model(
                model=model, artifact_path="model", model_type="sklearn"
            )

            # End run successfully
            await self.experiment_manager.end_run(RunStatus.FINISHED)

            # Register model
            model_uri = f"runs:/{run_id}/model"
            version = await self.model_registry.register_model(
                model_uri=model_uri,
                name=model_name,
                description=f"Model trained on {datetime.utcnow().date()}",
            )

            return version

        except Exception as e:
            await self.experiment_manager.end_run(RunStatus.FAILED)
            logger.error(f"Failed to train and register model {model_name}: {e}")
            raise

    async def deploy_model_to_production(self, model_name: str, version: str) -> bool:
        """Deploy a model version to production"""
        try:
            await self.model_registry.promote_model(
                model_name, version, ModelStage.PRODUCTION
            )

            # Publish deployment event
            await event_publisher.publish(
                "model.deployed",
                {
                    "model_name": model_name,
                    "version": version,
                    "stage": "production",
                    "deployed_at": datetime.utcnow().isoformat(),
                },
            )

            return True

        except Exception as e:
            logger.error(f"Failed to deploy model {model_name} v{version}: {e}")
            return False

    async def create_model_ab_test(
        self,
        model_name: str,
        current_version: str,
        candidate_version: str,
        test_config: ABTestConfig,
    ) -> str:
        """Create an A/B test between two model versions"""
        # Update test config with model versions
        test_config.model_a_version = current_version
        test_config.model_b_version = candidate_version

        test_id = await self.ab_testing.create_ab_test(test_config)

        # Publish A/B test start event
        await event_publisher.publish(
            "ab_test.started",
            {
                "test_id": test_id,
                "model_name": model_name,
                "current_version": current_version,
                "candidate_version": candidate_version,
                "traffic_split": test_config.traffic_split,
                "started_at": datetime.utcnow().isoformat(),
            },
        )

        return test_id

    async def get_model_for_inference(self, model_name: str, user_id: str = None):
        """Get the appropriate model for inference, considering A/B tests"""
        # Check if user is part of any active A/B tests
        if user_id:
            active_tests = await self.redis_client.smembers("ab_tests:active")

            for test_id in active_tests:
                config = await self.ab_testing._get_ab_test_config(test_id)
                if config and model_name in [
                    config["model_a_version"],
                    config["model_b_version"],
                ]:
                    model_version, variant = await self.ab_testing.get_model_for_user(
                        test_id, user_id
                    )
                    return await self.model_registry.load_model(
                        model_name, version=model_version
                    )

        # Default to production model
        return await self.model_registry.load_model(
            model_name, stage=ModelStage.PRODUCTION
        )


# Global MLflow integration instance
mlflow_integration = MLflowIntegration()
