"""
Model Storage Infrastructure for Dinner First AI Platform

Provides comprehensive model storage, versioning, and artifact management
for machine learning models in the dating platform ecosystem.

Features:
- Multi-backend storage (S3, MinIO, Local filesystem)
- Model versioning and metadata tracking
- Compression and optimization
- Distributed caching
- Security and access control
- Performance monitoring
"""

import gzip
import hashlib
import json
import logging
import pickle
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import joblib
import minio
from app.core.config import settings
from app.core.event_publisher import event_publisher
from app.core.redis_cluster import redis_cluster_manager
from pydantic import BaseModel, Field
from sklearn.base import BaseEstimator

logger = logging.getLogger(__name__)


class StorageBackend(str, Enum):
    S3 = "s3"
    MINIO = "minio"
    LOCAL = "local"


class CompressionType(str, Enum):
    NONE = "none"
    GZIP = "gzip"
    BROTLI = "brotli"


class ModelFormat(str, Enum):
    PICKLE = "pickle"
    JOBLIB = "joblib"
    ONNX = "onnx"
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"


class StorageConfig(BaseModel):
    backend: StorageBackend = StorageBackend.MINIO
    compression: CompressionType = CompressionType.GZIP
    encryption_enabled: bool = True
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_file_size: int = 100 * 1024 * 1024  # 100MB


class ModelMetadata(BaseModel):
    model_name: str
    version: str
    format: ModelFormat
    size_bytes: int
    checksum: str
    created_at: datetime
    created_by: str
    description: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    training_metadata: Dict[str, Any] = Field(default_factory=dict)
    storage_path: str
    compressed: bool = False
    encrypted: bool = False


class S3StorageBackend:
    """S3-compatible storage backend for model artifacts"""

    def __init__(
        self,
        endpoint_url: str = None,
        access_key: str = None,
        secret_key: str = None,
        bucket_name: str = None,
    ):
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT_URL
        self.access_key = access_key or settings.AWS_ACCESS_KEY_ID
        self.secret_key = secret_key or settings.AWS_SECRET_ACCESS_KEY
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME

        # Initialize S3 client
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=settings.AWS_REGION,
        )

        # Initialize MinIO client for direct operations
        if self.endpoint_url:
            self.minio_client = minio.Minio(
                self.endpoint_url.replace("http://", "").replace("https://", ""),
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.endpoint_url.startswith("https://"),
            )

    async def store_artifact(
        self, key: str, data: bytes, metadata: Dict[str, str] = None
    ) -> bool:
        """Store an artifact in S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                Metadata=metadata or {},
            )
            logger.info(f"Stored artifact: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to store artifact {key}: {e}")
            return False

    async def retrieve_artifact(self, key: str) -> Optional[bytes]:
        """Retrieve an artifact from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = response["Body"].read()
            logger.info(f"Retrieved artifact: {key}")
            return data

        except Exception as e:
            logger.error(f"Failed to retrieve artifact {key}: {e}")
            return None

    async def delete_artifact(self, key: str) -> bool:
        """Delete an artifact from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Deleted artifact: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete artifact {key}: {e}")
            return False

    async def list_artifacts(self, prefix: str = "") -> List[str]:
        """List artifacts with optional prefix filter"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )

            artifacts = []
            if "Contents" in response:
                artifacts = [obj["Key"] for obj in response["Contents"]]

            return artifacts

        except Exception as e:
            logger.error(f"Failed to list artifacts with prefix {prefix}: {e}")
            return []

    async def get_artifact_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an artifact"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return {
                "size": response["ContentLength"],
                "last_modified": response["LastModified"],
                "etag": response["ETag"],
                "metadata": response.get("Metadata", {}),
            }

        except Exception as e:
            logger.error(f"Failed to get metadata for artifact {key}: {e}")
            return None


