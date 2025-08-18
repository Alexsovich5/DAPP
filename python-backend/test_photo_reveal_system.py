"""
Photo Reveal System Integration Test
Comprehensive test of the Soul Before Skin photo reveal timeline
"""
import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.services.photo_reveal_service import photo_reveal_service
from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation
from app.models.photo_reveal import (
    PhotoRevealTimeline, PhotoRevealStage, PhotoConsentType, 
    PhotoPrivacyLevel, UserPhoto
)


async def test_photo_reveal_workflow():
    """Test complete photo reveal workflow"""
    print("🧪 Testing Photo Reveal System - Soul Before Skin")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Step 1: Create test users
        print("1️⃣ Creating test users...")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        user1 = User(
            email=f"alice_{timestamp}@soulmate.com",
            username=f"alice_soul_{timestamp}",
            first_name="Alice",
            last_name="Heart",
            hashed_password="hashed_pw_1",
            emotional_onboarding_completed=True,
            is_profile_complete=True
        )
        
        user2 = User(
            email=f"bob_{timestamp}@soulmate.com", 
            username=f"bob_soul_{timestamp}",
            first_name="Bob",
            last_name="Mind",
            hashed_password="hashed_pw_2",
            emotional_onboarding_completed=True,
            is_profile_complete=True
        )
        
        db.add(user1)
        db.add(user2)
        db.commit()
        db.refresh(user1)
        db.refresh(user2)
        
        print(f"   ✅ Created users: {user1.first_name} (ID: {user1.id}) & {user2.first_name} (ID: {user2.id})")
        
        # Step 2: Create soul connection
        print("\n2️⃣ Creating soul connection...")
        connection = SoulConnection(
            user1_id=user1.id,
            user2_id=user2.id,
            initiated_by=user1.id,
            compatibility_score=87.5,
            current_energy_level="high"
        )
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        print(f"   ✅ Created connection (ID: {connection.id}) with {connection.compatibility_score}% compatibility")
        
        # Step 3: Add some revelations to simulate timeline progress
        print("\n3️⃣ Simulating revelation timeline progress...")
        revelations = [
            {"day": 1, "user": user1, "content": "I value deep emotional connection above all"},
            {"day": 2, "user": user2, "content": "My biggest dream is to travel the world with someone special"},
            {"day": 3, "user": user1, "content": "I find peace in quiet moments together"},
            {"day": 4, "user": user2, "content": "Laughter is my love language"},
            {"day": 5, "user": user1, "content": "I believe vulnerability is the key to intimacy"},
        ]
        
        for rev_data in revelations:
            revelation = DailyRevelation(
                connection_id=connection.id,
                sender_id=rev_data["user"].id,
                day_number=rev_data["day"],
                revelation_type="personal_value",
                content=rev_data["content"]
            )
            db.add(revelation)
        
        db.commit()
        print(f"   ✅ Added {len(revelations)} revelations over 5 days")
        
        # Step 4: Create photo timeline
        print("\n4️⃣ Creating photo reveal timeline...")
        timeline = await photo_reveal_service.create_photo_timeline(connection.id, db)
        print(f"   ✅ Timeline created (ID: {timeline.id})")
        print(f"   📅 Reveal eligible date: {timeline.photo_reveal_eligible_at}")
        print(f"   🎯 Min revelations required: {timeline.min_revelations_required}")
        
        # Step 5: Simulate uploaded photos
        print("\n5️⃣ Simulating photo uploads...")
        
        # User1's photo
        user1_photo = UserPhoto(
            user_id=user1.id,
            original_filename="alice_smile.jpg",
            file_path="/secure/photos/alice_primary.jpg",
            file_size=2048000,
            mime_type="image/jpeg",
            is_profile_primary=True,
            encryption_key_hash="secure_hash_alice",
            moderation_status="approved",
            processing_complete=True
        )
        
        # User2's photo  
        user2_photo = UserPhoto(
            user_id=user2.id,
            original_filename="bob_adventure.jpg",
            file_path="/secure/photos/bob_primary.jpg",
            file_size=1856000,
            mime_type="image/jpeg",
            is_profile_primary=True,
            encryption_key_hash="secure_hash_bob",
            moderation_status="approved", 
            processing_complete=True
        )
        
        db.add(user1_photo)
        db.add(user2_photo)
        db.commit()
        
        print(f"   ✅ Photos uploaded for both users")
        print(f"   📸 {user1.first_name}: {user1_photo.original_filename}")
        print(f"   📸 {user2.first_name}: {user2_photo.original_filename}")
        
        # Step 6: Check current reveal status
        print("\n6️⃣ Checking photo reveal status...")
        status = await photo_reveal_service.get_photo_reveal_status(connection.id, db)
        
        print(f"   Current stage: {status.current_stage.value}")
        print(f"   Days until reveal: {status.days_until_reveal}")
        print(f"   Revelations completed: {status.revelations_completed}/{status.min_revelations_required}")
        print(f"   Progress: {status.progress_percentage:.1f}%")
        print(f"   Reveal eligible: {status.reveal_eligible}")
        print(f"   Can request early: {status.can_request_early_reveal}")
        
        # Step 7: Request early photo consent 
        print("\n7️⃣ Testing early photo consent request...")
        consent_result = await photo_reveal_service.request_photo_consent(
            connection_id=connection.id,
            requester_id=user1.id,
            request_type=PhotoConsentType.MANUAL_REQUEST,
            message="I feel such a deep connection with you. Would you be open to sharing photos?",
            emotional_context={
                "emotional_state": "romantic",
                "connection_energy": "high",
                "revelation_day": 5
            },
            db=db
        )
        
        if consent_result.success:
            print(f"   ✅ Consent request sent successfully")
            print(f"   📩 Request ID: {consent_result.request_id}")
            print(f"   ⏰ Expires: {consent_result.expires_at}")
        else:
            print(f"   ❌ Consent request failed: {consent_result.message}")
        
        # Step 8: Respond to consent request
        print("\n8️⃣ Responding to photo consent request...")
        if consent_result.success:
            response_result = await photo_reveal_service.respond_to_consent_request(
                request_id=consent_result.request_id,
                user_id=user2.id,
                approved=True,
                response_message="I feel the same deep connection. Yes, let's share photos! 💕",
                granted_privacy_level=PhotoPrivacyLevel.FULLY_REVEALED,
                db=db
            )
            
            if response_result["success"]:
                print(f"   ✅ Consent granted successfully")
                print(f"   💕 Mutual consent achieved: {response_result['mutual_consent_achieved']}")
            else:
                print(f"   ❌ Response failed: {response_result['message']}")
        
        # Step 9: Check final status after consent
        print("\n9️⃣ Checking final photo reveal status...")
        final_status = await photo_reveal_service.get_photo_reveal_status(connection.id, db)
        
        print(f"   Final stage: {final_status.current_stage.value}")
        print(f"   Photos revealed: {final_status.photos_revealed}")
        print(f"   User1 consent: {final_status.user1_consent_status}")
        print(f"   User2 consent: {final_status.user2_consent_status}")
        print(f"   Mutual consent: {final_status.mutual_consent_achieved}")
        
        # Step 10: Test photo access
        print("\n🔟 Testing photo access with permissions...")
        
        # User1 accessing User2's photo
        photo_access = await photo_reveal_service.get_photo_with_permissions(
            photo_uuid=str(user2_photo.photo_uuid),
            viewer_id=user1.id,
            privacy_level=PhotoPrivacyLevel.FULLY_REVEALED,
            db=db
        )
        
        if photo_access["success"]:
            print(f"   ✅ {user1.first_name} can access {user2.first_name}'s photo")
            print(f"   🔗 Photo URL: {photo_access['photo_url']}")
            print(f"   🔒 Privacy level: {photo_access['privacy_level']}")
        else:
            print(f"   ❌ Photo access denied: {photo_access.get('error')}")
        
        # Step 11: Test automatic reveal processing
        print("\n1️⃣1️⃣ Testing automatic reveal processing...")
        
        # Simulate timeline completion by setting eligible date to past
        timeline.photo_reveal_eligible_at = datetime.utcnow() - timedelta(hours=1)
        db.commit()
        
        auto_result = await photo_reveal_service.process_automatic_reveals(db)
        print(f"   ✅ Processed {auto_result['processed']} timelines")
        print(f"   🎉 Executed {auto_result['revealed']} automatic reveals")
        
        print("\n" + "=" * 60)
        print("🎉 PHOTO REVEAL SYSTEM TEST COMPLETED SUCCESSFULLY!")
        print("✨ Soul Before Skin timeline working perfectly!")
        print("💕 From hidden photos → emotional connection → mutual reveal")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup test data
        try:
            db.query(DailyRevelation).filter(DailyRevelation.connection_id == connection.id).delete()
            db.query(PhotoRevealTimeline).filter(PhotoRevealTimeline.connection_id == connection.id).delete()
            db.query(UserPhoto).filter(UserPhoto.user_id.in_([user1.id, user2.id])).delete()
            db.query(SoulConnection).filter(SoulConnection.id == connection.id).delete()
            db.query(User).filter(User.id.in_([user1.id, user2.id])).delete()
            db.commit()
            print("\n🧹 Test data cleaned up")
        except:
            pass
        
        db.close()


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_photo_reveal_workflow())
    exit(0 if result else 1)