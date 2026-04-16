"""
A/B Testing Database Models
Database models for experiment management, variant tracking, and analysis
"""

import uuid
from datetime import datetime
from enum import Enum

from app.core.database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship


class ExperimentStatus(Enum):
    """Experiment lifecycle status"""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class VariantType(Enum):
    """Experiment variant type"""

    CONTROL = "control"
    TREATMENT = "treatment"


class MetricType(Enum):
    """Type of metric being measured"""

    CONVERSION = "conversion"  # Binary outcome (0 or 1)
    CONTINUOUS = "continuous"  # Numerical value
    COUNT = "count"  # Count of events
    DURATION = "duration"  # Time-based metrics


class Experiment(Base):
    """A/B Testing experiment configuration"""

    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(
        String, unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    name = Column(String, nullable=False)
    description = Column(Text)
    hypothesis = Column(Text)

    # Metrics configuration
    primary_metric = Column(String, nullable=False)
    secondary_metrics = Column(JSON, default=[])

    # Targeting and allocation
    target_audience = Column(JSON, default={})
    traffic_allocation = Column(Float, default=1.0)  # 0.0 to 1.0

    # Statistical configuration
    minimum_sample_size = Column(Integer, default=1000)
    confidence_level = Column(Float, default=0.95)
    minimum_effect_size = Column(Float, default=0.05)

    # Status and timing
    status = Column(String, default="draft")
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    variants = relationship(
        "ExperimentVariant",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
    assignments = relationship("UserAssignment", back_populates="experiment")
    events = relationship("ExperimentEvent", back_populates="experiment")


class ExperimentVariant(Base):
    """A/B Testing experiment variant configuration"""

    __tablename__ = "experiment_variants"

    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(
        String, unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    experiment_id = Column(Integer, ForeignKey("experiments.id"))

    name = Column(String, nullable=False)
    variant_type = Column(String, default="treatment")  # control, treatment
    description = Column(Text)

    # Traffic allocation
    traffic_allocation = Column(Float, nullable=False)  # 0.0 to 1.0

    # Variant configuration
    configuration = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    experiment = relationship("Experiment", back_populates="variants")
    assignments = relationship("UserAssignment", back_populates="variant")
    events = relationship("ExperimentEvent", back_populates="variant")


class UserAssignment(Base):
    """User assignment to experiment variants"""

    __tablename__ = "user_assignments"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(
        String, unique=True, index=True, default=lambda: str(uuid.uuid4())
    )

    user_id = Column(Integer, ForeignKey("users.id"))
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    variant_id = Column(Integer, ForeignKey("experiment_variants.id"))

    # Assignment metadata
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Assignment context
    assignment_context = Column(JSON, default={})  # Browser, device, etc.

    # Relationships
    user = relationship("User")
    experiment = relationship("Experiment", back_populates="assignments")
    variant = relationship("ExperimentVariant", back_populates="assignments")


class ExperimentEvent(Base):
    """Events tracked for A/B testing analysis"""

    __tablename__ = "experiment_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(
        String, unique=True, index=True, default=lambda: str(uuid.uuid4())
    )

    user_id = Column(Integer, ForeignKey("users.id"))
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    variant_id = Column(Integer, ForeignKey("experiment_variants.id"))
    assignment_id = Column(Integer, ForeignKey("user_assignments.id"))

    # Event details
    event_type = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)

    # Event metadata
    properties = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Session context
    session_id = Column(String)
    page_url = Column(String)
    user_agent = Column(String)

    # Relationships
    user = relationship("User")
    experiment = relationship("Experiment", back_populates="events")
    variant = relationship("ExperimentVariant", back_populates="events")
    assignment = relationship("UserAssignment")


class ExperimentResults(Base):
    """Cached experiment results and statistical analysis"""

    __tablename__ = "experiment_results"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))

    # Analysis configuration
    metric_name = Column(String, nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    confidence_level = Column(Float, default=0.95)

    # Statistical results
    control_conversion_rate = Column(Float)
    control_sample_size = Column(Integer)
    control_conversions = Column(Integer)

    treatment_conversion_rate = Column(Float)
    treatment_sample_size = Column(Integer)
    treatment_conversions = Column(Integer)

    # Statistical significance
    p_value = Column(Float)
    z_statistic = Column(Float)
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)
    lift = Column(Float)

    is_statistically_significant = Column(Boolean, default=False)
    is_practically_significant = Column(Boolean, default=False)

    # Recommendations
    # adopt_treatment, continue_testing, stop_experiment
    recommended_action = Column(String)
    recommendation_reason = Column(Text)

    # Full results JSON
    detailed_results = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    experiment = relationship("Experiment")