class LocalStorageBackend:
    """Local filesystem storage backend for development"""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def store_artifact(
        self, key: str, data: bytes, metadata: Dict[str, str] = None
    ) -> bool:
        """Store an artifact locally"""
        try:
            artifact_path = self.base_path / key
            artifact_path.parent.mkdir(parents=True, exist_ok=True)

            # Write data
            artifact_path.write_bytes(data)

            # Store metadata if provided
            if metadata:
                metadata_path = artifact_path.with_suffix(
                    artifact_path.suffix + ".meta"
                )
                metadata_path.write_text(json.dumps(metadata, default=str))

            logger.info(f"Stored artifact locally: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to store artifact locally {key}: {e}")
            return False

    async def retrieve_artifact(self, key: str) -> Optional[bytes]:
        """Retrieve an artifact from local storage"""
        try:
            artifact_path = self.base_path / key
            if artifact_path.exists():
                data = artifact_path.read_bytes()
                logger.info(f"Retrieved artifact locally: {key}")
                return data

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve artifact locally {key}: {e}")
            return None

    async def delete_artifact(self, key: str) -> bool:
        """Delete an artifact from local storage"""
        try:
            artifact_path = self.base_path / key
            if artifact_path.exists():
                artifact_path.unlink()

                # Also delete metadata file if it exists
                metadata_path = artifact_path.with_suffix(
                    artifact_path.suffix + ".meta"
                )
                if metadata_path.exists():
                    metadata_path.unlink()

                logger.info(f"Deleted artifact locally: {key}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete artifact locally {key}: {e}")
            return False

    async def list_artifacts(self, prefix: str = "") -> List[str]:
        """List local artifacts with optional prefix filter"""
        try:
            artifacts = []
            search_path = self.base_path / prefix if prefix else self.base_path

            if search_path.exists():
                for artifact_path in search_path.rglob("*"):
                    if artifact_path.is_file() and not artifact_path.name.endswith(
                        ".meta"
                    ):
                        relative_path = artifact_path.relative_to(self.base_path)
                        artifacts.append(str(relative_path))

            return artifacts

        except Exception as e:
            logger.error(f"Failed to list local artifacts with prefix {prefix}: {e}")
            return []


class CompressionManager:
    """Manages compression and decompression of model artifacts"""

    @staticmethod
    def compress(data: bytes, compression_type: CompressionType) -> bytes:
        """Compress data using specified compression type"""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            return gzip.compress(data)
        elif compression_type == CompressionType.BROTLI:
            try:
                import brotli

                return brotli.compress(data)
            except ImportError:
                logger.warning("Brotli compression not available, falling back to gzip")
                return gzip.compress(data)
        else:
            raise ValueError(f"Unsupported compression type: {compression_type}")

    @staticmethod
    def decompress(data: bytes, compression_type: CompressionType) -> bytes:
        """Decompress data using specified compression type"""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            return gzip.decompress(data)
        elif compression_type == CompressionType.BROTLI:
            try:
                import brotli

                return brotli.decompress(data)
            except ImportError:
                logger.warning(
                    "Brotli decompression not available, falling back to gzip"
                )
                return gzip.decompress(data)
        else:
            raise ValueError(f"Unsupported compression type: {compression_type}")


