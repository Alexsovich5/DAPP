"""
Continuous Learning Pipeline for Dinner First AI Platform

Implements automated model retraining, performance monitoring, and deployment
pipeline for continuous improvement of machine learning models in production.

Features:
- Automated data collection and labeling
- Model performance monitoring and drift detection
- Automated retraining pipeline
- A/B testing for model validation
- Gradual model rollout and rollback
- Feedback loop integration
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from app.ai.mlflow_integration import MLflowIntegration, ModelMetrics
from app.ai.model_registry import MLModelRegistry
from app.core.event_publisher import event_publisher
from app.core.redis_cluster import redis_cluster_manager
from pydantic import BaseModel, Field
from sklearn.base import BaseEstimator
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


class LearningStrategy(str, Enum):
    BATCH = "batch"
    ONLINE = "online"
    INCREMENTAL = "incremental"
    ENSEMBLE = "ensemble"


class ModelStatus(str, Enum):
    TRAINING = "training"
    VALIDATING = "validating"
    TESTING = "testing"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class DriftDetectionMethod(str, Enum):
    STATISTICAL = "statistical"
    KL_DIVERGENCE = "kl_divergence"
    PSI = "psi"  # Population Stability Index
    DOMAIN_CLASSIFIER = "domain_classifier"


class RetrainingTrigger(str, Enum):
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_DRIFT = "data_drift"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    FEEDBACK_THRESHOLD = "feedback_threshold"


class LearningConfig(BaseModel):
    model_name: str
    strategy: LearningStrategy = LearningStrategy.BATCH
    retraining_frequency_hours: int = 24
    performance_threshold: float = 0.8
    data_drift_threshold: float = 0.1
    minimum_samples_for_retraining: int = 1000
    validation_split: float = 0.2
    test_split: float = 0.1
    auto_deploy_threshold: float = 0.95
    rollback_threshold: float = 0.7
    max_training_time_minutes: int = 120


class FeedbackData(BaseModel):
    user_id: str
    model_name: str
    model_version: str
    prediction: Any
    actual_outcome: Optional[Any] = None
    feedback_score: Optional[float] = None
    feedback_type: str = "implicit"
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelPerformanceMetrics(BaseModel):
    model_name: str
    model_version: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: Optional[float] = None
    latency_ms: float
    throughput_rps: float
    error_rate: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DriftDetectionResult(BaseModel):
    model_name: str
    feature_name: str
    drift_score: float
    drift_detected: bool
    method: DriftDetectionMethod
    threshold: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RetrainingJob(BaseModel):
    job_id: str
    model_name: str
    trigger: RetrainingTrigger
    config: LearningConfig
    status: ModelStatus = ModelStatus.TRAINING
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    metrics: Optional[ModelPerformanceMetrics] = None
    error_message: Optional[str] = None


class DataCollector:
    """Collects and manages training data for continuous learning"""

    def __init__(self):
        self.redis_client = redis_cluster_manager

    async def collect_feedback(self, feedback: FeedbackData):
        """Collect user feedback for model improvement"""
        feedback_key = f"feedback:{feedback.model_name}:{feedback.timestamp.date()}"

        # Store individual feedback
        feedback_data = feedback.dict()
        await self.redis_client.lpush(
            feedback_key, json.dumps(feedback_data, default=str)
        )

        # Update aggregate statistics
        await self._update_feedback_stats(feedback)

        # Check if feedback threshold is reached
        await self._check_feedback_threshold(feedback.model_name)

    async def collect_prediction_data(
        self,
        model_name: str,
        model_version: str,
        features: Dict[str, Any],
        prediction: Any,
        user_id: str,
        context: Dict[str, Any] = None,
    ):
        """Collect prediction data for monitoring and retraining"""
        prediction_data = {
            "model_name": model_name,
            "model_version": model_version,
            "user_id": user_id,
            "features": features,
            "prediction": prediction,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store prediction data
        prediction_key = f"predictions:{model_name}:{datetime.utcnow().date()}"
        await self.redis_client.lpush(
            prediction_key, json.dumps(prediction_data, default=str)
        )

        # Update feature statistics for drift detection
        await self._update_feature_stats(model_name, features)

    async def get_training_data(
        self, model_name: str, days_back: int = 30
    ) -> pd.DataFrame:
        """Retrieve training data for model retraining"""
        training_data = []

        # Collect feedback data with labels
        for i in range(days_back):
            date = datetime.utcnow().date() - timedelta(days=i)
            feedback_key = f"feedback:{model_name}:{date}"

            feedback_entries = await self.redis_client.lrange(feedback_key, 0, -1)
            for entry in feedback_entries:
                feedback_data = json.loads(entry)
                if feedback_data.get("actual_outcome") is not None:
                    training_data.append(feedback_data)

        if not training_data:
            return pd.DataFrame()

        return pd.DataFrame(training_data)

    async def get_prediction_data(
        self, model_name: str, days_back: int = 7
    ) -> pd.DataFrame:
        """Retrieve recent prediction data for monitoring"""
        prediction_data = []

        for i in range(days_back):
            date = datetime.utcnow().date() - timedelta(days=i)
            prediction_key = f"predictions:{model_name}:{date}"

            predictions = await self.redis_client.lrange(prediction_key, 0, -1)
            for pred in predictions:
                prediction_data.append(json.loads(pred))

        if not prediction_data:
            return pd.DataFrame()

        return pd.DataFrame(prediction_data)

    async def _update_feedback_stats(self, feedback: FeedbackData):
        """Update aggregate feedback statistics"""
        stats_key = f"feedback_stats:{feedback.model_name}"

        # Get current stats
        current_stats = await self.redis_client.get(stats_key)
        if current_stats:
            stats = json.loads(current_stats)
        else:
            stats = {
                "total_feedback": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
                "average_score": 0.0,
                "last_updated": datetime.utcnow().isoformat(),
            }

        # Update stats
        stats["total_feedback"] += 1
        if feedback.feedback_score:
            if feedback.feedback_score > 0.5:
                stats["positive_feedback"] += 1
            else:
                stats["negative_feedback"] += 1

            # Update running average
            total_score = (
                stats["average_score"] * (stats["total_feedback"] - 1)
                + feedback.feedback_score
            )
            stats["average_score"] = total_score / stats["total_feedback"]

        stats["last_updated"] = datetime.utcnow().isoformat()

        # Store updated stats
        await self.redis_client.set(stats_key, json.dumps(stats, default=str))

    async def _update_feature_stats(self, model_name: str, features: Dict[str, Any]):
        """Update feature statistics for drift detection"""
        for feature_name, value in features.items():
            if isinstance(value, (int, float)):
                # Store value for statistical analysis
                feature_key = f"feature_values:{model_name}:{feature_name}"
                await self.redis_client.lpush(feature_key, str(value))

                # Keep only recent values (last 10000)
                await self.redis_client.ltrim(feature_key, 0, 9999)

    async def _check_feedback_threshold(self, model_name: str):
        """Check if feedback threshold is reached for retraining"""
        stats_key = f"feedback_stats:{model_name}"
        stats_data = await self.redis_client.get(stats_key)

        if stats_data:
            stats = json.loads(stats_data)
            if stats["total_feedback"] >= 100 and stats["average_score"] < 0.6:

                await event_publisher.publish(
                    "retraining.triggered",
                    {
                        "model_name": model_name,
                        "trigger": RetrainingTrigger.FEEDBACK_THRESHOLD.value,
                        "feedback_score": stats["average_score"],
                        "total_feedback": stats["total_feedback"],
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )


class DriftDetector:
    """Detects data and concept drift in model inputs and performance"""

    def __init__(self):
        self.redis_client = redis_cluster_manager
        self.data_collector = DataCollector()

    async def detect_feature_drift(
        self,
        model_name: str,
        method: DriftDetectionMethod = DriftDetectionMethod.STATISTICAL,
        baseline_days: int = 30,
        current_days: int = 7,
    ) -> List[DriftDetectionResult]:
        """Detect drift in input features"""

        # Get baseline and current feature data
        baseline_data = await self.data_collector.get_prediction_data(
            model_name, baseline_days + current_days
        )
        current_data = await self.data_collector.get_prediction_data(
            model_name, current_days
        )

        if baseline_data.empty or current_data.empty:
            return []

        # Split baseline and current data
        baseline_cutoff = len(baseline_data) - len(current_data)
        baseline_features = baseline_data.iloc[:baseline_cutoff]
        current_features = current_data

        drift_results = []

        # Extract features from nested dictionaries
        baseline_features_dict = self._extract_features(baseline_features)
        current_features_dict = self._extract_features(current_features)

        # Detect drift for each feature
        for feature_name in baseline_features_dict.keys():
            if feature_name in current_features_dict:
                drift_result = await self._detect_single_feature_drift(
                    model_name,
                    feature_name,
                    baseline_features_dict[feature_name],
                    current_features_dict[feature_name],
                    method,
                )
                drift_results.append(drift_result)

        return drift_results

    async def detect_performance_drift(
        self, model_name: str, performance_window_hours: int = 24
    ) -> bool:
        """Detect performance drift based on recent metrics"""

        # Get recent performance metrics
        metrics_key = f"performance_metrics:{model_name}"
        recent_metrics = await self.redis_client.lrange(metrics_key, 0, -1)

        if len(recent_metrics) < 10:  # Need sufficient data points
            return False

        # Parse metrics and check for performance degradation
        metrics_list = []
        cutoff_time = datetime.utcnow() - timedelta(hours=performance_window_hours)

        for metric_json in recent_metrics:
            metric = json.loads(metric_json)
            metric_time = datetime.fromisoformat(metric["timestamp"])

            if metric_time >= cutoff_time:
                metrics_list.append(metric)

        if len(metrics_list) < 5:
            return False

        # Calculate performance trend
        accuracy_scores = [m["accuracy"] for m in metrics_list]
        recent_avg = np.mean(accuracy_scores[: len(accuracy_scores) // 2])
        historical_avg = np.mean(accuracy_scores[len(accuracy_scores) // 2 :])

        # Drift detected if recent performance is significantly worse
        performance_drop = (historical_avg - recent_avg) / historical_avg
        return performance_drop > 0.05  # 5% performance drop threshold

    async def _detect_single_feature_drift(
        self,
        model_name: str,
        feature_name: str,
        baseline_values: List[float],
        current_values: List[float],
        method: DriftDetectionMethod,
    ) -> DriftDetectionResult:
        """Detect drift for a single feature"""

        if method == DriftDetectionMethod.STATISTICAL:
            # Use Kolmogorov-Smirnov test
            from scipy.stats import ks_2samp

            statistic, p_value = ks_2samp(baseline_values, current_values)
            drift_score = statistic
            drift_detected = p_value < 0.05
            threshold = 0.05

        elif method == DriftDetectionMethod.PSI:
            # Population Stability Index
            drift_score = self._calculate_psi(baseline_values, current_values)
            threshold = 0.1
            drift_detected = drift_score > threshold

        else:
            # Default statistical method
            drift_score = abs(
                np.mean(current_values) - np.mean(baseline_values)
            ) / np.std(baseline_values)
            threshold = 2.0  # 2 standard deviations
            drift_detected = drift_score > threshold

        return DriftDetectionResult(
            model_name=model_name,
            feature_name=feature_name,
            drift_score=drift_score,
            drift_detected=drift_detected,
            method=method,
            threshold=threshold,
        )

    def _extract_features(self, data: pd.DataFrame) -> Dict[str, List[float]]:
        """Extract numerical features from prediction data"""
        features_dict = {}

        for _, row in data.iterrows():
            if "features" in row and isinstance(row["features"], dict):
                for feature_name, value in row["features"].items():
                    if isinstance(value, (int, float)):
                        if feature_name not in features_dict:
                            features_dict[feature_name] = []
                        features_dict[feature_name].append(float(value))

        return features_dict

    def _calculate_psi(
        self, baseline: List[float], current: List[float], bins: int = 10
    ) -> float:
        """Calculate Population Stability Index"""

        # Create bins based on baseline distribution
        baseline_array = np.array(baseline)
        current_array = np.array(current)

        # Define bin edges
        bin_edges = np.percentile(baseline_array, np.linspace(0, 100, bins + 1))

        # Calculate distributions
        baseline_dist, _ = np.histogram(baseline_array, bins=bin_edges)
        current_dist, _ = np.histogram(current_array, bins=bin_edges)

        # Convert to proportions
        baseline_dist = baseline_dist / len(baseline_array)
        current_dist = current_dist / len(current_array)

        # Calculate PSI
        psi = 0
        for i in range(len(baseline_dist)):
            if baseline_dist[i] > 0 and current_dist[i] > 0:
                psi += (current_dist[i] - baseline_dist[i]) * np.log(
                    current_dist[i] / baseline_dist[i]
                )

        return psi


class ModelRetrainer:
    """Handles automated model retraining and validation"""

    def __init__(self):
        self.redis_client = redis_cluster_manager
        self.data_collector = DataCollector()
        self.model_registry = MLModelRegistry()
        self.mlflow_integration = MLflowIntegration()

    async def retrain_model(
        self,
        model_name: str,
        config: LearningConfig,
        trigger: RetrainingTrigger,
    ) -> RetrainingJob:
        """Execute model retraining process"""

        job_id = f"retrain_{model_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        job = RetrainingJob(
            job_id=job_id,
            model_name=model_name,
            trigger=trigger,
            config=config,
        )

        try:
            # Store job status
            await self._store_retraining_job(job)

            # Get training data
            training_data = await self.data_collector.get_training_data(
                model_name, days_back=30
            )

            if len(training_data) < config.minimum_samples_for_retraining:
                raise ValueError(
                    f"Insufficient training data: {
                        len(training_data)} samples"
                )

            # Prepare training data
            X, y = await self._prepare_training_data(training_data, model_name)
            X_train, X_temp, y_train, y_temp = train_test_split(
                X,
                y,
                test_size=config.validation_split + config.test_split,
                random_state=42,
                stratify=y,
            )

            val_test_split = config.test_split / (
                config.validation_split + config.test_split
            )
            X_val, X_test, y_val, y_test = train_test_split(
                X_temp,
                y_temp,
                test_size=val_test_split,
                random_state=42,
                stratify=y_temp,
            )

            # Update job status
            job.status = ModelStatus.TRAINING
            await self._store_retraining_job(job)

            # Train model
            new_model = await self._train_model(model_name, X_train, y_train, config)

            # Validate model
            job.status = ModelStatus.VALIDATING
            await self._store_retraining_job(job)

            await self._validate_model(new_model, X_val, y_val)

            # Test model
            job.status = ModelStatus.TESTING
            await self._store_retraining_job(job)

            test_metrics = await self._test_model(new_model, X_test, y_test)

            # Create new model version

            # Register model with MLflow
            model_metrics = ModelMetrics(
                accuracy=test_metrics["accuracy"],
                precision=test_metrics["precision"],
                recall=test_metrics["recall"],
                f1_score=test_metrics["f1_score"],
            )

            experiment_id = await self.mlflow_integration.create_model_experiment(
                model_name,
                f"Automated retraining triggered by {trigger.value}",
            )

            registered_version = await self.mlflow_integration.train_and_register_model(
                model=new_model,
                model_name=model_name,
                experiment_id=experiment_id,
                training_data=pd.DataFrame(X_train),
                test_data=pd.DataFrame(X_test),
                hyperparameters=await self._get_model_hyperparameters(model_name),
                model_metrics=model_metrics,
            )

            # Update job with results
            job.status = ModelStatus.ACTIVE
            job.end_time = datetime.utcnow()
            job.metrics = ModelPerformanceMetrics(
                model_name=model_name,
                model_version=registered_version,
                **test_metrics,
                latency_ms=0.0,  # TODO: Measure actual latency
                throughput_rps=0.0,  # TODO: Measure actual throughput
                error_rate=0.0,
            )

            await self._store_retraining_job(job)

            # Publish completion event
            await event_publisher.publish(
                "model.retrained",
                {
                    "job_id": job_id,
                    "model_name": model_name,
                    "new_version": registered_version,
                    "trigger": trigger.value,
                    "performance_metrics": test_metrics,
                    "training_samples": len(X_train),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return job

        except Exception as e:
            job.status = ModelStatus.FAILED
            job.end_time = datetime.utcnow()
            job.error_message = str(e)

            await self._store_retraining_job(job)
            logger.error(f"Model retraining failed for {model_name}: {e}")

            return job

    async def _prepare_training_data(
        self, raw_data: pd.DataFrame, model_name: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from collected feedback"""

        # This is a placeholder implementation
        # In practice, you would implement model-specific data preparation

        # Extract features and labels
        features = []
        labels = []

        for _, row in raw_data.iterrows():
            if "context" in row and "actual_outcome" in row:
                # Convert context to feature vector
                feature_vector = self._context_to_features(row["context"])
                features.append(feature_vector)
                labels.append(row["actual_outcome"])

        return np.array(features), np.array(labels)

    def _context_to_features(self, context: Dict[str, Any]) -> List[float]:
        """Convert context dictionary to feature vector"""
        # This is a placeholder - implement based on your specific features
        features = []

        # Example feature extraction
        features.append(context.get("user_age", 0))
        features.append(context.get("interaction_count", 0))
        features.append(context.get("time_of_day", 12))

        return features

    async def _train_model(
        self,
        model_name: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        config: LearningConfig,
    ) -> BaseEstimator:
        """Train a new model version"""

        # Get current model architecture
        current_model = await self.model_registry.get_model(model_name, "latest")

        if current_model:
            # Clone model architecture
            new_model = type(current_model)()
            new_model.set_params(**current_model.get_params())
        else:
            # Default model (placeholder - implement based on your models)
            from sklearn.ensemble import RandomForestClassifier

            new_model = RandomForestClassifier(n_estimators=100, random_state=42)

        # Train model
        new_model.fit(X_train, y_train)

        return new_model

    async def _validate_model(
        self, model: BaseEstimator, X_val: np.ndarray, y_val: np.ndarray
    ) -> Dict[str, float]:
        """Validate trained model"""
        y_pred = model.predict(X_val)

        return {
            "accuracy": accuracy_score(y_val, y_pred),
            "precision": precision_score(y_val, y_pred, average="weighted"),
            "recall": recall_score(y_val, y_pred, average="weighted"),
            "f1_score": f1_score(y_val, y_pred, average="weighted"),
        }

    async def _test_model(
        self, model: BaseEstimator, X_test: np.ndarray, y_test: np.ndarray
    ) -> Dict[str, float]:
        """Test final model performance"""
        return await self._validate_model(model, X_test, y_test)

    async def _get_model_hyperparameters(self, model_name: str) -> Dict[str, Any]:
        """Get hyperparameters for model"""
        # Placeholder - implement based on your model configurations
        return {"n_estimators": 100, "max_depth": 10, "random_state": 42}

    async def _store_retraining_job(self, job: RetrainingJob):
        """Store retraining job status"""
        job_key = f"retraining_job:{job.job_id}"
        await self.redis_client.set(
            job_key, job.json(), ex=86400 * 7  # Keep for 7 days
        )


