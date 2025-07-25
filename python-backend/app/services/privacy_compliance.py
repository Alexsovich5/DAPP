# GDPR Compliance and Privacy Framework for Dating Platform
# Comprehensive data protection and privacy management system

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import json
import hashlib
from dataclasses import dataclass, asdict
from pydantic import BaseModel
import zipfile
import io

logger = logging.getLogger(__name__)

class DataCategory(Enum):
    PROFILE_DATA = "profile_data"
    MESSAGES = "messages"
    PHOTOS = "photos"  
    LOCATION_DATA = "location_data"
    MATCHING_PREFERENCES = "matching_preferences"
    BEHAVIORAL_DATA = "behavioral_data"
    DEVICE_DATA = "device_data"
    AUTHENTICATION_DATA = "authentication_data"

class ProcessingPurpose(Enum):
    ACCOUNT_MANAGEMENT = "account_management"
    MATCHING_SERVICE = "matching_service"
    COMMUNICATION = "communication"
    SAFETY_MODERATION = "safety_moderation"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    LEGAL_COMPLIANCE = "legal_compliance"

class LegalBasis(Enum):
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"

class ConsentStatus(Enum):
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"
    EXPIRED = "expired"

class DataSubjectRight(Enum):
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    RESTRICT_PROCESSING = "restrict_processing"
    DATA_PORTABILITY = "data_portability"
    OBJECT_PROCESSING = "object_processing"
    WITHDRAW_CONSENT = "withdraw_consent"

@dataclass
class ConsentRecord:
    user_id: int
    data_category: DataCategory
    processing_purpose: ProcessingPurpose
    legal_basis: LegalBasis
    status: ConsentStatus
    granted_at: datetime
    withdrawn_at: Optional[datetime]
    expires_at: Optional[datetime]
    consent_text: str
    version: str

@dataclass
class DataProcessingRecord:
    user_id: int
    data_category: DataCategory
    processing_purpose: ProcessingPurpose
    legal_basis: LegalBasis
    processor: str
    timestamp: datetime
    retention_period: timedelta
    metadata: Dict

@dataclass
class PrivacyRequest:
    request_id: str
    user_id: int
    request_type: DataSubjectRight
    status: str
    requested_at: datetime
    processed_at: Optional[datetime]
    data_categories: List[DataCategory]
    notes: str