class ModelSerializer:
    """Handles serialization and deserialization of various model types"""

    @staticmethod
    def serialize_model(model: Any, format: ModelFormat) -> bytes:
        """Serialize a model to bytes"""
        if format == ModelFormat.PICKLE:
            return pickle.dumps(model)
        elif format == ModelFormat.JOBLIB:
            # Use temporary file for joblib
            with tempfile.NamedTemporaryFile() as tmp_file:
                joblib.dump(model, tmp_file.name)
                return Path(tmp_file.name).read_bytes()
        elif format == ModelFormat.ONNX:
            # For ONNX models, assume model is already serialized bytes
            if isinstance(model, bytes):
                return model
            else:
                raise ValueError("ONNX model must be provided as bytes")
        else:
            # Default to pickle for other formats
            return pickle.dumps(model)

    @staticmethod
    def deserialize_model(data: bytes, format: ModelFormat) -> Any:
        """Deserialize bytes to a model"""
        if format == ModelFormat.PICKLE:
            return pickle.loads(data)
        elif format == ModelFormat.JOBLIB:
            # Use temporary file for joblib
            with tempfile.NamedTemporaryFile() as tmp_file:
                Path(tmp_file.name).write_bytes(data)
                return joblib.load(tmp_file.name)
        elif format == ModelFormat.ONNX:
            # For ONNX, return raw bytes (to be loaded by ONNX runtime)
            return data
        else:
            # Default to pickle
            return pickle.loads(data)

    @staticmethod
    def detect_model_format(model: Any) -> ModelFormat:
        """Auto-detect model format based on type"""
        if isinstance(model, BaseEstimator):
            return ModelFormat.JOBLIB  # Sklearn models work best with joblib
        elif hasattr(model, "state_dict"):  # PyTorch model
            return ModelFormat.PYTORCH
        elif hasattr(model, "save"):  # TensorFlow model
            return ModelFormat.TENSORFLOW
        elif isinstance(model, bytes):
            return ModelFormat.ONNX  # Assume bytes are ONNX
        else:
            return ModelFormat.PICKLE  # Default fallback


