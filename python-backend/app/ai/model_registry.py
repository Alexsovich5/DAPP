"""
Sprint 8: ML Model Registry with Versioning and A/B Testing
Comprehensive ML model lifecycle management for Dinner First platform
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import boto3
import mlflow
import mlflow.sklearn
from app.core.event_publisher import event_publisher
from app.core.redis_cluster import redis_cluster_manager

logger = logging.getLogger(__name__)


class ModelType(Enum):
    COMPATIBILITY_SCORER = "compatibility_scorer"
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    PERSONALITY_ANALYZER = "personality_analyzer"
    RECOMMENDATION_ENGINE = "recommendation_engine"


class ModelStatus(Enum):
    REGISTERED = "registered"
    TRAINING = "training"
    VALIDATION = "validation"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    FAILED = "failed"


@dataclass
class ModelMetrics:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float = 0.0
    user_satisfaction: float = 0.0
    processing_time_ms: float = 0.0
    model_size_mb: float = 0.0
    training_samples: int = 0
    validation_samples: int = 0
    deployment_ready: bool = False


@dataclass
class ModelVersion:
    model_name: str
    version: str
    model_type: ModelType
    status: ModelStatus
    metrics: ModelMetrics
    created_at: datetime
    created_by: str
    model_artifact_path: str
    feature_schema: Dict[str, Any]
    hyperparameters: Dict[str, Any]
    training_data_hash: str
    deployment_config: Dict[str, Any]
    experiment_id: Optional[str] = None
    run_id: Optional[str] = None
    tags: Dict[str, str] = None
    description: str = ""


class S3ModelStorage:
    """S3-compatible model artifact storage"""

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url="http://minio:9000",  # Local MinIO for development
            aws_access_key_id="dinner_first_ai",
            aws_secret_access_key="secure_ai_storage_key_2025",
            region_name="us-east-1",
        )
        self.bucket_name = "dinner-first-models"
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created S3 bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to create S3 bucket: {e}")

    async def upload_model(
        self, model_name: str, model_version: str, model_artifact: bytes
    ) -> str:
        """Upload model artifact to S3"""
        try:
            key = f"models/{model_name}/{model_version}/model.pkl"

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=model_artifact,
                Metadata={
                    "model-name": model_name,
                    "model-version": model_version,
                    "uploaded-at": datetime.utcnow().isoformat(),
                },
            )

            artifact_url = f"s3://{self.bucket_name}/{key}"
            logger.info(f"Model artifact uploaded: {artifact_url}")
            return artifact_url

        except Exception as e:
            logger.error(f"Failed to upload model artifact: {e}")
            raise

    async def download_model(self, artifact_path: str) -> bytes:
        """Download model artifact from S3"""
        try:
            # Extract bucket and key from s3:// URL
            path_parts = artifact_path.replace("s3://", "").split("/", 1)
            bucket = path_parts[0]
            key = path_parts[1]

            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()

        except Exception as e:
            logger.error(f"Failed to download model artifact: {e}")
            raise


class MLflowTracker:
    """MLflow experiment and run tracking"""

    def __init__(self):
        # Configure MLflow for local development
        mlflow.set_tracking_uri("http://mlflow:5000")
        self.experiment_name = "dinner_first_soul_matching"
        self._setup_experiment()

    def _setup_experiment(self):
        """Create MLflow experiment if it doesn't exist"""
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                self.experiment_id = mlflow.create_experiment(
                    name=self.experiment_name,
                    tags={
                        "project": "dinner_first",
                        "domain": "soul_matching",
                        "sprint": "8",
                    },
                )
            else:
                self.experiment_id = experiment.experiment_id

            mlflow.set_experiment(self.experiment_name)
            logger.info(f"MLflow experiment ready: {self.experiment_name}")

        except Exception as e:
            logger.error(f"Failed to setup MLflow experiment: {e}")
            self.experiment_id = None

    def start_run(self, run_name: str = None, tags: Dict[str, str] = None):
        """Start MLflow run"""
        return mlflow.start_run(run_name=run_name, tags=tags or {})

    def log_metrics(self, metrics: Dict[str, float]):
        """Log metrics to current run"""
        for key, value in metrics.items():
            mlflow.log_metric(key, value)

    def log_params(self, params: Dict[str, Any]):
        """Log parameters to current run"""
        for key, value in params.items():
            mlflow.log_param(key, str(value))

    def set_tags(self, tags: Dict[str, str]):
        """Set tags for current run"""
        for key, value in tags.items():
            mlflow.set_tag(key, value)

    def log_artifact(self, artifact_path: str):
        """Log artifact to current run"""
        mlflow.log_artifact(artifact_path)