class PrivacyComplianceService:
    """
    Comprehensive GDPR and privacy compliance system for dating platforms
    """
    
    def __init__(self, database, redis_client, storage_service):
        self.db = database
        self.redis = redis_client
        self.storage = storage_service
        self.data_retention_policies = self._load_retention_policies()
        self.consent_templates = self._load_consent_templates()
        
    def _load_retention_policies(self) -> Dict[DataCategory, timedelta]:
        """Load data retention policies per GDPR requirements"""
        return {
            DataCategory.PROFILE_DATA: timedelta(days=2555),  # 7 years for legal purposes
            DataCategory.MESSAGES: timedelta(days=1095),  # 3 years
            DataCategory.PHOTOS: timedelta(days=365),  # 1 year after deletion
            DataCategory.LOCATION_DATA: timedelta(days=90),  # 3 months
            DataCategory.MATCHING_PREFERENCES: timedelta(days=1095),  # 3 years
            DataCategory.BEHAVIORAL_DATA: timedelta(days=365),  # 1 year
            DataCategory.DEVICE_DATA: timedelta(days=180),  # 6 months
            DataCategory.AUTHENTICATION_DATA: timedelta(days=2555)  # 7 years
        }
    
    def _load_consent_templates(self) -> Dict:
        """Load consent text templates for different purposes"""
        return {
            "profile_matching": {
                "version": "1.0",
                "text": "I consent to Dinner1 processing my profile information, preferences, and behavioral data to provide matching services and recommendations. This includes using algorithms to suggest compatible partners based on your interests, values, and communication style.",
                "purposes": [ProcessingPurpose.MATCHING_SERVICE, ProcessingPurpose.ANALYTICS],
                "legal_basis": LegalBasis.CONSENT
            },
            "communication": {
                "version": "1.0", 
                "text": "I consent to Dinner1 storing and processing my messages and communication data to enable conversations with matched users and provide customer support when needed.",
                "purposes": [ProcessingPurpose.COMMUNICATION],
                "legal_basis": LegalBasis.CONTRACT
            },
            "safety_moderation": {
                "version": "1.0",
                "text": "I understand that my content may be automatically and manually reviewed for safety, including messages, photos, and profile information, to protect all users from harassment, scams, and inappropriate content.",
                "purposes": [ProcessingPurpose.SAFETY_MODERATION],
                "legal_basis": LegalBasis.LEGITIMATE_INTERESTS
            },
            "marketing": {
                "version": "1.0",
                "text": "I consent to receiving marketing communications about Dinner1 features, events, and dating tips via email and push notifications. You may withdraw this consent at any time.",
                "purposes": [ProcessingPurpose.MARKETING],
                "legal_basis": LegalBasis.CONSENT
            },
            "location_services": {
                "version": "1.0",
                "text": "I consent to Dinner1 collecting and processing my location data to show me nearby matches and improve matching accuracy. Location data is anonymized and not shared with other users in precise form.",
                "purposes": [ProcessingPurpose.MATCHING_SERVICE],
                "legal_basis": LegalBasis.CONSENT
            }
        }
    
    async def collect_user_consent(self, user_id: int, consent_categories: List[str]) -> Dict:
        """
        Collect and record user consent for various data processing activities
        """
        consent_records = []
        
        for category in consent_categories:
            if category not in self.consent_templates:
                continue
                
            template = self.consent_templates[category]
            
            # Create consent records for each purpose
            for purpose in template["purposes"]:
                consent_record = ConsentRecord(
                    user_id=user_id,
                    data_category=self._map_category_to_data_category(category),
                    processing_purpose=purpose,
                    legal_basis=template["legal_basis"],
                    status=ConsentStatus.GRANTED,
                    granted_at=datetime.utcnow(),
                    withdrawn_at=None,
                    expires_at=datetime.utcnow() + timedelta(days=365*2) if template["legal_basis"] == LegalBasis.CONSENT else None,
                    consent_text=template["text"],
                    version=template["version"]
                )
                
                consent_records.append(consent_record)
        
        # Store consent records
        await self._store_consent_records(consent_records)
        
        # Log consent collection
        await self._log_privacy_event({
            "event_type": "consent_collected",
            "user_id": user_id,
            "categories": consent_categories,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "consents_recorded": len(consent_records),
            "categories": consent_categories
        }
    
    async def withdraw_consent(self, user_id: int, data_category: DataCategory, 
                             processing_purpose: ProcessingPurpose) -> Dict:
        """
        Allow users to withdraw consent for specific data processing
        """
        # Find active consent record
        consent_record = await self._get_consent_record(user_id, data_category, processing_purpose)
        
        if not consent_record:
            return {"success": False, "error": "No active consent found"}
        
        # Update consent status
        consent_record.status = ConsentStatus.WITHDRAWN
        consent_record.withdrawn_at = datetime.utcnow()
        
        await self._update_consent_record(consent_record)
        
        # Stop related data processing
        await self._stop_data_processing(user_id, data_category, processing_purpose)
        
        # Log withdrawal
        await self._log_privacy_event({
            "event_type": "consent_withdrawn",
            "user_id": user_id,
            "data_category": data_category.value,
            "processing_purpose": processing_purpose.value,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "message": f"Consent withdrawn for {data_category.value} - {processing_purpose.value}",
            "effective_immediately": True
        }
    
    async def process_data_subject_request(self, request: PrivacyRequest) -> Dict:
        """
        Process GDPR data subject rights requests
        """
        request_handlers = {
            DataSubjectRight.ACCESS: self._handle_access_request,
            DataSubjectRight.RECTIFICATION: self._handle_rectification_request,
            DataSubjectRight.ERASURE: self._handle_erasure_request,
            DataSubjectRight.RESTRICT_PROCESSING: self._handle_restriction_request,
            DataSubjectRight.DATA_PORTABILITY: self._handle_portability_request,
            DataSubjectRight.OBJECT_PROCESSING: self._handle_objection_request,
            DataSubjectRight.WITHDRAW_CONSENT: self._handle_consent_withdrawal_request
        }
        
        handler = request_handlers.get(request.request_type)
        if not handler:
            return {"success": False, "error": "Unsupported request type"}
        
        try:
            # Update request status
            await self._update_request_status(request.request_id, "processing")
            
            # Process the request
            result = await handler(request)
            
            # Update request status
            status = "completed" if result["success"] else "failed"
            await self._update_request_status(request.request_id, status)
            
            # Log the processing
            await self._log_privacy_event({
                "event_type": "data_subject_request_processed",
                "request_id": request.request_id,
                "user_id": request.user_id,
                "request_type": request.request_type.value,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing data subject request {request.request_id}: {str(e)}")
            await self._update_request_status(request.request_id, "failed")
            return {"success": False, "error": str(e)}
    
    async def _handle_access_request(self, request: PrivacyRequest) -> Dict:
        """Handle right of access (Article 15) - provide copy of personal data"""
        
        # Collect all user data
        user_data = {}
        
        for category in request.data_categories:
            data = await self._collect_user_data_by_category(request.user_id, category)
            user_data[category.value] = data
        
        # Include processing information
        processing_info = await self._get_processing_information(request.user_id)
        user_data["processing_information"] = processing_info
        
        # Include consent records
        consent_records = await self._get_user_consent_records(request.user_id)
        user_data["consent_records"] = consent_records
        
        # Create downloadable package
        data_package = await self._create_data_package(user_data, request.user_id)
        
        return {
            "success": True,
            "data_package_url": data_package["url"],
            "data_categories": [cat.value for cat in request.data_categories],
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
    
    async def _handle_rectification_request(self, request: PrivacyRequest) -> Dict:
        """Handle right to rectification (Article 16) - correct inaccurate data"""
        
        corrections_applied = []
        
        # This would typically involve specific field updates
        # For now, we flag the profile for manual review
        await self._flag_profile_for_rectification(request.user_id, request.notes)
        
        return {
            "success": True,
            "message": "Rectification request received. Profile flagged for manual review.",
            "estimated_completion": "48 hours",
            "corrections_applied": corrections_applied
        }
    
    async def _handle_erasure_request(self, request: PrivacyRequest) -> Dict:
        """Handle right to erasure (Article 17) - delete personal data"""
        
        # Check if erasure is legally required or if we can retain data
        retention_check = await self._check_data_retention_requirements(request.user_id)
        
        if not retention_check["can_erase"]:
            return {
                "success": False,
                "error": "Data cannot be erased due to legal obligations",
                "legal_basis": retention_check["legal_basis"],
                "retention_period": retention_check["retention_period"]
            }
        
        # Perform erasure
        erasure_results = {}
        
        for category in request.data_categories:
            result = await self._erase_user_data_category(request.user_id, category)
            erasure_results[category.value] = result
        
        # Anonymize remaining data that cannot be deleted
        await self._anonymize_remaining_data(request.user_id)
        
        return {
            "success": True,
            "erasure_results": erasure_results,
            "anonymized_data": "Remaining data has been anonymized",
            "effective_date": datetime.utcnow().isoformat()
        }
    
    async def _handle_portability_request(self, request: PrivacyRequest) -> Dict:
        """Handle right to data portability (Article 20) - export data in machine-readable format"""
        
        # Collect user data in structured format
        portable_data = {}
        
        for category in request.data_categories:
            data = await self._collect_portable_data(request.user_id, category)
            portable_data[category.value] = data
        
        # Create JSON export
        json_export = json.dumps(portable_data, indent=2, default=str)
        
        # Store export file
        export_file = await self._store_export_file(json_export, request.user_id)
        
        return {
            "success": True,
            "export_format": "JSON",
            "download_url": export_file["url"],
            "file_size": export_file["size"],
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
    
    async def get_privacy_dashboard_data(self, user_id: int) -> Dict:
        """
        Provide comprehensive privacy dashboard information for users
        """
        
        # Get current consent status
        consent_status = await self._get_user_consent_status(user_id)
        
        # Get data processing activities
        processing_activities = await self._get_processing_activities(user_id)
        
        # Get data retention information
        retention_info = await self._get_retention_information(user_id)
        
        # Get privacy request history
        request_history = await self._get_privacy_request_history(user_id)
        
        # Calculate privacy score
        privacy_score = await self._calculate_privacy_score(user_id)
        
        return {
            "user_id": user_id,
            "privacy_score": privacy_score,
            "consent_status": consent_status,
            "data_processing": processing_activities,
            "data_retention": retention_info,
            "request_history": request_history,
            "available_rights": [right.value for right in DataSubjectRight],
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def automated_data_cleanup(self):
        """
        Automated cleanup of expired data per retention policies
        """
        cleanup_results = {}
        
        for category, retention_period in self.data_retention_policies.items():
            cutoff_date = datetime.utcnow() - retention_period
            
            # Find expired data
            expired_data = await self._find_expired_data(category, cutoff_date)
            
            if expired_data:
                # Clean up expired data
                cleanup_count = await self._cleanup_expired_data(category, expired_data)
                cleanup_results[category.value] = cleanup_count
                
                logger.info(f"Cleaned up {cleanup_count} expired {category.value} records")
        
        # Clean up expired consent records
        expired_consents = await self._cleanup_expired_consents()
        cleanup_results["expired_consents"] = expired_consents
        
        # Generate cleanup report
        await self._generate_cleanup_report(cleanup_results)
        
        return cleanup_results
    
    async def generate_privacy_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Generate comprehensive privacy compliance report
        """
        
        # Consent metrics
        consent_metrics = await self._get_consent_metrics(start_date, end_date)
        
        # Data subject requests metrics
        request_metrics = await self._get_request_metrics(start_date, end_date)
        
        # Data processing metrics
        processing_metrics = await self._get_processing_metrics(start_date, end_date)
        
        # Compliance score
        compliance_score = await self._calculate_compliance_score()
        
        # Data breach incidents (if any)
        breach_incidents = await self._get_breach_incidents(start_date, end_date)
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "compliance_score": compliance_score,
            "consent_metrics": consent_metrics,
            "data_subject_requests": request_metrics,
            "data_processing": processing_metrics,
            "data_breaches": breach_incidents,
            "recommendations": await self._generate_compliance_recommendations(),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # Helper methods
    
    def _map_category_to_data_category(self, category: str) -> DataCategory:
        """Map consent category strings to DataCategory enum"""
        mapping = {
            "profile_matching": DataCategory.PROFILE_DATA,
            "communication": DataCategory.MESSAGES,
            "marketing": DataCategory.PROFILE_DATA,
            "location_services": DataCategory.LOCATION_DATA
        }
        return mapping.get(category, DataCategory.PROFILE_DATA)
    
    async def _collect_user_data_by_category(self, user_id: int, category: DataCategory) -> Dict:
        """Collect all user data for a specific category"""
        
        data_collectors = {
            DataCategory.PROFILE_DATA: self._collect_profile_data,
            DataCategory.MESSAGES: self._collect_message_data,
            DataCategory.PHOTOS: self._collect_photo_data,
            DataCategory.LOCATION_DATA: self._collect_location_data,
            DataCategory.MATCHING_PREFERENCES: self._collect_preference_data,
            DataCategory.BEHAVIORAL_DATA: self._collect_behavioral_data,
            DataCategory.DEVICE_DATA: self._collect_device_data,
            DataCategory.AUTHENTICATION_DATA: self._collect_auth_data
        }
        
        collector = data_collectors.get(category)
        if collector:
            return await collector(user_id)
        return {}
    
    async def _collect_profile_data(self, user_id: int) -> Dict:
        """Collect user profile data"""
        # Implementation would query database for profile information
        return {
            "basic_info": "User profile data",
            "preferences": "User preferences",
            "bio": "User bio information"
        }
    
    async def _collect_message_data(self, user_id: int) -> List[Dict]:
        """Collect user message data"""
        # Implementation would query message history
        return [
            {
                "message_id": "example",
                "content": "Example message",
                "timestamp": datetime.utcnow().isoformat(),
                "recipient": "anonymized_user_id"
            }
        ]
    
    async def _create_data_package(self, user_data: Dict, user_id: int) -> Dict:
        """Create downloadable data package for user"""
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add main data file
            zip_file.writestr("user_data.json", json.dumps(user_data, indent=2, default=str))
            
            # Add privacy policy
            zip_file.writestr("privacy_policy.txt", "Current privacy policy content...")
            
            # Add explanation of data
            zip_file.writestr("README.txt", "Explanation of your personal data package...")
        
        zip_buffer.seek(0)
        
        # Store file and return URL (implementation depends on storage service)
        file_url = await self.storage.store_temp_file(
            zip_buffer.getvalue(), 
            f"user_data_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}.zip",
            expires_in_days=30
        )
        
        return {
            "url": file_url,
            "size": len(zip_buffer.getvalue())
        }
    
    async def _store_consent_records(self, consent_records: List[ConsentRecord]):
        """Store consent records in database"""
        # Implementation would store in database
        for record in consent_records:
            await self.redis.lpush("consent_records", json.dumps(asdict(record), default=str))
    
    async def _log_privacy_event(self, event_data: Dict):
        """Log privacy-related events for audit trail"""
        event_data["event_id"] = hashlib.sha256(
            f"{event_data['user_id']}{event_data['timestamp']}".encode()
        ).hexdigest()[:16]
        
        await self.redis.lpush("privacy_events", json.dumps(event_data))
        logger.info(f"Privacy event logged: {event_data['event_type']}")
    
    async def _calculate_privacy_score(self, user_id: int) -> Dict:
        """Calculate user's privacy score based on their settings and consents"""
        
        # Get consent status
        consents = await self._get_user_consent_records(user_id)
        
        # Calculate score based on privacy-friendly choices
        score = 75  # Base score
        
        # Bonus for granular consent management
        if len(consents) > 3:
            score += 10
        
        # Penalty for broad marketing consent
        marketing_consents = [c for c in consents if c.get("purpose") == "marketing"]
        if marketing_consents:
            score -= 5
        
        # Bonus for location consent limitations
        location_consents = [c for c in consents if c.get("category") == "location_data"]
        if not location_consents:
            score += 10
        
        return {
            "score": min(max(score, 0), 100),
            "level": "High" if score > 80 else "Medium" if score > 60 else "Low",
            "recommendations": self._get_privacy_recommendations(score)
        }
    
    def _get_privacy_recommendations(self, score: int) -> List[str]:
        """Get privacy improvement recommendations"""
        recommendations = []
        
        if score < 70:
            recommendations.append("Review and limit marketing consents")
            recommendations.append("Consider restricting location data sharing")
        
        if score < 60:
            recommendations.append("Review data sharing settings")
            recommendations.append("Consider using more privacy-focused features")
        
        return recommendations

# GDPR Article mapping for compliance tracking
GDPR_ARTICLES = {
    DataSubjectRight.ACCESS: "Article 15 - Right of access by the data subject",
    DataSubjectRight.RECTIFICATION: "Article 16 - Right to rectification", 
    DataSubjectRight.ERASURE: "Article 17 - Right to erasure ('right to be forgotten')",
    DataSubjectRight.RESTRICT_PROCESSING: "Article 18 - Right to restriction of processing",
    DataSubjectRight.DATA_PORTABILITY: "Article 20 - Right to data portability",
    DataSubjectRight.OBJECT_PROCESSING: "Article 21 - Right to object",
    DataSubjectRight.WITHDRAW_CONSENT: "Article 7 - Conditions for consent"
}

# Data retention policies per legal requirements
LEGAL_RETENTION_REQUIREMENTS = {
    "financial_records": timedelta(days=2555),  # 7 years
    "user_agreements": timedelta(days=2555),   # 7 years
    "safety_incidents": timedelta(days=1825),  # 5 years
    "marketing_data": timedelta(days=1095),    # 3 years
    "analytics_data": timedelta(days=365),     # 1 year
    "session_logs": timedelta(days=90)         # 3 months
}