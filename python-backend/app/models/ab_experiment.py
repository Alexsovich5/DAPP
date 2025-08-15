# AB Testing experiment models for database storage

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()

class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running" 
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ABExperiment(Base):
    """AB testing experiment model"""
    __tablename__ = "ab_experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    feature_flag = Column(String(100), nullable=False)
    status = Column(String(20), default="draft")
    
    # Experiment configuration
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    target_users = Column(Integer, default=0)
    success_metric = Column(String(100))
    
    # Traffic allocation (percentage)
    traffic_allocation = Column(Float, default=1.0)
    
    # Statistical significance
    confidence_level = Column(Float, default=0.95)
    minimum_effect_size = Column(Float, default=0.05)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    variants = relationship("ExperimentVariant", back_populates="experiment")

class ExperimentVariant(Base):
    """Experiment variant model for A/B testing"""
    __tablename__ = "experiment_variants"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("ab_experiments.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Traffic allocation for this variant
    traffic_percentage = Column(Float, nullable=False)
    
    # Configuration for the variant
    configuration = Column(JSON)
    
    # Control variant flag
    is_control = Column(Boolean, default=False)
    
    # Results tracking
    conversion_count = Column(Integer, default=0)
    user_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    experiment = relationship("ABExperiment", back_populates="variants")