class ModelPerformanceMonitor:
    """Monitor model performance in production"""

    def __init__(self):
        self.redis = redis_cluster_manager

    async def get_metrics(
        self, model_name: str, time_window: timedelta = timedelta(hours=24)
    ) -> Dict:
        """Get model performance metrics from production"""
        try:
            # Get performance data from Redis analytics database
            cluster = await self.redis.get_cluster(3)

            # Fetch recent prediction metrics
            metrics_key = f"model_performance:{model_name}"
            prefixed_key = self.redis._get_key_with_prefix(metrics_key, 3)

            # Get metrics from last 24 hours
            cutoff_time = int((datetime.utcnow() - time_window).timestamp() * 1000)
            metrics_data = await cluster.xrevrange(
                prefixed_key, min=cutoff_time, count=1000
            )

            if not metrics_data:
                return {
                    "accuracy": 0.0,
                    "user_satisfaction": 0.0,
                    "days_since_training": 999,
                    "prediction_count": 0,
                    "error_rate": 0.0,
                    "avg_response_time": 0.0,
                }

            # Process metrics
            total_predictions = len(metrics_data)
            accuracy_sum = 0.0
            satisfaction_sum = 0.0
            response_time_sum = 0.0
            error_count = 0

            for timestamp, fields in metrics_data:
                accuracy_sum += float(fields.get("accuracy", 0))
                satisfaction_sum += float(fields.get("user_satisfaction", 0))
                response_time_sum += float(fields.get("response_time_ms", 0))
                if fields.get("error") == "true":
                    error_count += 1

            # Calculate averages
            avg_accuracy = (
                accuracy_sum / total_predictions if total_predictions > 0 else 0.0
            )
            avg_satisfaction = (
                satisfaction_sum / total_predictions if total_predictions > 0 else 0.0
            )
            avg_response_time = (
                response_time_sum / total_predictions if total_predictions > 0 else 0.0
            )
            error_rate = (
                error_count / total_predictions if total_predictions > 0 else 0.0
            )

            # Get model creation date to calculate days since training
            model_info = await self.get_active_model_info(model_name)
            days_since_training = 0
            if model_info and model_info.get("created_at"):
                created_at = datetime.fromisoformat(model_info["created_at"])
                days_since_training = (datetime.utcnow() - created_at).days

            return {
                "accuracy": avg_accuracy,
                "user_satisfaction": avg_satisfaction,
                "days_since_training": days_since_training,
                "prediction_count": total_predictions,
                "error_rate": error_rate,
                "avg_response_time": avg_response_time,
            }

        except Exception as e:
            logger.error(f"Error getting model metrics: {e}")
            return {
                "accuracy": 0.0,
                "user_satisfaction": 0.0,
                "days_since_training": 999,
                "prediction_count": 0,
                "error_rate": 1.0,
                "avg_response_time": 0.0,
            }

    async def get_active_model_info(self, model_name: str) -> Optional[Dict]:
        """Get active model information"""
        try:
            cluster = await self.redis.get_cluster(5)  # Feature store
            key = f"active_model:{model_name}"
            prefixed_key = self.redis._get_key_with_prefix(key, 5)

            model_data = await cluster.get(prefixed_key)
            return json.loads(model_data) if model_data else None

        except Exception as e:
            logger.error(f"Error getting active model info: {e}")
            return None


