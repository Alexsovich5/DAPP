# Predictive Analytics Service for Dinner1
# Machine learning models for user behavior prediction and optimization

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import logging
from clickhouse_driver import Client
import redis
import asyncio

logger = logging.getLogger(__name__)

class PredictionType(Enum):
    CHURN_RISK = "churn_risk"
    MATCH_SUCCESS = "match_success"
    CONVERSATION_LIKELIHOOD = "conversation_likelihood"
    PHOTO_REVEAL_TIMING = "photo_reveal_timing"
    SUBSCRIPTION_PROPENSITY = "subscription_propensity"
    ENGAGEMENT_SCORE = "engagement_score"

@dataclass
class UserFeatures:
    user_id: int
    days_since_registration: int
    profile_completeness: float
    total_matches: int
    total_conversations: int
    total_revelations_shared: int
    avg_response_time_hours: float
    login_frequency: float
    last_activity_days_ago: int
    age: int
    gender: str
    interests_count: int
    photo_count: int
    bio_length: int
    compatibility_scores_avg: float
    match_rate: float
    conversation_rate: float
    revelation_completion_rate: float

@dataclass
class PredictionResult:
    user_id: int
    prediction_type: PredictionType
    prediction_value: float
    confidence: float
    prediction_date: datetime
    model_version: str
    features_used: List[str]

