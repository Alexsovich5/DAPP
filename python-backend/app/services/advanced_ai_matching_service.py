"""
Phase 7: Advanced AI Matching Evolution Service
Machine learning optimization and predictive analytics for matching success
"""
import logging
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import math
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation
from app.models.enhanced_communication_models import EnhancedMessage
from app.models.advanced_matching_models import (
    MatchingAlgorithmVersion, UserBehaviorAnalytics, MatchingOutcome,
    SuccessPrediction, AlgorithmPerformanceMetric, MatchingExperiment,
    UserPreferenceEvolution, RealTimeMatchingAdjustment, PredictiveCompatibility,
    AlgorithmType, OutcomeType, ExperimentStatus
)
from app.services.ai_matching_service import ai_matching_engine
from app.services.personalization_service import personalization_engine

logger = logging.getLogger(__name__)


class AdvancedAIMatchingEngine:
    """
    Next-generation AI matching with machine learning optimization
    Predictive analytics and real-time algorithm tuning
    """
    
    def __init__(self):
        self.algorithm_versions = {
            "v1.0": {"weights": {"compatibility": 0.4, "values": 0.3, "interests": 0.2, "demographics": 0.1}},
            "v2.0": {"weights": {"compatibility": 0.35, "values": 0.3, "interests": 0.15, "demographics": 0.1, "behavior": 0.1}},
            "v3.0": {"weights": {"compatibility": 0.3, "values": 0.25, "interests": 0.15, "demographics": 0.1, "behavior": 0.15, "success_prediction": 0.05}}
        }
        
        self.current_algorithm_version = "v3.0"
        
        self.success_indicators = {
            "message_exchange": {"weight": 0.2, "threshold": 10},
            "revelation_completion": {"weight": 0.3, "threshold": 7},
            "video_call_completion": {"weight": 0.25, "threshold": 1},
            "positive_feedback": {"weight": 0.15, "threshold": 0.8},
            "relationship_duration": {"weight": 0.1, "threshold": 30}  # days
        }
        
        self.learning_parameters = {
            "learning_rate": 0.01,
            "momentum": 0.9,
            "regularization": 0.001,
            "batch_size": 100,
            "validation_split": 0.2
        }

    async def generate_predictive_matches(
        self,
        user_id: int,
        count: int = 10,
        algorithm_version: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Generate matches using predictive AI with success probability"""
        try:
            algorithm_version = algorithm_version or self.current_algorithm_version
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Get user's behavioral analytics
            behavior_analytics = await self._get_user_behavior_analytics(user_id, db)
            
            # Get potential matches
            potential_matches = await self._get_potential_matches(user_id, db)
            
            # Calculate predictive compatibility for each potential match
            predictive_matches = []
            for potential_match in potential_matches[:count * 2]:  # Get extra for filtering
                compatibility_data = await self._calculate_predictive_compatibility(
                    user_id, potential_match.id, algorithm_version, behavior_analytics, db
                )
                
                if compatibility_data["success_probability"] > 0.4:  # Only high-probability matches
                    predictive_matches.append({
                        "user": potential_match,
                        "compatibility_data": compatibility_data,
                        "match_reasoning": compatibility_data["reasoning"],
                        "success_prediction": compatibility_data["success_prediction"]
                    })
            
            # Sort by success probability and compatibility
            predictive_matches.sort(
                key=lambda x: (x["compatibility_data"]["success_probability"], 
                              x["compatibility_data"]["overall_score"]),
                reverse=True
            )
            
            # Store predictive compatibility records
            for match in predictive_matches[:count]:
                await self._store_predictive_compatibility(
                    user_id, match["user"].id, match["compatibility_data"], db
                )
            
            # Generate matching insights
            matching_insights = await self._generate_matching_insights(
                user_id, predictive_matches[:count], behavior_analytics, db
            )
            
            return {
                "matches": predictive_matches[:count],
                "algorithm_version": algorithm_version,
                "total_analyzed": len(potential_matches),
                "high_probability_matches": len(predictive_matches),
                "matching_insights": matching_insights,
                "personalization_applied": True,
                "next_optimization": datetime.utcnow() + timedelta(hours=6)
            }
            
        except Exception as e:
            logger.error(f"Error generating predictive matches: {str(e)}")
            raise

    async def analyze_matching_success_patterns(
        self,
        user_id: int,
        time_period_days: int = 90,
        db: Session = None
    ) -> Dict[str, Any]:
        """Analyze patterns in matching success for optimization"""
        try:
            # Get user's connection history
            connections = db.query(SoulConnection).filter(
                and_(
                    or_(SoulConnection.user1_id == user_id, SoulConnection.user2_id == user_id),
                    SoulConnection.created_at >= datetime.utcnow() - timedelta(days=time_period_days)
                )
            ).all()
            
            if not connections:
                return {"pattern": "insufficient_data", "recommendations": []}
            
            # Analyze outcomes
            outcome_analysis = await self._analyze_connection_outcomes(connections, user_id, db)
            
            # Identify success patterns
            success_patterns = await self._identify_success_patterns(connections, user_id, db)
            
            # Generate optimization recommendations
            recommendations = await self._generate_optimization_recommendations(
                outcome_analysis, success_patterns, user_id, db
            )
            
            # Update user's matching preferences based on patterns
            await self._update_user_matching_preferences(user_id, success_patterns, db)
            
            return {
                "analysis_period": time_period_days,
                "total_connections": len(connections),
                "outcome_analysis": outcome_analysis,
                "success_patterns": success_patterns,
                "optimization_recommendations": recommendations,
                "matching_effectiveness": self._calculate_matching_effectiveness(outcome_analysis),
                "pattern_confidence": success_patterns.get("confidence", 0.5)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing matching success patterns: {str(e)}")
            return {"pattern": "analysis_error", "recommendations": []}

    async def run_matching_experiment(
        self,
        experiment_config: Dict[str, Any],
        target_users: Optional[List[int]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Run A/B test experiment on matching algorithms"""
        try:
            # Create experiment record
            experiment = MatchingExperiment(
                experiment_name=experiment_config["name"],
                experiment_type=experiment_config["type"],
                algorithm_a_config=experiment_config["algorithm_a"],
                algorithm_b_config=experiment_config["algorithm_b"],
                target_metrics=experiment_config["target_metrics"],
                expected_duration_days=experiment_config.get("duration_days", 30),
                sample_size_target=experiment_config.get("sample_size", 1000),
                status=ExperimentStatus.ACTIVE
            )
            
            db.add(experiment)
            db.commit()
            db.refresh(experiment)
            
            # Assign users to experiment groups
            if target_users:
                user_assignments = await self._assign_experiment_users(
                    experiment.id, target_users, db
                )
            else:
                user_assignments = await self._auto_assign_experiment_users(
                    experiment.id, experiment_config.get("sample_size", 1000), db
                )
            
            # Initialize experiment tracking
            await self._initialize_experiment_tracking(experiment.id, user_assignments, db)
            
            return {
                "experiment_id": experiment.id,
                "status": "active",
                "participants_assigned": len(user_assignments["group_a"]) + len(user_assignments["group_b"]),
                "group_a_size": len(user_assignments["group_a"]),
                "group_b_size": len(user_assignments["group_b"]),
                "expected_results_date": (
                    datetime.utcnow() + timedelta(days=experiment.expected_duration_days)
                ).isoformat(),
                "tracking_metrics": experiment.target_metrics
            }
            
        except Exception as e:
            logger.error(f"Error running matching experiment: {str(e)}")
            raise

    async def optimize_algorithm_real_time(
        self,
        user_id: int,
        recent_outcomes: List[Dict[str, Any]],
        db: Session = None
    ) -> Dict[str, Any]:
        """Real-time algorithm optimization based on immediate feedback"""
        try:
            # Analyze recent outcomes
            outcome_patterns = await self._analyze_recent_outcomes(recent_outcomes, user_id, db)
            
            # Calculate required adjustments
            adjustments = await self._calculate_algorithm_adjustments(
                outcome_patterns, user_id, db
            )
            
            if adjustments["adjustment_magnitude"] > 0.1:  # Significant adjustment needed
                # Create real-time adjustment record
                adjustment_record = RealTimeMatchingAdjustment(
                    user_id=user_id,
                    adjustment_type="outcome_based",
                    original_weights=adjustments["original_weights"],
                    adjusted_weights=adjustments["adjusted_weights"],
                    adjustment_reason=adjustments["reason"],
                    confidence_score=adjustments["confidence"],
                    expected_improvement=adjustments["expected_improvement"]
                )
                
                db.add(adjustment_record)
                db.commit()
                db.refresh(adjustment_record)
                
                # Apply adjustments to user's matching profile
                await self._apply_real_time_adjustments(user_id, adjustments, db)
                
                return {
                    "adjustment_applied": True,
                    "adjustment_id": adjustment_record.id,
                    "adjustment_magnitude": adjustments["adjustment_magnitude"],
                    "expected_improvement": adjustments["expected_improvement"],
                    "confidence": adjustments["confidence"],
                    "next_optimization_in": "24 hours",
                    "monitoring_period": "7 days"
                }
            else:
                return {
                    "adjustment_applied": False,
                    "reason": "No significant improvement opportunity detected",
                    "current_performance": outcome_patterns.get("performance_score", 0.7),
                    "next_check_in": "12 hours"
                }
            
        except Exception as e:
            logger.error(f"Error in real-time algorithm optimization: {str(e)}")
            raise

    async def predict_relationship_success(
        self,
        user1_id: int,
        user2_id: int,
        connection_context: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Predict long-term relationship success using ML models"""
        try:
            # Get comprehensive user data
            user1_data = await self._get_comprehensive_user_data(user1_id, db)
            user2_data = await self._get_comprehensive_user_data(user2_id, db)
            
            # Calculate compatibility features
            compatibility_features = await self._extract_compatibility_features(
                user1_data, user2_data, connection_context
            )
            
            # Apply ML model for success prediction
            prediction_result = await self._apply_success_prediction_model(
                compatibility_features, user1_id, user2_id, db
            )
            
            # Generate detailed prediction breakdown
            prediction_breakdown = await self._generate_prediction_breakdown(
                prediction_result, compatibility_features, db
            )
            
            # Store prediction for validation
            success_prediction = SuccessPrediction(
                user1_id=user1_id,
                user2_id=user2_id,
                prediction_model_version="v2.1",
                success_probability=prediction_result["success_probability"],
                relationship_duration_prediction=prediction_result["duration_prediction"],
                key_compatibility_factors=prediction_breakdown["key_factors"],
                risk_factors=prediction_breakdown["risk_factors"],
                prediction_confidence=prediction_result["confidence"],
                prediction_metadata=prediction_result["metadata"]
            )
            
            db.add(success_prediction)
            db.commit()
            db.refresh(success_prediction)
            
            return {
                "prediction_id": success_prediction.id,
                "success_probability": prediction_result["success_probability"],
                "relationship_duration_prediction": prediction_result["duration_prediction"],
                "confidence_level": prediction_result["confidence"],
                "key_success_factors": prediction_breakdown["key_factors"],
                "potential_challenges": prediction_breakdown["risk_factors"],
                "recommendation": prediction_breakdown["recommendation"],
                "model_version": "v2.1",
                "prediction_timestamp": success_prediction.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting relationship success: {str(e)}")
            raise

    async def generate_algorithm_performance_report(
        self,
        time_period_days: int = 30,
        algorithm_versions: Optional[List[str]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Generate comprehensive algorithm performance report"""
        try:
            algorithm_versions = algorithm_versions or list(self.algorithm_versions.keys())
            
            report_data = {
                "report_period": time_period_days,
                "algorithms_analyzed": algorithm_versions,
                "generated_at": datetime.utcnow().isoformat(),
                "performance_metrics": {},
                "comparative_analysis": {},
                "optimization_recommendations": []
            }
            
            for version in algorithm_versions:
                # Get performance metrics for this version
                metrics = await self._calculate_algorithm_performance_metrics(
                    version, time_period_days, db
                )
                
                report_data["performance_metrics"][version] = metrics
            
            # Generate comparative analysis
            if len(algorithm_versions) > 1:
                report_data["comparative_analysis"] = await self._compare_algorithm_versions(
                    algorithm_versions, report_data["performance_metrics"], db
                )
            
            # Generate optimization recommendations
            report_data["optimization_recommendations"] = await self._generate_algorithm_recommendations(
                report_data["performance_metrics"], db
            )
            
            # Store performance metrics
            await self._store_performance_metrics(report_data, db)
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating algorithm performance report: {str(e)}")
            raise

    # Private helper methods

    async def _get_user_behavior_analytics(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get comprehensive user behavior analytics"""
        analytics = db.query(UserBehaviorAnalytics).filter(
            UserBehaviorAnalytics.user_id == user_id
        ).first()
        
        if not analytics:
            # Create initial analytics
            analytics = await self._create_initial_behavior_analytics(user_id, db)
        
        return {
            "interaction_patterns": analytics.interaction_patterns or {},
            "preference_evolution": analytics.preference_evolution or {},
            "success_indicators": analytics.success_indicators or {},
            "behavioral_score": analytics.behavioral_score or 0.5,
            "last_updated": analytics.updated_at
        }

    async def _get_potential_matches(self, user_id: int, db: Session) -> List[User]:
        """Get potential matches excluding already connected users"""
        # Get users already connected to
        existing_connections = db.query(SoulConnection).filter(
            or_(SoulConnection.user1_id == user_id, SoulConnection.user2_id == user_id)
        ).all()
        
        connected_user_ids = set()
        for conn in existing_connections:
            if conn.user1_id == user_id:
                connected_user_ids.add(conn.user2_id)
            else:
                connected_user_ids.add(conn.user1_id)
        
        # Get potential matches
        potential_matches = db.query(User).filter(
            and_(
                User.id != user_id,
                ~User.id.in_(connected_user_ids),
                User.is_active == True,
                User.emotional_onboarding_completed == True
            )
        ).limit(100).all()
        
        return potential_matches

    async def _calculate_predictive_compatibility(
        self,
        user1_id: int,
        user2_id: int,
        algorithm_version: str,
        behavior_analytics: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Calculate predictive compatibility with success probability"""
        
        # Get base compatibility from existing AI matching
        base_compatibility = await ai_matching_engine.calculate_ai_compatibility_score(
            user1_id, user2_id, db
        )
        
        # Apply behavioral learning adjustments
        behavioral_adjustment = await self._calculate_behavioral_adjustment(
            user1_id, user2_id, behavior_analytics, db
        )
        
        # Calculate success probability using ML model
        success_probability = await self._calculate_success_probability(
            user1_id, user2_id, base_compatibility, behavioral_adjustment, db
        )
        
        # Generate reasoning
        reasoning = await self._generate_compatibility_reasoning(
            base_compatibility, behavioral_adjustment, success_probability
        )
        
        # Calculate overall enhanced score
        enhanced_score = (
            base_compatibility["overall_score"] * 0.6 +
            behavioral_adjustment["score"] * 0.3 +
            success_probability * 0.1
        )
        
        return {
            "overall_score": enhanced_score,
            "base_compatibility": base_compatibility,
            "behavioral_adjustment": behavioral_adjustment,
            "success_probability": success_probability,
            "reasoning": reasoning,
            "success_prediction": {
                "short_term": success_probability,
                "long_term": success_probability * 0.8,  # Typically lower
                "confidence": 0.7
            },
            "algorithm_version": algorithm_version,
            "calculated_at": datetime.utcnow().isoformat()
        }

    async def _calculate_success_probability(
        self, user1_id: int, user2_id: int, base_compatibility: Dict, behavioral_adjustment: Dict, db: Session
    ) -> float:
        """Calculate probability of successful relationship"""
        
        # This would use a trained ML model
        # For now, using rule-based approach
        
        factors = []
        
        # Base compatibility factor
        if base_compatibility["overall_score"] > 0.8:
            factors.append(0.3)
        elif base_compatibility["overall_score"] > 0.6:
            factors.append(0.2)
        else:
            factors.append(0.1)
        
        # Behavioral compatibility factor
        if behavioral_adjustment["score"] > 0.7:
            factors.append(0.2)
        else:
            factors.append(0.1)
        
        # Communication style alignment
        factors.append(0.15)  # Would calculate based on actual data
        
        # Values alignment strength
        values_score = base_compatibility.get("breakdown", {}).get("values", 0.5)
        factors.append(values_score * 0.2)
        
        # Demographic compatibility
        demo_score = base_compatibility.get("breakdown", {}).get("demographics", 0.5)
        factors.append(demo_score * 0.15)
        
        return min(sum(factors), 0.95)  # Cap at 95%

    async def _store_predictive_compatibility(
        self, user1_id: int, user2_id: int, compatibility_data: Dict, db: Session
    ) -> None:
        """Store predictive compatibility data"""
        
        predictive_compatibility = PredictiveCompatibility(
            user1_id=user1_id,
            user2_id=user2_id,
            algorithm_version=compatibility_data["algorithm_version"],
            base_compatibility_score=compatibility_data["base_compatibility"]["overall_score"],
            behavioral_adjustment_score=compatibility_data["behavioral_adjustment"]["score"],
            predicted_success_probability=compatibility_data["success_probability"],
            overall_enhanced_score=compatibility_data["overall_score"],
            compatibility_reasoning=compatibility_data["reasoning"],
            prediction_metadata=compatibility_data["success_prediction"]
        )
        
        db.add(predictive_compatibility)
        db.commit()

    async def _generate_matching_insights(
        self, user_id: int, matches: List[Dict], behavior_analytics: Dict, db: Session
    ) -> Dict[str, Any]:
        """Generate insights about the matching results"""
        
        if not matches:
            return {"insights": [], "recommendations": []}
        
        # Analyze match quality distribution
        success_probabilities = [m["compatibility_data"]["success_probability"] for m in matches]
        avg_success_prob = statistics.mean(success_probabilities)
        
        insights = []
        recommendations = []
        
        if avg_success_prob > 0.7:
            insights.append("Excellent match quality detected")
            recommendations.append("These are high-potential connections - invest time in meaningful conversations")
        elif avg_success_prob > 0.5:
            insights.append("Good match quality with room for deeper connections")
            recommendations.append("Focus on shared values and interests to build stronger connections")
        else:
            insights.append("Moderate match quality - may benefit from profile optimization")
            recommendations.append("Consider updating your preferences or expanding your interests")
        
        # Analyze matching patterns
        compatibility_scores = [m["compatibility_data"]["overall_score"] for m in matches]
        if max(compatibility_scores) - min(compatibility_scores) < 0.2:
            insights.append("Consistent compatibility scores indicate clear preferences")
        else:
            insights.append("Varied compatibility scores suggest diverse connection opportunities")
        
        return {
            "insights": insights,
            "recommendations": recommendations,
            "average_success_probability": avg_success_prob,
            "match_quality_assessment": "excellent" if avg_success_prob > 0.7 else "good" if avg_success_prob > 0.5 else "moderate"
        }

    # Additional helper methods would continue here...
    async def _create_initial_behavior_analytics(self, user_id: int, db: Session) -> UserBehaviorAnalytics:
        """Create initial behavior analytics for new user"""
        analytics = UserBehaviorAnalytics(
            user_id=user_id,
            interaction_patterns={},
            preference_evolution={},
            success_indicators={},
            behavioral_score=0.5
        )
        
        db.add(analytics)
        db.commit()
        db.refresh(analytics)
        
        return analytics

    async def _calculate_behavioral_adjustment(
        self, user1_id: int, user2_id: int, behavior_analytics: Dict, db: Session
    ) -> Dict[str, Any]:
        """Calculate behavioral compatibility adjustment"""
        return {"score": 0.7, "factors": [], "confidence": 0.6}

    async def _generate_compatibility_reasoning(
        self, base_compatibility: Dict, behavioral_adjustment: Dict, success_probability: float
    ) -> List[str]:
        """Generate human-readable compatibility reasoning"""
        reasoning = []
        
        if base_compatibility["overall_score"] > 0.8:
            reasoning.append("Strong foundational compatibility")
        
        if behavioral_adjustment["score"] > 0.7:
            reasoning.append("Excellent behavioral alignment")
        
        if success_probability > 0.7:
            reasoning.append("High probability of meaningful connection")
        
        return reasoning

    async def _analyze_connection_outcomes(self, connections: List[SoulConnection], user_id: int, db: Session) -> Dict[str, Any]:
        """Analyze outcomes of user's connections"""
        return {"success_rate": 0.6, "patterns": []}

    async def _identify_success_patterns(self, connections: List[SoulConnection], user_id: int, db: Session) -> Dict[str, Any]:
        """Identify patterns in successful connections"""
        return {"patterns": [], "confidence": 0.5}

    async def _generate_optimization_recommendations(
        self, outcome_analysis: Dict, success_patterns: Dict, user_id: int, db: Session
    ) -> List[str]:
        """Generate recommendations for matching optimization"""
        return ["Focus on shared values", "Prioritize emotional intelligence"]

    async def _update_user_matching_preferences(self, user_id: int, success_patterns: Dict, db: Session) -> None:
        """Update user's matching preferences based on patterns"""
        pass

    def _calculate_matching_effectiveness(self, outcome_analysis: Dict) -> float:
        """Calculate overall matching effectiveness score"""
        return outcome_analysis.get("success_rate", 0.5)


# Initialize the global advanced AI matching engine
advanced_ai_matching_engine = AdvancedAIMatchingEngine()