class MLModelRegistry:
    """
    Comprehensive ML model registry with versioning, A/B testing, and learning
    """

    def __init__(self):
        self.redis_client = redis_cluster_manager
        self.model_storage = S3ModelStorage()
        self.experiment_tracker = MLflowTracker()
        self.performance_monitor = ModelPerformanceMonitor()

    async def register_model(
        self,
        model_name: str,
        model_version: str,
        model_artifact: bytes,
        model_type: ModelType,
        metrics: ModelMetrics,
        feature_schema: Dict[str, Any],
        hyperparameters: Dict[str, Any],
        training_data_hash: str,
        created_by: str,
        tags: Dict[str, str] = None,
        description: str = "",
    ) -> str:
        """Register new model version with comprehensive metadata"""

        try:
            # Upload model artifact
            artifact_url = await self.model_storage.upload_model(
                model_name, model_version, model_artifact
            )

            # Create MLflow run
            with self.experiment_tracker.start_run(
                run_name=f"{model_name}_v{model_version}", tags=tags or {}
            ) as run:

                # Log to MLflow
                self.experiment_tracker.log_metrics(asdict(metrics))
                self.experiment_tracker.log_params(hyperparameters)
                self.experiment_tracker.set_tags(
                    {
                        "model_name": model_name,
                        "model_version": model_version,
                        "model_type": model_type.value,
                        "created_by": created_by,
                    }
                )

                # Create model version object
                model_version_obj = ModelVersion(
                    model_name=model_name,
                    version=model_version,
                    model_type=model_type,
                    status=ModelStatus.REGISTERED,
                    metrics=metrics,
                    created_at=datetime.utcnow(),
                    created_by=created_by,
                    model_artifact_path=artifact_url,
                    feature_schema=feature_schema,
                    hyperparameters=hyperparameters,
                    training_data_hash=training_data_hash,
                    deployment_config={},
                    experiment_id=self.experiment_tracker.experiment_id,
                    run_id=run.info.run_id,
                    tags=tags or {},
                    description=description,
                )

                # Store in Redis
                await self._store_model_version(model_version_obj)

                # Publish registration event
                await event_publisher.publish_ai_model_trained(
                    model_name=model_name,
                    model_version=model_version,
                    performance_metrics=asdict(metrics),
                    source_service="ml-registry",
                )

                logger.info(f"Model registered: {model_name} v{model_version}")
                return f"{model_name}:{model_version}"

        except Exception as e:
            logger.error(f"Error registering model: {e}")
            raise

    async def _store_model_version(self, model_version: ModelVersion):
        """Store model version in Redis"""
        cluster = await self.redis_client.get_cluster(5)  # Feature store

        # Store model version
        version_key = (
            f"model_version:{model_version.model_name}:{model_version.version}"
        )
        prefixed_key = self.redis_client._get_key_with_prefix(version_key, 5)

        version_data = {
            **asdict(model_version),
            "created_at": model_version.created_at.isoformat(),
            "status": model_version.status.value,
            "model_type": model_version.model_type.value,
            "metrics": asdict(model_version.metrics),
        }

        # 30 days
        await cluster.setex(prefixed_key, 30 * 24 * 3600, json.dumps(version_data))

        # Update model versions list
        versions_key = f"model_versions:{model_version.model_name}"
        prefixed_versions_key = self.redis_client._get_key_with_prefix(versions_key, 5)
        await cluster.sadd(prefixed_versions_key, model_version.version)
        await cluster.expire(prefixed_versions_key, 30 * 24 * 3600)

    async def get_active_model(self, model_name: str) -> Optional[ModelVersion]:
        """Get currently active model for serving"""
        try:
            cluster = await self.redis_client.get_cluster(5)
            active_key = f"active_model:{model_name}"
            prefixed_key = self.redis_client._get_key_with_prefix(active_key, 5)

            model_data = await cluster.get(prefixed_key)
            if model_data:
                data = json.loads(model_data)
                return await self._deserialize_model_version(data)

            return None

        except Exception as e:
            logger.error(f"Error getting active model: {e}")
            return None

    async def promote_model(self, model_name: str, model_version: str) -> bool:
        """Promote model to active status after validation"""
        try:
            # Get model version
            model_ver = await self.get_model_version(model_name, model_version)
            if not model_ver:
                logger.error(f"Model version not found: {model_name}:{model_version}")
                return False

            # Get current active model for A/B testing
            current_model = await self.get_active_model(model_name)

            if current_model:
                # Run A/B test
                comparison_results = await self.run_ab_test(
                    model_name, current_model.version, model_version
                )

                if not comparison_results["new_model_better"]:
                    logger.info(f"A/B test failed for {model_name}:{model_version}")
                    return False

            # Promote to active
            await self._switch_active_model(model_name, model_version)

            # Update status
            model_ver.status = ModelStatus.PRODUCTION
            await self._store_model_version(model_ver)

            logger.info(f"Model promoted to production: {model_name}:{model_version}")
            return True

        except Exception as e:
            logger.error(f"Error promoting model: {e}")
            return False

    async def run_ab_test(
        self,
        model_name: str,
        current_version: str,
        new_version: str,
        test_duration_hours: int = 2,
    ) -> Dict[str, Any]:
        """Run A/B test between current and new model versions"""
        try:
            logger.info(
                f"Starting A/B test: {model_name} {current_version} vs {new_version}"
            )

            # For demonstration, we'll use cached performance metrics
            # In production, this would involve real traffic splitting

            current_metrics = await self.performance_monitor.get_metrics(model_name)

            # Simulate new model metrics (in reality, these would come from
            # test traffic)
            new_model = await self.get_model_version(model_name, new_version)
            if not new_model:
                return {
                    "new_model_better": False,
                    "reason": "New model not found",
                }

            # Compare metrics
            current_score = (
                current_metrics["accuracy"] * 0.4
                + current_metrics["user_satisfaction"] * 0.6
            )

            new_score = (
                new_model.metrics.accuracy * 0.4
                + new_model.metrics.user_satisfaction * 0.6
            )

            # Statistical significance check (simplified)
            improvement = new_score - current_score
            is_significant = improvement > 0.05  # 5% improvement threshold

            result = {
                "new_model_better": is_significant and new_score > current_score,
                "current_score": current_score,
                "new_score": new_score,
                "improvement": improvement,
                "statistically_significant": is_significant,
                "test_duration_hours": test_duration_hours,
                "recommendation": (
                    "promote" if is_significant and improvement > 0 else "reject"
                ),
            }

            # Log A/B test results
            await self._log_ab_test_result(
                model_name, current_version, new_version, result
            )

            return result

        except Exception as e:
            logger.error(f"Error running A/B test: {e}")
            return {"new_model_better": False, "error": str(e)}

    async def _switch_active_model(self, model_name: str, model_version: str):
        """Switch active model to new version"""
        cluster = await self.redis_client.get_cluster(5)

        # Get model version data
        model_ver = await self.get_model_version(model_name, model_version)
        if not model_ver:
            raise ValueError(f"Model version not found: {model_name}:{model_version}")

        # Store as active model
        active_key = f"active_model:{model_name}"
        prefixed_key = self.redis_client._get_key_with_prefix(active_key, 5)

        active_data = {
            "model_name": model_name,
            "version": model_version,
            "promoted_at": datetime.utcnow().isoformat(),
            "artifact_path": model_ver.model_artifact_path,
            "metrics": asdict(model_ver.metrics),
            "feature_schema": model_ver.feature_schema,
        }

        await cluster.setex(prefixed_key, 30 * 24 * 3600, json.dumps(active_data))

    async def get_model_version(
        self, model_name: str, model_version: str
    ) -> Optional[ModelVersion]:
        """Get specific model version"""
        try:
            cluster = await self.redis_client.get_cluster(5)
            version_key = f"model_version:{model_name}:{model_version}"
            prefixed_key = self.redis_client._get_key_with_prefix(version_key, 5)

            version_data = await cluster.get(prefixed_key)
            if version_data:
                data = json.loads(version_data)
                return await self._deserialize_model_version(data)

            return None

        except Exception as e:
            logger.error(f"Error getting model version: {e}")
            return None

    async def _deserialize_model_version(self, data: Dict) -> ModelVersion:
        """Deserialize model version from stored data"""
        metrics_data = data["metrics"]
        metrics = ModelMetrics(
            accuracy=metrics_data["accuracy"],
            precision=metrics_data["precision"],
            recall=metrics_data["recall"],
            f1_score=metrics_data["f1_score"],
            auc_roc=metrics_data["auc_roc"],
            user_satisfaction=metrics_data["user_satisfaction"],
            processing_time_ms=metrics_data["processing_time_ms"],
            model_size_mb=metrics_data["model_size_mb"],
            deployment_ready=metrics_data.get("deployment_ready", False),
        )

        return ModelVersion(
            model_name=data["model_name"],
            version=data["version"],
            model_type=ModelType(data["model_type"]),
            status=ModelStatus(data["status"]),
            metrics=metrics,
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=data["created_by"],
            model_artifact_path=data["model_artifact_path"],
            feature_schema=data["feature_schema"],
            hyperparameters=data["hyperparameters"],
            training_data_hash=data["training_data_hash"],
            deployment_config=data["deployment_config"],
            experiment_id=data["experiment_id"],
            run_id=data["run_id"],
            tags=data.get("tags", {}),
            description=data.get("description", ""),
        )

    async def _log_ab_test_result(
        self,
        model_name: str,
        current_version: str,
        new_version: str,
        result: Dict,
    ):
        """Log A/B test results for analysis"""
        cluster = await self.redis_client.get_cluster(3)  # Analytics database

        log_entry = {
            "model_name": model_name,
            "current_version": current_version,
            "new_version": new_version,
            "test_result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store in Redis streams
        stream_key = f"ab_test_results:{model_name}"
        prefixed_key = self.redis_client._get_key_with_prefix(stream_key, 3)
        await cluster.xadd(prefixed_key, log_entry)

        # Keep only last 1000 tests
        await cluster.xtrim(prefixed_key, maxlen=1000, approximate=True)

    async def list_model_versions(self, model_name: str) -> List[str]:
        """List all versions of a model"""
        try:
            cluster = await self.redis_client.get_cluster(5)
            versions_key = f"model_versions:{model_name}"
            prefixed_key = self.redis_client._get_key_with_prefix(versions_key, 5)

            versions = await cluster.smembers(prefixed_key)
            return sorted(list(versions), reverse=True) if versions else []

        except Exception as e:
            logger.error(f"Error listing model versions: {e}")
            return []

    async def get_model_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive model registry statistics"""
        try:
            cluster = await self.redis_client.get_cluster(5)

            stats = {
                "total_models": 0,
                "total_versions": 0,
                "active_models": 0,
                "models_by_type": {},
                "models_by_status": {},
                "recent_registrations": 0,
                "ab_tests_run": 0,
            }

            # Count models and versions
            db_prefix = (
                self.redis_client.db_configs[5].description.replace(" ", "_").lower()
            )

            model_names = set()
            for key in cluster.scan_iter(match=f"{db_prefix}:model_version:*"):
                key_parts = key.split(":")
                if len(key_parts) >= 4:
                    model_name = key_parts[2]
                    model_names.add(model_name)
                    stats["total_versions"] += 1

                    # Get model data for detailed stats
                    try:
                        model_data = await cluster.get(key)
                        if model_data:
                            data = json.loads(model_data)

                            # Count by type
                            model_type = data.get("model_type", "unknown")
                            stats["models_by_type"][model_type] = (
                                stats["models_by_type"].get(model_type, 0) + 1
                            )

                            # Count by status
                            status = data.get("status", "unknown")
                            stats["models_by_status"][status] = (
                                stats["models_by_status"].get(status, 0) + 1
                            )

                            # Count recent registrations (last 7 days)
                            created_at = datetime.fromisoformat(data["created_at"])
                            if (datetime.utcnow() - created_at).days <= 7:
                                stats["recent_registrations"] += 1

                    except Exception:
                        pass

            stats["total_models"] = len(model_names)

            # Count active models
            for key in cluster.scan_iter(match=f"{db_prefix}:active_model:*"):
                stats["active_models"] += 1

            # Count A/B tests (from analytics database)
            analytics_cluster = await self.redis_client.get_cluster(3)
            analytics_prefix = (
                self.redis_client.db_configs[3].description.replace(" ", "_").lower()
            )

            for key in cluster.scan_iter(match=f"{analytics_prefix}:ab_test_results:*"):
                try:
                    test_count = await analytics_cluster.xlen(key)
                    stats["ab_tests_run"] += test_count
                except Exception:
                    pass

            return stats

        except Exception as e:
            logger.error(f"Error getting registry stats: {e}")
            return {"error": str(e)}


# Global model registry instance
model_registry = MLModelRegistry()