class PredictiveAnalyticsService:
    """
    Machine learning service for predicting user behavior and optimizing dating platform
    """
    
    def __init__(self, clickhouse_client: Client, redis_client: redis.Redis):
        self.clickhouse = clickhouse_client
        self.redis = redis_client
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.model_versions = {}
        
        # Feature columns for different prediction types
        self.feature_columns = {
            PredictionType.CHURN_RISK: [
                'days_since_registration', 'last_activity_days_ago', 'login_frequency',
                'total_matches', 'total_conversations', 'match_rate', 'conversation_rate',
                'profile_completeness', 'avg_response_time_hours'
            ],
            PredictionType.MATCH_SUCCESS: [
                'compatibility_scores_avg', 'profile_completeness', 'photo_count',
                'bio_length', 'interests_count', 'age', 'gender_encoded'
            ],
            PredictionType.CONVERSATION_LIKELIHOOD: [
                'compatibility_scores_avg', 'match_rate', 'avg_response_time_hours',
                'profile_completeness', 'total_conversations', 'age'
            ],
            PredictionType.SUBSCRIPTION_PROPENSITY: [
                'days_since_registration', 'total_matches', 'total_conversations',
                'match_rate', 'conversation_rate', 'login_frequency', 'age'
            ]
        }
    
    async def initialize_models(self):
        """
        Initialize and load pre-trained models
        """
        try:
            logger.info("Initializing predictive analytics models...")
            
            # Load existing models or train new ones
            for prediction_type in PredictionType:
                await self._load_or_train_model(prediction_type)
            
            logger.info("Predictive analytics models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            raise
    
    async def predict_churn_risk(self, user_id: int) -> PredictionResult:
        """
        Predict the likelihood of user churn
        """
        try:
            features = await self._get_user_features(user_id)
            if not features:
                raise ValueError(f"Could not get features for user {user_id}")
            
            # Prepare features for churn model
            feature_vector = self._prepare_features(features, PredictionType.CHURN_RISK)
            
            # Make prediction
            model = self.models[PredictionType.CHURN_RISK]
            churn_probability = model.predict_proba(feature_vector.reshape(1, -1))[0][1]
            
            # Calculate confidence based on model's certainty
            confidence = max(churn_probability, 1 - churn_probability)
            
            result = PredictionResult(
                user_id=user_id,
                prediction_type=PredictionType.CHURN_RISK,
                prediction_value=churn_probability,
                confidence=confidence,
                prediction_date=datetime.utcnow(),
                model_version=self.model_versions[PredictionType.CHURN_RISK],
                features_used=self.feature_columns[PredictionType.CHURN_RISK]
            )
            
            # Store prediction for tracking
            await self._store_prediction(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to predict churn risk for user {user_id}: {e}")
            raise
    
    async def predict_match_success(self, user1_id: int, user2_id: int, 
                                  compatibility_score: float) -> PredictionResult:
        """
        Predict the likelihood of a successful match between two users
        """
        try:
            # Get features for both users
            user1_features = await self._get_user_features(user1_id)
            user2_features = await self._get_user_features(user2_id)
            
            if not user1_features or not user2_features:
                raise ValueError("Could not get features for one or both users")
            
            # Create combined features for match prediction
            combined_features = self._create_match_features(
                user1_features, user2_features, compatibility_score
            )
            
            # Make prediction
            model = self.models[PredictionType.MATCH_SUCCESS]
            success_probability = model.predict_proba(combined_features.reshape(1, -1))[0][1]
            
            confidence = max(success_probability, 1 - success_probability)
            
            result = PredictionResult(
                user_id=user1_id,  # Primary user for this prediction
                prediction_type=PredictionType.MATCH_SUCCESS,
                prediction_value=success_probability,
                confidence=confidence,
                prediction_date=datetime.utcnow(),
                model_version=self.model_versions[PredictionType.MATCH_SUCCESS],
                features_used=self.feature_columns[PredictionType.MATCH_SUCCESS]
            )
            
            await self._store_prediction(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to predict match success for users {user1_id}, {user2_id}: {e}")
            raise
    
    async def predict_conversation_likelihood(self, user1_id: int, user2_id: int) -> PredictionResult:
        """
        Predict the likelihood that a match will lead to conversation
        """
        try:
            user1_features = await self._get_user_features(user1_id)
            user2_features = await self._get_user_features(user2_id)
            
            # Create features for conversation prediction
            conv_features = self._create_conversation_features(user1_features, user2_features)
            
            model = self.models[PredictionType.CONVERSATION_LIKELIHOOD]
            conversation_probability = model.predict_proba(conv_features.reshape(1, -1))[0][1]
            
            confidence = max(conversation_probability, 1 - conversation_probability)
            
            result = PredictionResult(
                user_id=user1_id,
                prediction_type=PredictionType.CONVERSATION_LIKELIHOOD,
                prediction_value=conversation_probability,
                confidence=confidence,
                prediction_date=datetime.utcnow(),
                model_version=self.model_versions[PredictionType.CONVERSATION_LIKELIHOOD],
                features_used=self.feature_columns[PredictionType.CONVERSATION_LIKELIHOOD]
            )
            
            await self._store_prediction(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to predict conversation likelihood: {e}")
            raise
    
    async def predict_subscription_propensity(self, user_id: int) -> PredictionResult:
        """
        Predict the likelihood that a user will subscribe to premium features
        """
        try:
            features = await self._get_user_features(user_id)
            feature_vector = self._prepare_features(features, PredictionType.SUBSCRIPTION_PROPENSITY)
            
            model = self.models[PredictionType.SUBSCRIPTION_PROPENSITY]
            subscription_probability = model.predict_proba(feature_vector.reshape(1, -1))[0][1]
            
            confidence = max(subscription_probability, 1 - subscription_probability)
            
            result = PredictionResult(
                user_id=user_id,
                prediction_type=PredictionType.SUBSCRIPTION_PROPENSITY,
                prediction_value=subscription_probability,
                confidence=confidence,
                prediction_date=datetime.utcnow(),
                model_version=self.model_versions[PredictionType.SUBSCRIPTION_PROPENSITY],
                features_used=self.feature_columns[PredictionType.SUBSCRIPTION_PROPENSITY]
            )
            
            await self._store_prediction(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to predict subscription propensity for user {user_id}: {e}")
            raise
    
    async def get_user_engagement_score(self, user_id: int) -> float:
        """
        Calculate comprehensive user engagement score
        """
        try:
            features = await self._get_user_features(user_id)
            if not features:
                return 0.0
            
            # Calculate weighted engagement score
            engagement_score = (
                min(features.login_frequency * 10, 30) +  # Login frequency (max 30 points)
                min(features.match_rate * 100, 25) +      # Match rate (max 25 points)
                min(features.conversation_rate * 100, 25) + # Conversation rate (max 25 points)
                min(features.profile_completeness * 20, 20) # Profile completeness (max 20 points)
            )
            
            # Penalty for inactivity
            if features.last_activity_days_ago > 7:
                engagement_score *= 0.5
            elif features.last_activity_days_ago > 3:
                engagement_score *= 0.8
            
            return min(engagement_score, 100.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate engagement score for user {user_id}: {e}")
            return 0.0
    
    async def identify_at_risk_users(self, threshold: float = 0.7) -> List[int]:
        """
        Identify users at high risk of churning
        """
        try:
            # Get active users from last 30 days
            active_users = await self._get_active_users(days=30)
            
            at_risk_users = []
            
            for user_id in active_users:
                churn_prediction = await self.predict_churn_risk(user_id)
                
                if churn_prediction.prediction_value >= threshold:
                    at_risk_users.append(user_id)
            
            # Cache results for quick access
            await self._cache_at_risk_users(at_risk_users)
            
            return at_risk_users
            
        except Exception as e:
            logger.error(f"Failed to identify at-risk users: {e}")
            return []
    
    async def generate_user_recommendations(self, user_id: int) -> Dict[str, Any]:
        """
        Generate personalized recommendations for improving user experience
        """
        try:
            features = await self._get_user_features(user_id)
            churn_risk = await self.predict_churn_risk(user_id)
            engagement_score = await self.get_user_engagement_score(user_id)
            
            recommendations = {
                "user_id": user_id,
                "engagement_score": engagement_score,
                "churn_risk": churn_risk.prediction_value,
                "recommendations": []
            }
            
            # Generate specific recommendations based on user data
            if features.profile_completeness < 0.8:
                recommendations["recommendations"].append({
                    "type": "profile_completion",
                    "priority": "high",
                    "message": "Complete your profile to get better matches",
                    "action": "complete_profile"
                })
            
            if features.photo_count < 3:
                recommendations["recommendations"].append({
                    "type": "add_photos",
                    "priority": "medium",
                    "message": "Add more photos to increase your visibility",
                    "action": "upload_photos"
                })
            
            if features.last_activity_days_ago > 7:
                recommendations["recommendations"].append({
                    "type": "re_engagement",
                    "priority": "high",
                    "message": "Check out new potential matches",
                    "action": "browse_profiles"
                })
            
            if features.conversation_rate < 0.3 and features.total_matches > 5:
                recommendations["recommendations"].append({
                    "type": "conversation_tips",
                    "priority": "medium",
                    "message": "Improve your conversation starter game",
                    "action": "view_tips"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations for user {user_id}: {e}")
            return {}
    
    async def _get_user_features(self, user_id: int) -> Optional[UserFeatures]:
        """
        Extract features for a user from analytics data
        """
        try:
            # Query user data from ClickHouse
            user_query = """
            SELECT 
                u.id as user_id,
                dateDiff('day', u.created_at, now()) as days_since_registration,
                -- Calculate profile completeness based on filled fields
                (
                    (CASE WHEN u.first_name != '' THEN 1 ELSE 0 END) +
                    (CASE WHEN u.last_name != '' THEN 1 ELSE 0 END) +
                    (CASE WHEN u.date_of_birth IS NOT NULL THEN 1 ELSE 0 END) +
                    (CASE WHEN p.bio != '' THEN 1 ELSE 0 END) +
                    (CASE WHEN length(p.interests) > 0 THEN 1 ELSE 0 END)
                ) / 5.0 as profile_completeness,
                dateDiff('day', u.last_activity, now()) as last_activity_days_ago,
                u.age,
                u.gender,
                length(p.interests) as interests_count,
                -- These would need to be calculated from related tables
                0 as total_matches,
                0 as total_conversations,
                0 as total_revelations_shared,
                0 as avg_response_time_hours,
                0 as login_frequency,
                0 as photo_count,
                length(p.bio) as bio_length,
                0 as compatibility_scores_avg,
                0 as match_rate,
                0 as conversation_rate,
                0 as revelation_completion_rate
            FROM users u
            LEFT JOIN emotional_profiles p ON u.id = p.user_id
            WHERE u.id = %(user_id)s
            """
            
            # For now, return mock data since the full schema isn't implemented
            return UserFeatures(
                user_id=user_id,
                days_since_registration=30,
                profile_completeness=0.8,
                total_matches=15,
                total_conversations=8,
                total_revelations_shared=12,
                avg_response_time_hours=2.5,
                login_frequency=0.7,
                last_activity_days_ago=1,
                age=28,
                gender="female",
                interests_count=8,
                photo_count=4,
                bio_length=150,
                compatibility_scores_avg=0.75,
                match_rate=0.6,
                conversation_rate=0.4,
                revelation_completion_rate=0.8
            )
            
        except Exception as e:
            logger.error(f"Failed to get user features for {user_id}: {e}")
            return None
    
    async def _load_or_train_model(self, prediction_type: PredictionType):
        """
        Load existing model or train a new one
        """
        try:
            model_path = f"models/{prediction_type.value}_model.joblib"
            scaler_path = f"models/{prediction_type.value}_scaler.joblib"
            
            try:
                # Try to load existing model
                self.models[prediction_type] = joblib.load(model_path)
                self.scalers[prediction_type] = joblib.load(scaler_path)
                self.model_versions[prediction_type] = "v1.0"
                logger.info(f"Loaded existing model for {prediction_type.value}")
            except FileNotFoundError:
                # Train new model
                logger.info(f"Training new model for {prediction_type.value}")
                await self._train_model(prediction_type)
                
        except Exception as e:
            logger.error(f"Failed to load/train model for {prediction_type.value}: {e}")
            # Create dummy model for development
            self._create_dummy_model(prediction_type)
    
    async def _train_model(self, prediction_type: PredictionType):
        """
        Train a machine learning model for the given prediction type
        """
        try:
            # Get training data
            training_data = await self._get_training_data(prediction_type)
            
            if training_data.empty:
                logger.warning(f"No training data available for {prediction_type.value}")
                self._create_dummy_model(prediction_type)
                return
            
            # Prepare features and target
            feature_cols = self.feature_columns[prediction_type]
            X = training_data[feature_cols]
            y = training_data['target']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model based on prediction type
            if prediction_type in [PredictionType.CHURN_RISK, PredictionType.MATCH_SUCCESS]:
                # Classification models
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                # Regression models
                model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            predictions = model.predict(X_test_scaled)
            
            if prediction_type in [PredictionType.CHURN_RISK, PredictionType.MATCH_SUCCESS]:
                accuracy = accuracy_score(y_test, predictions)
                logger.info(f"{prediction_type.value} model accuracy: {accuracy:.3f}")
            
            # Save model and scaler
            self.models[prediction_type] = model
            self.scalers[prediction_type] = scaler
            self.model_versions[prediction_type] = f"v{datetime.now().strftime('%Y%m%d')}"
            
            # Save to disk
            joblib.dump(model, f"models/{prediction_type.value}_model.joblib")
            joblib.dump(scaler, f"models/{prediction_type.value}_scaler.joblib")
            
            logger.info(f"Trained and saved model for {prediction_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to train model for {prediction_type.value}: {e}")
            self._create_dummy_model(prediction_type)
    
    def _create_dummy_model(self, prediction_type: PredictionType):
        """
        Create a dummy model for development/testing
        """
        # Create simple dummy models that return random predictions
        if prediction_type in [PredictionType.CHURN_RISK, PredictionType.MATCH_SUCCESS]:
            self.models[prediction_type] = type('DummyClassifier', (), {
                'predict_proba': lambda self, X: np.random.rand(len(X), 2)
            })()
        else:
            self.models[prediction_type] = type('DummyRegressor', (), {
                'predict': lambda self, X: np.random.rand(len(X))
            })()
        
        self.scalers[prediction_type] = StandardScaler()
        self.model_versions[prediction_type] = "dummy_v1.0"
        
        logger.warning(f"Created dummy model for {prediction_type.value}")
    
    def _prepare_features(self, features: UserFeatures, prediction_type: PredictionType) -> np.ndarray:
        """
        Prepare feature vector for model prediction
        """
        feature_cols = self.feature_columns[prediction_type]
        feature_vector = []
        
        for col in feature_cols:
            if col == 'gender_encoded':
                # Encode gender (0 for male, 1 for female, 0.5 for other)
                gender_map = {'male': 0, 'female': 1, 'other': 0.5}
                feature_vector.append(gender_map.get(features.gender, 0.5))
            else:
                # Get attribute value
                attr_name = col
                feature_vector.append(getattr(features, attr_name, 0))
        
        feature_array = np.array(feature_vector)
        
        # Scale features if scaler exists
        if prediction_type in self.scalers:
            feature_array = self.scalers[prediction_type].transform(feature_array.reshape(1, -1))[0]
        
        return feature_array
    
    def _create_match_features(self, user1_features: UserFeatures, 
                              user2_features: UserFeatures, 
                              compatibility_score: float) -> np.ndarray:
        """
        Create combined features for match success prediction
        """
        # Combine features from both users
        combined_features = [
            compatibility_score,
            (user1_features.profile_completeness + user2_features.profile_completeness) / 2,
            (user1_features.photo_count + user2_features.photo_count) / 2,
            (user1_features.bio_length + user2_features.bio_length) / 2,
            (user1_features.interests_count + user2_features.interests_count) / 2,
            abs(user1_features.age - user2_features.age),  # Age difference
            1 if user1_features.gender != user2_features.gender else 0  # Different genders
        ]
        
        return np.array(combined_features)
    
    def _create_conversation_features(self, user1_features: UserFeatures,
                                    user2_features: UserFeatures) -> np.ndarray:
        """
        Create features for conversation likelihood prediction
        """
        conv_features = [
            (user1_features.compatibility_scores_avg + user2_features.compatibility_scores_avg) / 2,
            (user1_features.match_rate + user2_features.match_rate) / 2,
            (user1_features.avg_response_time_hours + user2_features.avg_response_time_hours) / 2,
            (user1_features.profile_completeness + user2_features.profile_completeness) / 2,
            (user1_features.total_conversations + user2_features.total_conversations) / 2,
            (user1_features.age + user2_features.age) / 2
        ]
        
        return np.array(conv_features)
    
    async def _get_training_data(self, prediction_type: PredictionType) -> pd.DataFrame:
        """
        Get historical data for model training
        """
        # This would query historical data from ClickHouse
        # For now, return empty DataFrame
        return pd.DataFrame()
    
    async def _get_active_users(self, days: int = 30) -> List[int]:
        """
        Get list of active users in the last N days
        """
        try:
            # This would query ClickHouse for active users
            # For now, return mock data
            return list(range(1, 101))  # Mock 100 users
            
        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            return []
    
    async def _store_prediction(self, prediction: PredictionResult):
        """
        Store prediction result for tracking and evaluation
        """
        try:
            # Store in Redis for quick access
            prediction_key = f"prediction:{prediction.user_id}:{prediction.prediction_type.value}"
            prediction_data = {
                'value': prediction.prediction_value,
                'confidence': prediction.confidence,
                'timestamp': prediction.prediction_date.isoformat(),
                'model_version': prediction.model_version
            }
            
            self.redis.set(prediction_key, str(prediction_data), ex=86400 * 7)  # 7 days
            
            # Store in ClickHouse for analysis (would need table creation)
            # self.clickhouse.execute("INSERT INTO predictions VALUES", [prediction_data])
            
        except Exception as e:
            logger.error(f"Failed to store prediction: {e}")
    
    async def _cache_at_risk_users(self, user_ids: List[int]):
        """
        Cache list of at-risk users for quick access
        """
        try:
            self.redis.set(
                "at_risk_users",
                ",".join(map(str, user_ids)),
                ex=3600 * 6  # 6 hours
            )
        except Exception as e:
            logger.error(f"Failed to cache at-risk users: {e}")
    
    async def retrain_models(self):
        """
        Retrain all models with fresh data
        """
        try:
            logger.info("Starting model retraining...")
            
            for prediction_type in PredictionType:
                await self._train_model(prediction_type)
            
            logger.info("Model retraining completed")
            
        except Exception as e:
            logger.error(f"Failed to retrain models: {e}")
            raise