class ContinuousLearningPipeline:
    """Main continuous learning pipeline orchestrator"""

    def __init__(self):
        self.redis_client = redis_cluster_manager
        self.data_collector = DataCollector()
        self.drift_detector = DriftDetector()
        self.model_retrainer = ModelRetrainer()
        self.model_registry = MLModelRegistry()
        self.mlflow_integration = MLflowIntegration()

        # Pipeline configuration
        self.learning_configs: Dict[str, LearningConfig] = {}
        self.active_models: Dict[str, str] = {}  # model_name -> version

        # Background tasks
        self._monitoring_task = None
        self._is_running = False

    async def initialize(self):
        """Initialize the continuous learning pipeline"""
        try:
            await self.mlflow_integration.initialize()
            logger.info("Continuous learning pipeline initialized")

        except Exception as e:
            logger.error(f"Failed to initialize continuous learning pipeline: {e}")
            raise

    async def register_model_for_learning(
        self, model_name: str, config: LearningConfig
    ):
        """Register a model for continuous learning"""
        self.learning_configs[model_name] = config

        # Store configuration in Redis
        config_key = f"learning_config:{model_name}"
        await self.redis_client.set(config_key, config.json())

        logger.info(f"Registered model {model_name} for continuous learning")

    async def start_monitoring(self):
        """Start the continuous monitoring process"""
        if self._is_running:
            return

        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started continuous learning monitoring")

    async def stop_monitoring(self):
        """Stop the monitoring process"""
        self._is_running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped continuous learning monitoring")

    async def trigger_retraining(
        self,
        model_name: str,
        trigger: RetrainingTrigger = RetrainingTrigger.MANUAL,
    ) -> str:
        """Manually trigger model retraining"""

        if model_name not in self.learning_configs:
            raise ValueError(
                f"Model {model_name} not registered for continuous learning"
            )

        config = self.learning_configs[model_name]
        job = await self.model_retrainer.retrain_model(model_name, config, trigger)

        return job.job_id

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        status = {
            "is_running": self._is_running,
            "registered_models": list(self.learning_configs.keys()),
            "active_retraining_jobs": [],
            "recent_drift_detections": [],
            "performance_summary": {},
        }

        # Get active retraining jobs
        job_keys = await self.redis_client.keys("retraining_job:*")
        for job_key in job_keys:
            job_data = await self.redis_client.get(job_key)
            if job_data:
                job = RetrainingJob.parse_raw(job_data)
                if job.status in [
                    ModelStatus.TRAINING,
                    ModelStatus.VALIDATING,
                    ModelStatus.TESTING,
                ]:
                    status["active_retraining_jobs"].append(job.dict())

        return status

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._is_running:
            try:
                await self._run_monitoring_cycle()
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _run_monitoring_cycle(self):
        """Run a single monitoring cycle"""

        for model_name, config in self.learning_configs.items():
            try:
                # Check for drift
                drift_results = await self.drift_detector.detect_feature_drift(
                    model_name
                )

                significant_drift = any(
                    result.drift_detected for result in drift_results
                )
                if significant_drift:
                    logger.warning(f"Data drift detected for model {model_name}")
                    await self._handle_drift_detection(
                        model_name, drift_results, config
                    )

                # Check performance drift
                performance_drift = await self.drift_detector.detect_performance_drift(
                    model_name
                )
                if performance_drift:
                    logger.warning(f"Performance drift detected for model {model_name}")
                    await self._handle_performance_drift(model_name, config)

                # Check scheduled retraining
                await self._check_scheduled_retraining(model_name, config)

            except Exception as e:
                logger.error(f"Error monitoring model {model_name}: {e}")

    async def _handle_drift_detection(
        self,
        model_name: str,
        drift_results: List[DriftDetectionResult],
        config: LearningConfig,
    ):
        """Handle detected data drift"""

        # Trigger retraining if drift is significant
        significant_features = [
            r.feature_name for r in drift_results if r.drift_detected
        ]

        if len(significant_features) > 2:  # Multiple features showing drift
            await event_publisher.publish(
                "retraining.triggered",
                {
                    "model_name": model_name,
                    "trigger": RetrainingTrigger.DATA_DRIFT.value,
                    "drift_features": significant_features,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            await self.trigger_retraining(model_name, RetrainingTrigger.DATA_DRIFT)

    async def _handle_performance_drift(self, model_name: str, config: LearningConfig):
        """Handle detected performance drift"""

        await event_publisher.publish(
            "retraining.triggered",
            {
                "model_name": model_name,
                "trigger": RetrainingTrigger.PERFORMANCE_DEGRADATION.value,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        await self.trigger_retraining(
            model_name, RetrainingTrigger.PERFORMANCE_DEGRADATION
        )

    async def _check_scheduled_retraining(
        self, model_name: str, config: LearningConfig
    ):
        """Check if scheduled retraining is due"""

        last_training_key = f"last_training:{model_name}"
        last_training = await self.redis_client.get(last_training_key)

        if last_training:
            last_time = datetime.fromisoformat(last_training)
            time_since_training = datetime.utcnow() - last_time

            hours_since = time_since_training.total_seconds() / 3600
            if hours_since > config.retraining_frequency_hours:
                await self.trigger_retraining(model_name, RetrainingTrigger.SCHEDULED)

                # Update last training time
                await self.redis_client.set(
                    last_training_key, datetime.utcnow().isoformat()
                )
        else:
            # First time - record current time
            await self.redis_client.set(
                last_training_key, datetime.utcnow().isoformat()
            )


# Global continuous learning pipeline instance
continuous_learning_pipeline = ContinuousLearningPipeline()
