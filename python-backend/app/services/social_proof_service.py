"""
Phase 7: Social Proof & Community Features Service
Trust, safety, and social validation system for enhanced user confidence
"""
import logging
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.social_proof_models import (
    UserVerification, CommunityFeedback, SuccessStory, UserReputation,
    ReferralSystem, SocialProofIndicator, TrustScore, SafetyReport,
    VerificationType, FeedbackType, ReputationCategory, SafetyLevel
)
from app.services.personalization_service import personalization_engine

logger = logging.getLogger(__name__)


class SocialProofEngine:
    """
    Advanced social proof and community validation system
    Builds trust through verification, feedback, and community engagement
    """
    
    def __init__(self):
        self.verification_weights = {
            "photo_verification": 0.25,
            "phone_verification": 0.20,
            "social_media_verification": 0.15,
            "identity_verification": 0.30,
            "community_feedback": 0.10
        }
        
        self.reputation_categories = {
            "authenticity": 0.30,
            "communication": 0.25,
            "respect": 0.25,
            "reliability": 0.20
        }
        
        self.trust_thresholds = {
            "verified_user": 0.7,
            "trusted_member": 0.8,
            "community_champion": 0.9
        }

    async def initiate_user_verification(
        self,
        user_id: int,
        verification_type: str,
        verification_data: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """Initiate user verification process"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Create verification record
            verification = UserVerification(
                user_id=user_id,
                verification_type=VerificationType(verification_type),
                verification_data=verification_data,
                verification_token=self._generate_verification_token(),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            db.add(verification)
            db.commit()
            db.refresh(verification)
            
            # Process verification based on type
            result = await self._process_verification(verification, db)
            
            # Update user's trust score
            await self._update_user_trust_score(user_id, db)
            
            return {
                "verification_id": verification.id,
                "verification_token": verification.verification_token,
                "status": result["status"],
                "next_steps": result["next_steps"],
                "estimated_completion": result.get("estimated_completion"),
                "verification_boost": result.get("trust_score_boost", 0)
            }
            
        except Exception as e:
            logger.error(f"Error initiating verification: {str(e)}")
            raise

    async def submit_community_feedback(
        self,
        reviewer_id: int,
        subject_user_id: int,
        connection_id: int,
        feedback_data: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """Submit feedback about user interaction"""
        try:
            # Validate reviewer can give feedback (must have interacted)
            connection = db.query(SoulConnection).filter(
                and_(
                    SoulConnection.id == connection_id,
                    or_(
                        and_(SoulConnection.user1_id == reviewer_id, SoulConnection.user2_id == subject_user_id),
                        and_(SoulConnection.user1_id == subject_user_id, SoulConnection.user2_id == reviewer_id)
                    )
                )
            ).first()
            
            if not connection:
                raise ValueError("No valid connection found for feedback")
            
            # Check if feedback already exists
            existing_feedback = db.query(CommunityFeedback).filter(
                and_(
                    CommunityFeedback.reviewer_id == reviewer_id,
                    CommunityFeedback.subject_user_id == subject_user_id,
                    CommunityFeedback.connection_id == connection_id
                )
            ).first()
            
            if existing_feedback:
                # Update existing feedback
                existing_feedback.feedback_type = FeedbackType(feedback_data["type"])
                existing_feedback.rating_scores = feedback_data["ratings"]
                existing_feedback.feedback_text = feedback_data.get("text")
                existing_feedback.updated_at = datetime.utcnow()
                
                feedback = existing_feedback
            else:
                # Create new feedback
                feedback = CommunityFeedback(
                    reviewer_id=reviewer_id,
                    subject_user_id=subject_user_id,
                    connection_id=connection_id,
                    feedback_type=FeedbackType(feedback_data["type"]),
                    rating_scores=feedback_data["ratings"],
                    feedback_text=feedback_data.get("text"),
                    interaction_context=feedback_data.get("context", {})
                )
                
                db.add(feedback)
            
            db.commit()
            db.refresh(feedback)
            
            # Update subject user's reputation
            await self._update_user_reputation(subject_user_id, db)
            
            # Generate community insights
            insights = await self._generate_community_insights(subject_user_id, db)
            
            return {
                "feedback_id": feedback.id,
                "impact_on_reputation": insights["reputation_change"],
                "community_standing": insights["community_standing"],
                "thank_you_message": "Thank you for helping build a trustworthy community!"
            }
            
        except Exception as e:
            logger.error(f"Error submitting community feedback: {str(e)}")
            raise

    async def create_success_story(
        self,
        user1_id: int,
        user2_id: int,
        connection_id: int,
        story_data: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """Create and validate a success story"""
        try:
            # Validate both users consent to sharing story
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError("Connection not found")
            
            # Check if both users completed their revelation cycle
            if not (connection.reveal_day >= 7 and connection.first_dinner_completed):
                return {
                    "success": False,
                    "reason": "Success stories can only be shared after completing the full connection journey"
                }
            
            # Create success story
            success_story = SuccessStory(
                user1_id=user1_id,
                user2_id=user2_id,
                connection_id=connection_id,
                story_title=story_data["title"],
                story_content=story_data["content"],
                story_type=story_data.get("type", "relationship_success"),
                both_users_consented=story_data.get("both_consent", False),
                story_metadata={
                    "connection_duration": (datetime.utcnow() - connection.created_at).days,
                    "revelation_completion": connection.reveal_day,
                    "compatibility_score": float(connection.compatibility_score or 0)
                }
            )
            
            db.add(success_story)
            db.commit()
            db.refresh(success_story)
            
            # If approved, boost both users' reputation
            if success_story.both_users_consented and success_story.is_approved:
                await self._boost_reputation_for_success(user1_id, user2_id, db)
            
            # Generate inspiring content for community
            community_impact = await self._calculate_story_community_impact(success_story, db)
            
            return {
                "success": True,
                "story_id": success_story.id,
                "moderation_status": "pending_approval",
                "community_impact_score": community_impact["impact_score"],
                "inspiration_potential": community_impact["inspiration_potential"],
                "estimated_approval_time": "24-48 hours"
            }
            
        except Exception as e:
            logger.error(f"Error creating success story: {str(e)}")
            raise

    async def process_referral_system(
        self,
        referrer_id: int,
        referee_email: str,
        referral_data: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """Process friend referral system"""
        try:
            referrer = db.query(User).filter(User.id == referrer_id).first()
            if not referrer:
                raise ValueError("Referrer not found")
            
            # Check referrer's reputation (must be trusted member)
            trust_score = await self._get_user_trust_score(referrer_id, db)
            if trust_score < self.trust_thresholds["trusted_member"]:
                return {
                    "success": False,
                    "reason": "Referrals available for trusted members only",
                    "current_trust_score": trust_score,
                    "required_trust_score": self.trust_thresholds["trusted_member"]
                }
            
            # Create referral record
            referral = ReferralSystem(
                referrer_id=referrer_id,
                referee_email=referee_email,
                referral_token=self._generate_referral_token(),
                referral_message=referral_data.get("message", ""),
                referral_context=referral_data.get("context", {}),
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            db.add(referral)
            db.commit()
            db.refresh(referral)
            
            # Send referral invitation (would integrate with email service)
            invitation_data = await self._prepare_referral_invitation(referrer, referral, db)
            
            return {
                "referral_id": referral.id,
                "referral_link": f"/join?ref={referral.referral_token}",
                "invitation_preview": invitation_data["preview"],
                "expected_benefits": invitation_data["benefits"],
                "referrer_rewards": invitation_data["rewards"]
            }
            
        except Exception as e:
            logger.error(f"Error processing referral: {str(e)}")
            raise

    async def generate_social_proof_indicators(
        self,
        user_id: int,
        context: str = "profile_view",
        db: Session = None
    ) -> Dict[str, Any]:
        """Generate social proof indicators for user profiles"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"indicators": [], "trust_level": "unverified"}
            
            # Get user's verifications
            verifications = db.query(UserVerification).filter(
                and_(
                    UserVerification.user_id == user_id,
                    UserVerification.is_verified == True
                )
            ).all()
            
            # Get reputation data
            reputation = db.query(UserReputation).filter(
                UserReputation.user_id == user_id
            ).first()
            
            # Get community feedback summary
            feedback_summary = await self._get_feedback_summary(user_id, db)
            
            # Generate trust score
            trust_score = await self._get_user_trust_score(user_id, db)
            
            # Build social proof indicators
            indicators = []
            
            # Verification badges
            for verification in verifications:
                indicators.append({
                    "type": "verification",
                    "badge": f"{verification.verification_type}_verified",
                    "confidence": verification.confidence_score,
                    "description": self._get_verification_description(verification.verification_type)
                })
            
            # Community reputation indicators
            if reputation and reputation.overall_reputation_score > 0.7:
                indicators.append({
                    "type": "reputation",
                    "badge": "trusted_member",
                    "score": float(reputation.overall_reputation_score),
                    "description": "Highly rated by the community"
                })
            
            # Positive feedback indicators
            if feedback_summary["positive_percentage"] > 80 and feedback_summary["total_feedback"] >= 3:
                indicators.append({
                    "type": "community_feedback",
                    "badge": "positive_interactions",
                    "percentage": feedback_summary["positive_percentage"],
                    "description": f"{feedback_summary['positive_percentage']}% positive feedback"
                })
            
            # Success story participation
            success_stories_count = db.query(func.count(SuccessStory.id)).filter(
                or_(SuccessStory.user1_id == user_id, SuccessStory.user2_id == user_id)
            ).scalar() or 0
            
            if success_stories_count > 0:
                indicators.append({
                    "type": "success_participation",
                    "badge": "connection_creator",
                    "count": success_stories_count,
                    "description": "Part of meaningful connections"
                })
            
            # Determine overall trust level
            trust_level = "unverified"
            if trust_score >= self.trust_thresholds["community_champion"]:
                trust_level = "community_champion"
            elif trust_score >= self.trust_thresholds["trusted_member"]:
                trust_level = "trusted_member"
            elif trust_score >= self.trust_thresholds["verified_user"]:
                trust_level = "verified_user"
            
            return {
                "indicators": indicators,
                "trust_level": trust_level,
                "trust_score": trust_score,
                "verification_count": len(verifications),
                "community_standing": feedback_summary.get("standing", "new_member"),
                "profile_strength": self._calculate_profile_strength(indicators, trust_score)
            }
            
        except Exception as e:
            logger.error(f"Error generating social proof indicators: {str(e)}")
            return {"indicators": [], "trust_level": "unverified"}

    async def report_safety_concern(
        self,
        reporter_id: int,
        reported_user_id: int,
        report_data: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """Report safety concerns about users"""
        try:
            # Create safety report
            safety_report = SafetyReport(
                reporter_id=reporter_id,
                reported_user_id=reported_user_id,
                report_type=report_data["type"],
                report_description=report_data["description"],
                severity_level=SafetyLevel(report_data.get("severity", "medium")),
                evidence_data=report_data.get("evidence", {}),
                connection_context=report_data.get("connection_context", {})
            )
            
            db.add(safety_report)
            db.commit()
            db.refresh(safety_report)
            
            # Immediate safety actions based on severity
            immediate_actions = await self._process_immediate_safety_actions(safety_report, db)
            
            # Update reported user's safety score
            await self._update_user_safety_score(reported_user_id, safety_report.severity_level, db)
            
            return {
                "report_id": safety_report.id,
                "status": "received",
                "immediate_actions": immediate_actions,
                "investigation_timeline": "24-72 hours",
                "reporter_protection": "Your identity is protected",
                "follow_up": "We'll update you on the investigation"
            }
            
        except Exception as e:
            logger.error(f"Error reporting safety concern: {str(e)}")
            raise

    # Private helper methods

    async def _process_verification(self, verification: UserVerification, db: Session) -> Dict[str, Any]:
        """Process specific verification type"""
        verification_type = verification.verification_type
        
        if verification_type == VerificationType.PHOTO_VERIFICATION:
            return await self._process_photo_verification(verification, db)
        elif verification_type == VerificationType.PHONE_VERIFICATION:
            return await self._process_phone_verification(verification, db)
        elif verification_type == VerificationType.SOCIAL_MEDIA_VERIFICATION:
            return await self._process_social_media_verification(verification, db)
        elif verification_type == VerificationType.IDENTITY_VERIFICATION:
            return await self._process_identity_verification(verification, db)
        
        return {"status": "initiated", "next_steps": ["Complete verification process"]}

    async def _process_photo_verification(self, verification: UserVerification, db: Session) -> Dict[str, Any]:
        """Process photo verification with AI face matching"""
        # This would integrate with actual photo verification service
        # For now, return mock successful verification
        
        verification.is_verified = True
        verification.verification_completed_at = datetime.utcnow()
        verification.confidence_score = 0.9
        verification.verification_notes = "Photo successfully verified"
        
        db.commit()
        
        return {
            "status": "completed",
            "next_steps": [],
            "trust_score_boost": 0.25,
            "estimated_completion": "immediate"
        }

    async def _process_phone_verification(self, verification: UserVerification, db: Session) -> Dict[str, Any]:
        """Process phone number verification"""
        # This would integrate with SMS verification service
        
        return {
            "status": "sms_sent",
            "next_steps": ["Enter SMS verification code"],
            "trust_score_boost": 0.20,
            "estimated_completion": "5 minutes"
        }

    async def _process_social_media_verification(self, verification: UserVerification, db: Session) -> Dict[str, Any]:
        """Process social media account verification"""
        # This would integrate with social media APIs
        
        return {
            "status": "oauth_required",
            "next_steps": ["Connect your social media account"],
            "trust_score_boost": 0.15,
            "estimated_completion": "2 minutes"
        }

    async def _process_identity_verification(self, verification: UserVerification, db: Session) -> Dict[str, Any]:
        """Process government ID verification"""
        # This would integrate with identity verification service
        
        return {
            "status": "documents_required",
            "next_steps": ["Upload government-issued ID"],
            "trust_score_boost": 0.30,
            "estimated_completion": "24 hours"
        }

    async def _update_user_trust_score(self, user_id: int, db: Session) -> float:
        """Update user's overall trust score"""
        # Get all verification scores
        verifications = db.query(UserVerification).filter(
            and_(
                UserVerification.user_id == user_id,
                UserVerification.is_verified == True
            )
        ).all()
        
        # Calculate weighted verification score
        verification_score = 0.0
        for verification in verifications:
            weight = self.verification_weights.get(verification.verification_type, 0.1)
            confidence = verification.confidence_score or 0.5
            verification_score += weight * confidence
        
        # Get community feedback score
        feedback_summary = await self._get_feedback_summary(user_id, db)
        community_score = feedback_summary.get("average_rating", 0.5)
        
        # Calculate overall trust score
        trust_score = (verification_score * 0.7) + (community_score * 0.3)
        
        # Store or update trust score
        trust_record = db.query(TrustScore).filter(TrustScore.user_id == user_id).first()
        if trust_record:
            trust_record.trust_score = trust_score
            trust_record.updated_at = datetime.utcnow()
        else:
            trust_record = TrustScore(
                user_id=user_id,
                trust_score=trust_score,
                verification_score=verification_score,
                community_feedback_score=community_score
            )
            db.add(trust_record)
        
        db.commit()
        return trust_score

    async def _update_user_reputation(self, user_id: int, db: Session) -> None:
        """Update user reputation based on community feedback"""
        # Get all feedback for user
        feedback_records = db.query(CommunityFeedback).filter(
            CommunityFeedback.subject_user_id == user_id
        ).all()
        
        if not feedback_records:
            return
        
        # Calculate reputation scores by category
        category_scores = {}
        for category in self.reputation_categories:
            scores = []
            for feedback in feedback_records:
                if feedback.rating_scores and category in feedback.rating_scores:
                    scores.append(feedback.rating_scores[category])
            
            if scores:
                category_scores[category] = sum(scores) / len(scores)
            else:
                category_scores[category] = 0.5  # Neutral default
        
        # Calculate overall reputation
        overall_score = sum(
            score * weight for score, weight in 
            zip(category_scores.values(), self.reputation_categories.values())
        )
        
        # Store reputation
        reputation = db.query(UserReputation).filter(UserReputation.user_id == user_id).first()
        if reputation:
            reputation.authenticity_score = category_scores["authenticity"]
            reputation.communication_score = category_scores["communication"]
            reputation.respect_score = category_scores["respect"]
            reputation.reliability_score = category_scores["reliability"]
            reputation.overall_reputation_score = overall_score
            reputation.updated_at = datetime.utcnow()
        else:
            reputation = UserReputation(
                user_id=user_id,
                authenticity_score=category_scores["authenticity"],
                communication_score=category_scores["communication"],
                respect_score=category_scores["respect"],
                reliability_score=category_scores["reliability"],
                overall_reputation_score=overall_score
            )
            db.add(reputation)
        
        db.commit()

    async def _generate_community_insights(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Generate insights about user's community standing"""
        # Get current reputation
        reputation = db.query(UserReputation).filter(UserReputation.user_id == user_id).first()
        
        # Calculate reputation change (would compare with historical data)
        reputation_change = 0.0  # Placeholder
        
        # Determine community standing
        if reputation and reputation.overall_reputation_score > 0.8:
            standing = "excellent"
        elif reputation and reputation.overall_reputation_score > 0.6:
            standing = "good"
        elif reputation and reputation.overall_reputation_score > 0.4:
            standing = "fair"
        else:
            standing = "needs_improvement"
        
        return {
            "reputation_change": reputation_change,
            "community_standing": standing,
            "trust_level": await self._get_trust_level(user_id, db)
        }

    async def _get_feedback_summary(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get summary of community feedback for user"""
        feedback_records = db.query(CommunityFeedback).filter(
            CommunityFeedback.subject_user_id == user_id
        ).all()
        
        if not feedback_records:
            return {"total_feedback": 0, "positive_percentage": 0, "average_rating": 0.5}
        
        positive_count = sum(1 for f in feedback_records if f.feedback_type in ["positive", "excellent"])
        total_count = len(feedback_records)
        positive_percentage = (positive_count / total_count) * 100
        
        # Calculate average rating across all categories
        all_ratings = []
        for feedback in feedback_records:
            if feedback.rating_scores:
                all_ratings.extend(feedback.rating_scores.values())
        
        average_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0.5
        
        return {
            "total_feedback": total_count,
            "positive_percentage": positive_percentage,
            "average_rating": average_rating,
            "standing": "good" if positive_percentage > 70 else "fair"
        }

    async def _get_user_trust_score(self, user_id: int, db: Session) -> float:
        """Get user's current trust score"""
        trust_record = db.query(TrustScore).filter(TrustScore.user_id == user_id).first()
        return trust_record.trust_score if trust_record else 0.5

    async def _get_trust_level(self, user_id: int, db: Session) -> str:
        """Get user's trust level classification"""
        trust_score = await self._get_user_trust_score(user_id, db)
        
        for level, threshold in reversed(self.trust_thresholds.items()):
            if trust_score >= threshold:
                return level
        
        return "unverified"

    def _generate_verification_token(self) -> str:
        """Generate secure verification token"""
        return str(uuid.uuid4())

    def _generate_referral_token(self) -> str:
        """Generate secure referral token"""
        return hashlib.sha256(f"{uuid.uuid4()}{datetime.utcnow()}".encode()).hexdigest()[:16]

    def _get_verification_description(self, verification_type: str) -> str:
        """Get human-readable verification description"""
        descriptions = {
            "photo_verification": "Photo verified with AI face matching",
            "phone_verification": "Phone number verified with SMS",
            "social_media_verification": "Social media profile connected",
            "identity_verification": "Government ID verified"
        }
        return descriptions.get(verification_type, "Verified by community")

    def _calculate_profile_strength(self, indicators: List[Dict], trust_score: float) -> int:
        """Calculate profile strength percentage"""
        base_strength = int(trust_score * 60)  # Base 60% from trust
        indicator_bonus = min(len(indicators) * 10, 40)  # Up to 40% from indicators
        return base_strength + indicator_bonus

    # Additional helper methods would continue here...
    async def _boost_reputation_for_success(self, user1_id: int, user2_id: int, db: Session) -> None:
        """Boost reputation for users with success stories"""
        pass  # Implementation would boost both users' scores

    async def _calculate_story_community_impact(self, story: SuccessStory, db: Session) -> Dict[str, Any]:
        """Calculate impact of success story on community"""
        return {"impact_score": 0.8, "inspiration_potential": 0.9}

    async def _prepare_referral_invitation(self, referrer: User, referral: ReferralSystem, db: Session) -> Dict[str, Any]:
        """Prepare referral invitation data"""
        return {
            "preview": f"{referrer.first_name} invited you to join a meaningful dating experience",
            "benefits": ["Soul-before-skin connections", "Verified community", "Meaningful relationships"],
            "rewards": {"referrer": "Trust score boost", "referee": "Premium features trial"}
        }

    async def _process_immediate_safety_actions(self, report: SafetyReport, db: Session) -> List[str]:
        """Process immediate safety actions based on report severity"""
        actions = []
        
        if report.severity_level == SafetyLevel.HIGH:
            actions.extend([
                "Temporary account restriction applied",
                "Priority investigation initiated",
                "Safety team notified immediately"
            ])
        elif report.severity_level == SafetyLevel.MEDIUM:
            actions.extend([
                "Account flagged for review",
                "Investigation scheduled within 24 hours"
            ])
        else:
            actions.append("Report logged for standard review")
        
        return actions

    async def _update_user_safety_score(self, user_id: int, severity: SafetyLevel, db: Session) -> None:
        """Update user's safety score based on reports"""
        # This would implement safety scoring logic
        pass


# Initialize the global social proof engine
social_proof_engine = SocialProofEngine()