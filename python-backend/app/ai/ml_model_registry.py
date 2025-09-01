"""
ML Model Registry & Versioning System for Sprint 8 - Advanced Microservices Architecture
Comprehensive model lifecycle management with A/B testing, continuous learning, and performance monitoring
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import structlog
from core.event_publisher import EventPublisher, EventType

# Import our Redis cluster manager and event publisher
from core.redis_cluster_manager import DatabaseType, RedisClusterManager
from prometheus_client import Counter, Gauge, Histogram

logger = structlog.get_logger(__name__)

# Prometheus metrics
MODEL_PREDICTIONS = Counter(
    "ml_model_predictions_total",
    "Total model predictions",
    ["model_name", "version", "status"],
)
MODEL_TRAINING_DURATION = Histogram(
    "ml_model_training_duration_seconds", "Model training duration"
)
ACTIVE_MODELS = Gauge("ml_active_models", "Number of active models", ["model_type"])
MODEL_ACCURACY = Gauge(
    "ml_model_accuracy", "Model accuracy score", ["model_name", "version"]
)
MODEL_PERFORMANCE_DRIFT = Gauge(
    "ml_model_performance_drift", "Model performance drift", ["model_name", "version"]
)


class ModelType(Enum):
    """Supported model types"""

    COMPATIBILITY_MATCHING = "compatibility_matching"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    USER_RECOMMENDATION = "user_recommendation"
    CONVERSATION_STARTER = "conversation_starter"
    BEHAVIORAL_PREDICTION = "behavioral_prediction"
    FRAUD_DETECTION = "fraud_detection"


class ModelStatus(Enum):
    """Model lifecycle status"""

    TRAINING = "training"
    TRAINED = "trained"
    VALIDATING = "validating"
    ACTIVE = "active"
    CHAMPION = "champion"
    CHALLENGER = "challenger"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ModelMetrics:
    """Model performance metrics container"""

    def __init__(self):
        self.accuracy: float = 0.0
        self.precision: float = 0.0
        self.recall: float = 0.0
        self.f1_score: float = 0.0
        self.auc_roc: Optional[float] = None
        self.mse: Optional[float] = None
        self.mae: Optional[float] = None
        self.custom_metrics: Dict[str, float] = {}
        self.inference_latency_ms: float = 0.0
        self.throughput_qps: float = 0.0
        self.memory_usage_mb: float = 0.0
        self.cpu_usage_percent: float = 0.0

        # Business metrics
        self.user_engagement_lift: float = 0.0
        self.conversion_rate_improvement: float = 0.0
        self.user_satisfaction_score: float = 0.0

        self.timestamp: datetime = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "auc_roc": self.auc_roc,
            "mse": self.mse,
            "mae": self.mae,
            "custom_metrics": self.custom_metrics,
            "inference_latency_ms": self.inference_latency_ms,
            "throughput_qps": self.throughput_qps,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "user_engagement_lift": self.user_engagement_lift,
            "conversion_rate_improvement": self.conversion_rate_improvement,
            "user_satisfaction_score": self.user_satisfaction_score,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMetrics":
        """Create metrics from dictionary"""
        metrics = cls()
        for key, value in data.items():
            if key == "timestamp":
                metrics.timestamp = datetime.fromisoformat(value)
            elif hasattr(metrics, key):
                setattr(metrics, key, value)
        return metrics


class ModelArtifact:
    """Model artifact with metadata and versioning"""

    def __init__(
        self,
        name: str,
        version: str,
        model_type: ModelType,
        model_object: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):

        self.id = str(uuid.uuid4())
        self.name = name
        self.version = version
        self.model_type = model_type
        self.model_object = model_object
        self.metadata = metadata or {}

        self.status = ModelStatus.TRAINING
        self.metrics = ModelMetrics()
        self.training_data_hash: Optional[str] = None
        self.feature_schema: Optional[Dict[str, Any]] = None

        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.deployed_at: Optional[datetime] = None
        self.deprecated_at: Optional[datetime] = None

        # A/B Testing
        self.ab_test_group: Optional[str] = None
        self.traffic_percentage: float = 0.0
        self.champion_comparison: Optional[Dict[str, Any]] = None

        # Performance tracking
        self.prediction_count = 0
        self.error_count = 0
        self.total_inference_time = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert artifact to dictionary (without model object)"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "model_type": self.model_type.value,
            "metadata": self.metadata,
            "status": self.status.value,
            "metrics": self.metrics.to_dict(),
            "training_data_hash": self.training_data_hash,
            "feature_schema": self.feature_schema,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "deprecated_at": (
                self.deprecated_at.isoformat() if self.deprecated_at else None
            ),
            "ab_test_group": self.ab_test_group,
            "traffic_percentage": self.traffic_percentage,
            "champion_comparison": self.champion_comparison,
            "prediction_count": self.prediction_count,
            "error_count": self.error_count,
            "total_inference_time": self.total_inference_time,
        }


class MLModelRegistry:
    """
    Comprehensive ML Model Registry with versioning, A/B testing,
    and continuous performance monitoring
    """

    def __init__(
        self,
        redis_manager: RedisClusterManager,
        event_publisher: EventPublisher,
        model_storage_path: str = "/app/models",
    ):

        self.redis_manager = redis_manager
        self.event_publisher = event_publisher
        self.model_storage_path = Path(model_storage_path)
        self.model_storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory model cache for fast inference
        self.active_models: Dict[str, ModelArtifact] = {}
        self.model_cache_ttl = 3600  # 1 hour

        # A/B testing configuration
        self.ab_test_configs: Dict[str, Dict[str, Any]] = {}

        # Performance monitoring
        self.performance_monitor = ModelPerformanceMonitor()

        logger.info("ML Model Registry initialized")

    async def register_model(
        self,
        name: str,
        version: str,
        model_type: ModelType,
        model_object: Any,
        training_metrics: ModelMetrics,
        training_data_hash: str,
        feature_schema: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a new model version

        Args:
            name: Model name
            version: Model version
            model_type: Type of the model
            model_object: Trained model object
            training_metrics: Training performance metrics
            training_data_hash: Hash of training data for lineage
            feature_schema: Feature schema definition
            metadata: Additional metadata

        Returns:
            Model artifact ID
        """
        try:
            # Create model artifact
            artifact = ModelArtifact(
                name=name,
                version=version,
                model_type=model_type,
                model_object=model_object,
                metadata=metadata,
            )

            artifact.metrics = training_metrics
            artifact.training_data_hash = training_data_hash
            artifact.feature_schema = feature_schema
            artifact.status = ModelStatus.TRAINED

            # Save model to disk
            model_path = self._get_model_path(name, version)
            await self._save_model_to_disk(model_object, model_path)

            # Store metadata in Redis
            metadata_key = f"model_metadata:{name}:{version}"
            await self.redis_manager.set_with_ttl(
                DatabaseType.SENTIMENT_CACHE,
                metadata_key,
                artifact.to_dict(),
                ttl=86400,  # 24 hours
            )

            # Update model versions list
            versions_key = f"model_versions:{name}"
            versions = (
                await self.redis_manager.get(DatabaseType.SENTIMENT_CACHE, versions_key)
                or []
            )
            if version not in versions:
                versions.append(version)
                await self.redis_manager.set_with_ttl(
                    DatabaseType.SENTIMENT_CACHE, versions_key, versions, ttl=86400
                )

            # Publish model registration event
            await self.event_publisher.publish_analytics_event(
                EventType.PERFORMANCE_METRIC,
                {
                    "event_type": "model_registered",
                    "model_id": artifact.id,
                    "model_name": name,
                    "model_version": version,
                    "model_type": model_type.value,
                    "training_metrics": training_metrics.to_dict(),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Update Prometheus metrics
            ACTIVE_MODELS.labels(model_type=model_type.value).inc()
            MODEL_ACCURACY.labels(model_name=name, version=version).set(
                training_metrics.accuracy
            )

            logger.info(f"Model registered: {name}:{version} ({artifact.id})")

            return artifact.id

        except Exception as e:
            logger.error(f"Failed to register model {name}:{version}: {e}")
            raise

    async def get_active_model(self, name: str) -> Optional[ModelArtifact]:
        """Get currently active model version"""
        try:
            active_key = f"active_model:{name}"
            active_info = await self.redis_manager.get(
                DatabaseType.SENTIMENT_CACHE, active_key
            )

            if not active_info:
                return None

            return await self.load_model_for_inference(name, active_info["version"])

        except Exception as e:
            logger.error(f"Failed to get active model {name}: {e}")
            return None

    async def load_model_for_inference(
        self, name: str, version: Optional[str] = None
    ) -> Optional[ModelArtifact]:
        """
        Load model with model object for inference

        Args:
            name: Model name
            version: Model version (latest if None)

        Returns:
            Model artifact with loaded model object
        """
        try:
            artifact = await self.get_model(name, version)
            if not artifact:
                return None

            # Load model object from disk if not already loaded
            if artifact.model_object is None:
                model_path = self._get_model_path(name, artifact.version)
                artifact.model_object = await self._load_model_from_disk(model_path)

            # Cache in memory for fast access
            cache_key = f"{name}:{artifact.version}"
            self.active_models[cache_key] = artifact

            return artifact

        except Exception as e:
            logger.error(f"Failed to load model {name}:{version} for inference: {e}")
            return None

    async def get_model(
        self, name: str, version: Optional[str] = None
    ) -> Optional[ModelArtifact]:
        """
        Get model artifact by name and version

        Args:
            name: Model name
            version: Model version (latest if None)

        Returns:
            Model artifact or None if not found
        """
        try:
            if version is None:
                version = await self._get_latest_version(name)
                if not version:
                    return None

            # Check in-memory cache first
            cache_key = f"{name}:{version}"
            if cache_key in self.active_models:
                return self.active_models[cache_key]

            # Get metadata from Redis
            metadata_key = f"model_metadata:{name}:{version}"
            metadata = await self.redis_manager.get(
                DatabaseType.SENTIMENT_CACHE, metadata_key
            )

            if not metadata:
                return None

            # Create artifact (without model object initially)
            artifact = ModelArtifact(
                name=metadata["name"],
                version=metadata["version"],
                model_type=ModelType(metadata["model_type"]),
                metadata=metadata.get("metadata", {}),
            )

            # Restore other attributes
            artifact.id = metadata["id"]
            artifact.status = ModelStatus(metadata["status"])
            artifact.metrics = ModelMetrics.from_dict(metadata["metrics"])
            artifact.training_data_hash = metadata.get("training_data_hash")
            artifact.feature_schema = metadata.get("feature_schema")
            artifact.created_at = datetime.fromisoformat(metadata["created_at"])
            artifact.updated_at = datetime.fromisoformat(metadata["updated_at"])

            if metadata.get("deployed_at"):
                artifact.deployed_at = datetime.fromisoformat(metadata["deployed_at"])
            if metadata.get("deprecated_at"):
                artifact.deprecated_at = datetime.fromisoformat(
                    metadata["deprecated_at"]
                )

            artifact.ab_test_group = metadata.get("ab_test_group")
            artifact.traffic_percentage = metadata.get("traffic_percentage", 0.0)
            artifact.champion_comparison = metadata.get("champion_comparison")
            artifact.prediction_count = metadata.get("prediction_count", 0)
            artifact.error_count = metadata.get("error_count", 0)
            artifact.total_inference_time = metadata.get("total_inference_time", 0.0)

            return artifact

        except Exception as e:
            logger.error(f"Failed to get model {name}:{version}: {e}")
            return None

    def _get_model_path(self, name: str, version: str) -> Path:
        """Get file path for model storage"""
        return self.model_storage_path / f"{name}_{version}.pkl"

    async def _save_model_to_disk(self, model_object: Any, model_path: Path):
        """Save model object to disk"""
        try:
            with open(model_path, "wb") as f:
                if hasattr(model_object, "save"):
                    # For models with custom save method (e.g., TensorFlow, PyTorch)
                    model_object.save(str(model_path))
                else:
                    # Use joblib for sklearn models
                    joblib.dump(model_object, f)
        except Exception as e:
            logger.error(f"Failed to save model to {model_path}: {e}")
            raise

    async def _load_model_from_disk(self, model_path: Path) -> Any:
        """Load model object from disk"""
        try:
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")

            with open(model_path, "rb") as f:
                return joblib.load(f)
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}")
            raise

    async def _get_latest_version(self, name: str) -> Optional[str]:
        """Get latest version of a model"""
        try:
            versions_key = f"model_versions:{name}"
            versions = await self.redis_manager.get(
                DatabaseType.SENTIMENT_CACHE, versions_key
            )

            if not versions:
                return None

            # Sort versions and return latest (assuming semantic versioning)
            sorted_versions = sorted(
                versions,
                key=lambda x: [int(i) for i in x.split(".") if i.isdigit()],
                reverse=True,
            )
            return sorted_versions[0]

        except Exception as e:
            logger.error(f"Failed to get latest version for {name}: {e}")
            return None


class ModelPerformanceMonitor:
    """Monitor model performance and detect drift"""

    def __init__(self):
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        self.drift_threshold = 0.05  # 5% performance drop triggers alert

    async def record_prediction(
        self,
        model_name: str,
        model_version: str,
        prediction_result: Any,
        inference_time_ms: float,
        user_context: Optional[Dict[str, Any]] = None,
    ):
        """Record prediction for performance monitoring"""
        key = f"{model_name}:{model_version}"

        if key not in self.performance_history:
            self.performance_history[key] = []

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "inference_time_ms": inference_time_ms,
            "prediction_result": str(prediction_result)[:100],  # Truncate for storage
            "user_context": user_context,
        }

        self.performance_history[key].append(record)

        # Keep only recent history (last 1000 predictions)
        if len(self.performance_history[key]) > 1000:
            self.performance_history[key] = self.performance_history[key][-1000:]

    async def detect_performance_drift(
        self, model_name: str, model_version: str
    ) -> Optional[Dict[str, Any]]:
        """Detect performance drift for a model"""
        key = f"{model_name}:{model_version}"

        if (
            key not in self.performance_history
            or len(self.performance_history[key]) < 100
        ):
            return None

        history = self.performance_history[key]

        # Analyze recent performance vs historical baseline
        recent_data = history[-50:]  # Last 50 predictions
        baseline_data = history[-200:-50]  # Previous 150 predictions

        if len(baseline_data) < 50:
            return None

        recent_avg_time = np.mean([r["inference_time_ms"] for r in recent_data])
        baseline_avg_time = np.mean([r["inference_time_ms"] for r in baseline_data])

        # Calculate drift
        time_drift = (
            (recent_avg_time - baseline_avg_time) / baseline_avg_time
            if baseline_avg_time > 0
            else 0
        )

        if abs(time_drift) > self.drift_threshold:
            drift_info = {
                "model_name": model_name,
                "model_version": model_version,
                "drift_type": "inference_time",
                "drift_magnitude": time_drift,
                "recent_avg_time_ms": recent_avg_time,
                "baseline_avg_time_ms": baseline_avg_time,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Update Prometheus metric
            MODEL_PERFORMANCE_DRIFT.labels(
                model_name=model_name, version=model_version
            ).set(abs(time_drift))

            return drift_info

        return None


# Global model registry instance
model_registry: Optional[MLModelRegistry] = None


def get_model_registry() -> MLModelRegistry:
    """Get global model registry instance"""
    global model_registry
    if model_registry is None:
        raise Exception(
            "Model registry not initialized. Call init_model_registry first."
        )
    return model_registry


async def init_model_registry(
    redis_manager: RedisClusterManager,
    event_publisher: EventPublisher,
    model_storage_path: str = "/app/models",
) -> MLModelRegistry:
    """Initialize global model registry"""
    global model_registry
    model_registry = MLModelRegistry(redis_manager, event_publisher, model_storage_path)
    logger.info("Model registry initialized globally")
    return model_registry