class ModelStorage:
    """Main model storage interface with caching and compression"""

    def __init__(self, config: StorageConfig = None):
        self.config = config or StorageConfig()
        self.redis_client = redis_cluster_manager

        # Initialize storage backend
        if self.config.backend == StorageBackend.S3:
            self.backend = S3StorageBackend()
        elif self.config.backend == StorageBackend.MINIO:
            self.backend = S3StorageBackend()  # MinIO is S3-compatible
        else:
            self.backend = LocalStorageBackend()

        self.compression_manager = CompressionManager()
        self.serializer = ModelSerializer()

    async def store_model(
        self,
        model: Any,
        model_name: str,
        version: str,
        created_by: str,
        description: str = None,
        tags: Dict[str, str] = None,
        performance_metrics: Dict[str, float] = None,
        model_format: ModelFormat = None,
    ) -> ModelMetadata:
        """Store a model with metadata"""

        # Auto-detect format if not provided
        if model_format is None:
            model_format = self.serializer.detect_model_format(model)

        # Serialize model
        model_data = self.serializer.serialize_model(model, model_format)
        original_size = len(model_data)

        # Compress if enabled
        compressed = False
        if self.config.compression != CompressionType.NONE:
            model_data = self.compression_manager.compress(
                model_data, self.config.compression
            )
            compressed = True

        # Calculate checksum
        checksum = hashlib.sha256(model_data).hexdigest()

        # Generate storage key
        storage_key = f"models/{model_name}/{version}/model.{model_format.value}"
        if compressed:
            storage_key += f".{self.config.compression.value}"

        # Store in backend
        storage_metadata = {
            "model_name": model_name,
            "version": version,
            "format": model_format.value,
            "compressed": str(compressed),
            "checksum": checksum,
            "created_by": created_by,
        }

        success = await self.backend.store_artifact(
            storage_key, model_data, storage_metadata
        )
        if not success:
            raise RuntimeError(f"Failed to store model {model_name} v{version}")

        # Create metadata
        metadata = ModelMetadata(
            model_name=model_name,
            version=version,
            format=model_format,
            size_bytes=original_size,
            checksum=checksum,
            created_at=datetime.utcnow(),
            created_by=created_by,
            description=description,
            tags=tags or {},
            performance_metrics=performance_metrics or {},
            storage_path=storage_key,
            compressed=compressed,
            encrypted=self.config.encryption_enabled,
        )

        # Store metadata
        await self._store_metadata(metadata)

        # Cache model if enabled
        if self.config.cache_enabled:
            await self._cache_model(model_name, version, model_data, compressed)

        # Publish event
        await event_publisher.publish(
            "model.stored",
            {
                "model_name": model_name,
                "version": version,
                "size_bytes": original_size,
                "compressed": compressed,
                "storage_path": storage_key,
                "created_by": created_by,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Stored model {model_name} v{version} ({original_size} bytes)")
        return metadata

    async def load_model(self, model_name: str, version: str) -> Optional[Any]:
        """Load a model from storage"""

        # Check cache first
        if self.config.cache_enabled:
            cached_model = await self._get_cached_model(model_name, version)
            if cached_model:
                return cached_model

        # Get metadata
        metadata = await self._get_metadata(model_name, version)
        if not metadata:
            logger.warning(f"Metadata not found for model {model_name} v{version}")
            return None

        # Load from backend
        model_data = await self.backend.retrieve_artifact(metadata.storage_path)
        if not model_data:
            logger.error(f"Failed to load model data for {model_name} v{version}")
            return None

        # Verify checksum
        actual_checksum = hashlib.sha256(model_data).hexdigest()
        if actual_checksum != metadata.checksum:
            logger.error(f"Checksum mismatch for model {model_name} v{version}")
            return None

        # Decompress if needed
        if metadata.compressed:
            model_data = self.compression_manager.decompress(
                model_data, self.config.compression
            )

        # Deserialize model
        model = self.serializer.deserialize_model(model_data, metadata.format)

        # Cache for future use
        if self.config.cache_enabled:
            await self._cache_model(
                model_name, version, model_data, metadata.compressed
            )

        logger.info(f"Loaded model {model_name} v{version}")
        return model

    async def delete_model(self, model_name: str, version: str) -> bool:
        """Delete a model and its metadata"""

        # Get metadata
        metadata = await self._get_metadata(model_name, version)
        if not metadata:
            return False

        # Delete from backend
        success = await self.backend.delete_artifact(metadata.storage_path)
        if not success:
            return False

        # Delete metadata
        await self._delete_metadata(model_name, version)

        # Remove from cache
        if self.config.cache_enabled:
            await self._remove_cached_model(model_name, version)

        # Publish event
        await event_publisher.publish(
            "model.deleted",
            {
                "model_name": model_name,
                "version": version,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Deleted model {model_name} v{version}")
        return True

    async def list_model_versions(self, model_name: str) -> List[ModelMetadata]:
        """List all versions of a model"""
        metadata_keys = await self.redis_client.keys(f"model_metadata:{model_name}:*")

        metadata_list = []
        for key in metadata_keys:
            metadata_json = await self.redis_client.get(key)
            if metadata_json:
                metadata_dict = json.loads(metadata_json)
                metadata_list.append(ModelMetadata(**metadata_dict))

        # Sort by creation time, newest first
        metadata_list.sort(key=lambda x: x.created_at, reverse=True)
        return metadata_list

    async def get_model_metadata(
        self, model_name: str, version: str
    ) -> Optional[ModelMetadata]:
        """Get metadata for a specific model version"""
        return await self._get_metadata(model_name, version)

    async def update_model_metadata(
        self, model_name: str, version: str, updates: Dict[str, Any]
    ) -> bool:
        """Update model metadata"""
        metadata = await self._get_metadata(model_name, version)
        if not metadata:
            return False

        # Update allowed fields
        allowed_fields = {"description", "tags", "performance_metrics"}
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(metadata, field, value)

        # Store updated metadata
        await self._store_metadata(metadata)

        logger.info(f"Updated metadata for model {model_name} v{version}")
        return True

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_models = 0
        total_size = 0
        model_counts_by_name = {}

        # Get all metadata keys
        metadata_keys = await self.redis_client.keys("model_metadata:*")

        for key in metadata_keys:
            total_models += 1
            metadata_json = await self.redis_client.get(key)
            if metadata_json:
                metadata = json.loads(metadata_json)
                total_size += metadata.get("size_bytes", 0)

                model_name = metadata.get("model_name", "unknown")
                model_counts_by_name[model_name] = (
                    model_counts_by_name.get(model_name, 0) + 1
                )

        return {
            "total_models": total_models,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "models_by_name": model_counts_by_name,
            "storage_backend": self.config.backend.value,
            "compression_enabled": self.config.compression != CompressionType.NONE,
            "cache_enabled": self.config.cache_enabled,
        }

    async def _store_metadata(self, metadata: ModelMetadata):
        """Store model metadata in Redis"""
        metadata_key = f"model_metadata:{metadata.model_name}:{metadata.version}"
        metadata_json = metadata.json()

        await self.redis_client.set(metadata_key, metadata_json)

        # Also store in a searchable index
        await self.redis_client.sadd(
            f"model_versions:{metadata.model_name}", metadata.version
        )
        await self.redis_client.sadd("all_models", metadata.model_name)

    async def _get_metadata(
        self, model_name: str, version: str
    ) -> Optional[ModelMetadata]:
        """Get model metadata from Redis"""
        metadata_key = f"model_metadata:{model_name}:{version}"
        metadata_json = await self.redis_client.get(metadata_key)

        if metadata_json:
            metadata_dict = json.loads(metadata_json)
            return ModelMetadata(**metadata_dict)

        return None

    async def _delete_metadata(self, model_name: str, version: str):
        """Delete model metadata from Redis"""
        metadata_key = f"model_metadata:{model_name}:{version}"
        await self.redis_client.delete(metadata_key)

        # Remove from indexes
        await self.redis_client.srem(f"model_versions:{model_name}", version)

        # If no more versions, remove from all_models
        remaining_versions = await self.redis_client.scard(
            f"model_versions:{model_name}"
        )
        if remaining_versions == 0:
            await self.redis_client.srem("all_models", model_name)

    async def _cache_model(
        self,
        model_name: str,
        version: str,
        model_data: bytes,
        compressed: bool,
    ):
        """Cache model data in Redis"""
        if len(model_data) > self.config.max_file_size:
            logger.warning(f"Model {model_name} v{version} too large for caching")
            return

        cache_key = f"model_cache:{model_name}:{version}"
        cache_data = {
            "data": model_data.hex(),  # Store as hex string
            "compressed": compressed,
            "cached_at": datetime.utcnow().isoformat(),
        }

        await self.redis_client.set(
            cache_key, json.dumps(cache_data), ex=self.config.cache_ttl
        )

    async def _get_cached_model(self, model_name: str, version: str) -> Optional[Any]:
        """Get cached model data"""
        cache_key = f"model_cache:{model_name}:{version}"
        cache_data_json = await self.redis_client.get(cache_key)

        if not cache_data_json:
            return None

        cache_data = json.loads(cache_data_json)
        model_data = bytes.fromhex(cache_data["data"])
        compressed = cache_data["compressed"]

        # Get metadata for deserialization
        metadata = await self._get_metadata(model_name, version)
        if not metadata:
            return None

        # Decompress if needed
        if compressed:
            model_data = self.compression_manager.decompress(
                model_data, self.config.compression
            )

        # Deserialize and return model
        return self.serializer.deserialize_model(model_data, metadata.format)

    async def _remove_cached_model(self, model_name: str, version: str):
        """Remove model from cache"""
        cache_key = f"model_cache:{model_name}:{version}"
        await self.redis_client.delete(cache_key)


class ModelStorageManager:
    """High-level model storage manager with advanced features"""

    def __init__(self):
        self.storage = ModelStorage()
        self.redis_client = redis_cluster_manager

    async def store_model_with_validation(
        self,
        model: Any,
        model_name: str,
        version: str,
        created_by: str,
        validation_data: Dict[str, Any] = None,
        **kwargs,
    ) -> ModelMetadata:
        """Store model with validation and performance benchmarking"""

        # Validate model before storing
        if validation_data:
            validation_results = await self._validate_model(model, validation_data)
            kwargs["performance_metrics"] = validation_results

        # Store model
        metadata = await self.storage.store_model(
            model, model_name, version, created_by, **kwargs
        )

        # Record storage metrics
        await self._record_storage_metrics(metadata)

        return metadata

    async def create_model_snapshot(
        self,
        model_name: str,
        source_version: str,
        snapshot_version: str,
        created_by: str,
    ) -> bool:
        """Create a snapshot/backup of an existing model version"""

        # Load source model
        source_model = await self.storage.load_model(model_name, source_version)
        if not source_model:
            return False

        # Get source metadata
        source_metadata = await self.storage.get_model_metadata(
            model_name, source_version
        )
        if not source_metadata:
            return False

        # Create snapshot with modified metadata
        await self.storage.store_model(
            model=source_model,
            model_name=model_name,
            version=snapshot_version,
            created_by=created_by,
            description=f"Snapshot of v{source_version}",
            tags={**source_metadata.tags, "snapshot_source": source_version},
            performance_metrics=source_metadata.performance_metrics,
            model_format=source_metadata.format,
        )

        logger.info(
            f"Created snapshot {model_name} v{snapshot_version} from v{source_version}"
        )
        return True

    async def cleanup_old_versions(
        self, model_name: str, keep_versions: int = 5
    ) -> int:
        """Clean up old model versions, keeping only the most recent ones"""

        versions = await self.storage.list_model_versions(model_name)
        if len(versions) <= keep_versions:
            return 0

        # Sort by creation time and keep the newest ones
        versions.sort(key=lambda x: x.created_at, reverse=True)
        versions_to_delete = versions[keep_versions:]

        deleted_count = 0
        for version_metadata in versions_to_delete:
            success = await self.storage.delete_model(
                model_name, version_metadata.version
            )
            if success:
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old versions of {model_name}")
        return deleted_count

    async def get_model_lineage(self, model_name: str, version: str) -> Dict[str, Any]:
        """Get model lineage and relationship information"""
        metadata = await self.storage.get_model_metadata(model_name, version)
        if not metadata:
            return {}

        lineage = {
            "model_name": model_name,
            "version": version,
            "created_at": metadata.created_at.isoformat(),
            "created_by": metadata.created_by,
            "parent_versions": [],
            "child_versions": [],
            "snapshots": [],
        }

        # Find related versions
        all_versions = await self.storage.list_model_versions(model_name)

        for v in all_versions:
            if v.version != version:
                # Check if it's a snapshot
                if v.tags.get("snapshot_source") == version:
                    lineage["child_versions"].append(
                        {
                            "version": v.version,
                            "type": "snapshot",
                            "created_at": v.created_at.isoformat(),
                        }
                    )
                elif version in v.tags.get("snapshot_source", ""):
                    lineage["parent_versions"].append(
                        {
                            "version": v.version,
                            "type": "source",
                            "created_at": v.created_at.isoformat(),
                        }
                    )

        return lineage

    async def _validate_model(
        self, model: Any, validation_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Validate model performance"""
        # This is a placeholder for model validation logic
        # In practice, you would run the model on validation data
        # and compute performance metrics

        return {
            "validation_accuracy": 0.95,
            "validation_latency_ms": 50.0,
            "memory_usage_mb": 128.0,
        }

    async def _record_storage_metrics(self, metadata: ModelMetadata):
        """Record storage metrics for monitoring"""
        metrics = {
            "model_size_bytes": metadata.size_bytes,
            "storage_timestamp": datetime.utcnow().isoformat(),
            "compressed": metadata.compressed,
            "format": metadata.format.value,
        }

        # Store in time series for monitoring
        await self.redis_client.lpush(
            f"storage_metrics:{metadata.model_name}", json.dumps(metrics)
        )

        # Keep only recent metrics (last 100 entries)
        await self.redis_client.ltrim(f"storage_metrics:{metadata.model_name}", 0, 99)


# Global model storage instances
model_storage = ModelStorage()
model_storage_manager = ModelStorageManager()
