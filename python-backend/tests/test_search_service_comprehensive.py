import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json
import uuid
from app.services.search_service import (
    ElasticsearchService,
    SearchType,
    SortOrder,
    SearchCriteria,
    SearchResult,
    SearchResponse
)
class TestElasticsearchService:
    
    @pytest.fixture
    def mock_elasticsearch(self):
        mock_es = AsyncMock()
        mock_es.indices = AsyncMock()
        mock_es.indices.create = AsyncMock()
        mock_es.search = AsyncMock()
        mock_es.index = AsyncMock()
        mock_es.delete = AsyncMock()
        mock_es.get = AsyncMock()
        return mock_es
    
    @pytest.fixture
    def mock_redis(self):
        mock_redis = Mock()
        mock_redis.get = Mock()
        mock_redis.set = Mock()
        mock_redis.lpush = Mock()
        mock_redis.ltrim = Mock()
        mock_redis.lrange = Mock()
        return mock_redis
    
    @pytest.fixture
    def search_service(self, mock_elasticsearch, mock_redis):
        with patch.object(ElasticsearchService, '_setup_indexes'):
            return ElasticsearchService(mock_elasticsearch, mock_redis)
    
    @pytest.fixture
    def sample_search_criteria(self):
        return SearchCriteria(
            search_type=SearchType.PROFILE_DISCOVERY,
            query="travel enthusiast",
            filters={"gender": "female", "verified_only": True},
            location=(37.7749, -122.4194),  # San Francisco
            radius_km=25,
            age_range=(25, 35),
            interests=["travel", "photography", "hiking"],
            sort_by=SortOrder.COMPATIBILITY_SCORE,
            page=0,
            size=20
        )
    
    @pytest.fixture
    def sample_search_response(self):
        return {
            "hits": {
                "total": {"value": 150},
                "hits": [
                    {
                        "_score": 0.95,
                        "_source": {
                            "user_id": 123,
                            "username": "travel_girl",
                            "first_name": "Sarah",
                            "age": 28,
                            "gender": "female",
                            "location": {"lat": 37.7849, "lon": -122.4094},
                            "city": "San Francisco",
                            "last_active": "2024-01-15T10:30:00Z",
                            "profile_completeness": 0.95,
                            "photo_count": 5,
                            "emotional_depth_score": 0.88,
                            "verification_status": "verified",
                            "is_active": True,
                            "is_premium": True
                        }
                    },
                    {
                        "_score": 0.87,
                        "_source": {
                            "user_id": 456,
                            "username": "adventure_seeker",
                            "first_name": "Emma",
                            "age": 31,
                            "gender": "female",
                            "location": {"lat": 37.7649, "lon": -122.4294},
                            "city": "San Francisco",
                            "last_active": "2024-01-14T15:45:00Z",
                            "profile_completeness": 0.92,
                            "photo_count": 8,
                            "emotional_depth_score": 0.85,
                            "verification_status": "verified",
                            "is_active": True,
                            "is_premium": False
                        }
                    }
                ]
            }
        }
    def test_service_initialization(self, search_service, mock_elasticsearch, mock_redis):
        """Test search service initialization"""
        assert search_service.es_client == mock_elasticsearch
        assert search_service.redis_client == mock_redis
        assert len(search_service.indexes) == 3
        assert "users" in search_service.indexes
        assert "profiles" in search_service.indexes
        assert "activities" in search_service.indexes
    def test_search_configurations(self, search_service):
        """Test search configurations are properly set"""
        config = search_service.search_configs
        
        assert config['default_radius_km'] == 50
        assert config['max_results'] == 100
        assert config['cache_ttl'] == 300
        assert config['min_compatibility_score'] == 0.3
        
        # Test boost factors
        boost_factors = config['boost_factors']
        assert boost_factors['recent_activity'] == 2.0
        assert boost_factors['profile_completeness'] == 1.5
        assert boost_factors['mutual_interests'] == 3.0
        assert boost_factors['location_proximity'] == 1.8
        assert boost_factors['age_compatibility'] == 1.2
    def test_search_type_enum_values(self):
        """Test SearchType enum values"""
        assert SearchType.PROFILE_DISCOVERY.value == "profile_discovery"
        assert SearchType.COMPATIBILITY_SEARCH.value == "compatibility_search"
        assert SearchType.INTEREST_BASED.value == "interest_based"
        assert SearchType.LOCATION_BASED.value == "location_based"
        assert SearchType.KEYWORD_SEARCH.value == "keyword_search"
        assert SearchType.ADVANCED_FILTERS.value == "advanced_filters"
    def test_sort_order_enum_values(self):
        """Test SortOrder enum values"""
        assert SortOrder.RELEVANCE.value == "relevance"
        assert SortOrder.COMPATIBILITY_SCORE.value == "compatibility_score"
        assert SortOrder.DISTANCE.value == "distance"
        assert SortOrder.LAST_ACTIVE.value == "last_active"
        assert SortOrder.NEWEST_FIRST.value == "newest_first"
        assert SortOrder.RANDOM.value == "random"
    def test_search_criteria_dataclass(self, sample_search_criteria):
        """Test SearchCriteria dataclass"""
        assert sample_search_criteria.search_type == SearchType.PROFILE_DISCOVERY
        assert sample_search_criteria.query == "travel enthusiast"
        assert sample_search_criteria.location == (37.7749, -122.4194)
        assert sample_search_criteria.radius_km == 25
        assert sample_search_criteria.age_range == (25, 35)
        assert len(sample_search_criteria.interests) == 3
        assert sample_search_criteria.sort_by == SortOrder.COMPATIBILITY_SCORE
    def test_search_result_dataclass(self):
        """Test SearchResult dataclass"""
        result = SearchResult(
            user_id=123,
            score=0.95,
            compatibility_score=0.88,
            distance_km=5.2,
            match_reasons=["High compatibility", "Lives nearby"],
            profile_data={"name": "Test User"},
            last_active=datetime.utcnow()
        )
        
        assert result.user_id == 123
        assert result.score == 0.95
        assert result.compatibility_score == 0.88
        assert result.distance_km == 5.2
        assert len(result.match_reasons) == 2
    def test_search_response_dataclass(self):
        """Test SearchResponse dataclass"""
        response = SearchResponse(
            results=[],
            total_count=150,
            page=0,
            size=20,
            took_ms=45,
            search_id="test_search_123",
            suggestions=["Try expanding age range"]
        )
        
        assert response.total_count == 150
        assert response.page == 0
        assert response.size == 20
        assert response.took_ms == 45
        assert response.search_id == "test_search_123"
        assert len(response.suggestions) == 1
    @pytest.mark.asyncio
    async def test_setup_indexes(self, mock_elasticsearch, mock_redis):
        """Test Elasticsearch indexes setup"""
        with patch.object(ElasticsearchService, '_create_users_index') as mock_users:
            with patch.object(ElasticsearchService, '_create_profiles_index') as mock_profiles:
                with patch.object(ElasticsearchService, '_create_activities_index') as mock_activities:
                    service = ElasticsearchService(mock_elasticsearch, mock_redis)
                    await service._setup_indexes()
                    
                    mock_users.assert_called_once()
                    mock_profiles.assert_called_once()
                    mock_activities.assert_called_once()
    @pytest.mark.asyncio
    async def test_create_users_index_success(self, search_service, mock_elasticsearch):
        """Test successful users index creation"""
        mock_elasticsearch.indices.create.return_value = {"acknowledged": True}
        
        await search_service._create_users_index()
        
        mock_elasticsearch.indices.create.assert_called_once()
        call_args = mock_elasticsearch.indices.create.call_args
        assert call_args[1]['index'] == search_service.indexes['users']
        assert 'mappings' in call_args[1]['body']
        assert 'settings' in call_args[1]['body']
    @pytest.mark.asyncio
    async def test_create_users_index_error(self, search_service, mock_elasticsearch):
        """Test users index creation error handling"""
        mock_elasticsearch.indices.create.side_effect = Exception("Index creation failed")
        
        # Should not raise exception but log warning
        await search_service._create_users_index()
        
        mock_elasticsearch.indices.create.assert_called_once()
    @pytest.mark.asyncio
    async def test_create_profiles_index(self, search_service, mock_elasticsearch):
        """Test profiles index creation"""
        await search_service._create_profiles_index()
        
        mock_elasticsearch.indices.create.assert_called_once()
        call_args = mock_elasticsearch.indices.create.call_args
        
        # Check synonym filters are configured
        body = call_args[1]['body']
        assert 'analysis' in body['settings']
        assert 'synonym' in body['settings']['analysis']['filter']
    @pytest.mark.asyncio
    async def test_create_activities_index(self, search_service, mock_elasticsearch):
        """Test activities index creation"""
        await search_service._create_activities_index()
        
        mock_elasticsearch.indices.create.assert_called_once()
        call_args = mock_elasticsearch.indices.create.call_args
        
        # Check mapping properties
        mapping = call_args[1]['body']['mappings']['properties']
        assert 'user_id' in mapping
        assert 'activity_type' in mapping
        assert 'timestamp' in mapping
        assert 'interaction_score' in mapping
    @pytest.mark.asyncio
    async def test_search_users_success(self, search_service, sample_search_criteria, sample_search_response):
        """Test successful user search"""
        with patch.object(search_service, '_get_cached_search', return_value=None):
            with patch.object(search_service, '_build_search_query', return_value={"query": {"match_all": {}}}) as mock_build:
                with patch.object(search_service, '_process_search_results', return_value=[]) as mock_process:
                    with patch.object(search_service, '_cache_search_results') as mock_cache:
                        with patch.object(search_service, '_track_search_analytics') as mock_track:
                            with patch.object(search_service, '_generate_search_suggestions', return_value=[]):
                                search_service.es_client.search.return_value = sample_search_response
                                
                                result = await search_service.search_users(100, sample_search_criteria)
                                
                                assert isinstance(result, SearchResponse)
                                assert result.total_count == 150
                                mock_build.assert_called_once_with(100, sample_search_criteria)
                                mock_process.assert_called_once()
                                mock_cache.assert_called_once()
                                mock_track.assert_called_once()
    @pytest.mark.asyncio
    async def test_search_users_cached_result(self, search_service, sample_search_criteria):
        """Test search with cached result"""
        cached_response = SearchResponse(
            results=[], total_count=50, page=0, size=20, took_ms=5, search_id="cached"
        )
        
        with patch.object(search_service, '_get_cached_search', return_value=cached_response):
            result = await search_service.search_users(100, sample_search_criteria)
            
            assert result == cached_response
            assert result.search_id == "cached"
            # Should not call Elasticsearch if cached result exists
            search_service.es_client.search.assert_not_called()
    @pytest.mark.asyncio
    async def test_search_users_error_handling(self, search_service, sample_search_criteria):
        """Test search error handling"""
        with patch.object(search_service, '_get_cached_search', return_value=None):
            with patch.object(search_service, '_build_search_query', side_effect=Exception("Query build error")):
                result = await search_service.search_users(100, sample_search_criteria)
                
                assert isinstance(result, SearchResponse)
                assert result.total_count == 0
                assert result.search_id == "error"
                assert len(result.results) == 0
    @pytest.mark.asyncio
    async def test_build_search_query_basic(self, search_service, sample_search_criteria):
        """Test basic search query building"""
        with patch.object(search_service, '_get_user_profile', return_value={"age": 30, "interests": ["travel"]}):
            with patch.object(search_service, '_add_compatibility_boosting') as mock_compatibility:
                with patch.object(search_service, '_apply_advanced_filters') as mock_filters:
                    with patch.object(search_service, '_apply_sorting') as mock_sorting:
                        with patch.object(search_service, '_wrap_with_function_score', return_value={"test": "query"}) as mock_wrap:
                            result = await search_service._build_search_query(100, sample_search_criteria)
                            
                            assert result == {"test": "query"}
                            mock_compatibility.assert_not_called()  # Not compatibility search
                            mock_filters.assert_called_once()
                            mock_sorting.assert_called_once()
                            mock_wrap.assert_called_once()
    @pytest.mark.asyncio
    async def test_build_search_query_keyword_search(self, search_service):
        """Test keyword search query building"""
        criteria = SearchCriteria(
            search_type=SearchType.KEYWORD_SEARCH,
            query="adventure travel"
        )
        
        with patch.object(search_service, '_get_user_profile', return_value={}):
            with patch.object(search_service, '_apply_advanced_filters'):
                with patch.object(search_service, '_apply_sorting'):
                    with patch.object(search_service, '_wrap_with_function_score', return_value={"query": {"bool": {"must": []}}}) as mock_wrap:
                        result = await search_service._build_search_query(100, criteria)
                        
                        # Should add multi_match query for keyword search
                        mock_wrap.assert_called_once()
    @pytest.mark.asyncio
    async def test_build_search_query_interest_based(self, search_service):
        """Test interest-based search query building"""
        criteria = SearchCriteria(
            search_type=SearchType.INTEREST_BASED,
            interests=["hiking", "photography", "travel"]
        )
        
        with patch.object(search_service, '_get_user_profile', return_value={}):
            with patch.object(search_service, '_apply_advanced_filters'):
                with patch.object(search_service, '_apply_sorting'):
                    with patch.object(search_service, '_wrap_with_function_score', return_value={"query": {"bool": {"should": []}}}) as mock_wrap:
                        result = await search_service._build_search_query(100, criteria)
                        
                        mock_wrap.assert_called_once()
    @pytest.mark.asyncio
    async def test_build_search_query_compatibility_search(self, search_service):
        """Test compatibility search query building"""
        criteria = SearchCriteria(search_type=SearchType.COMPATIBILITY_SEARCH)
        
        with patch.object(search_service, '_get_user_profile', return_value={"interests": ["travel"], "personality_traits": {}}):
            with patch.object(search_service, '_add_compatibility_boosting') as mock_compatibility:
                with patch.object(search_service, '_apply_advanced_filters'):
                    with patch.object(search_service, '_apply_sorting'):
                        with patch.object(search_service, '_wrap_with_function_score', return_value={"test": "query"}):
                            result = await search_service._build_search_query(100, criteria)
                            
                            mock_compatibility.assert_called_once()
    @pytest.mark.asyncio
    async def test_add_compatibility_boosting(self, search_service):
        """Test compatibility boosting addition"""
        query = {"query": {"bool": {"should": []}}}
        searcher_profile = {
            "interests": ["travel", "hiking"],
            "personality_traits": {"outgoing": 0.8, "adventurous": 0.7}
        }
        
        with patch.object(search_service, '_get_compatible_traits', return_value={"outgoing": 1.5, "adventurous": 1.3}):
            await search_service._add_compatibility_boosting(query, searcher_profile)
            
            # Should add boosting for interests and personality traits
            should_clauses = query["query"]["bool"]["should"]
            assert len(should_clauses) > 0
    @pytest.mark.asyncio
    async def test_add_compatibility_boosting_no_profile(self, search_service):
        """Test compatibility boosting with no searcher profile"""
        query = {"query": {"bool": {"should": []}}}
        
        await search_service._add_compatibility_boosting(query, None)
        
        # Should not modify query if no profile
        assert len(query["query"]["bool"]["should"]) == 0
    @pytest.mark.asyncio
    async def test_apply_advanced_filters(self, search_service):
        """Test advanced filters application"""
        query = {"query": {"bool": {"filter": []}}}
        filters = {
            "gender": "female",
            "education_level": "bachelor",
            "verified_only": True,
            "has_photos": True,
            "premium_only": True,
            "min_profile_completeness": 0.8
        }
        
        await search_service._apply_advanced_filters(query, filters)
        
        filter_clauses = query["query"]["bool"]["filter"]
        assert len(filter_clauses) == 6
        
        # Check specific filters
        gender_filter = next((f for f in filter_clauses if "gender" in f.get("term", {})), None)
        assert gender_filter is not None
        assert gender_filter["term"]["gender"] == "female"
    @pytest.mark.asyncio
    async def test_apply_sorting_compatibility_score(self, search_service):
        """Test sorting by compatibility score"""
        query = {}
        criteria = SearchCriteria(
            search_type=SearchType.PROFILE_DISCOVERY,
            sort_by=SortOrder.COMPATIBILITY_SCORE
        )
        
        await search_service._apply_sorting(query, criteria)
        
        assert "sort" in query
        sort_fields = query["sort"]
        assert {"emotional_depth_score": {"order": "desc"}} in sort_fields
        assert {"profile_completeness": {"order": "desc"}} in sort_fields
        assert "_score" in sort_fields
    @pytest.mark.asyncio
    async def test_apply_sorting_distance(self, search_service):
        """Test sorting by distance"""
        query = {}
        criteria = SearchCriteria(
            search_type=SearchType.LOCATION_BASED,
            sort_by=SortOrder.DISTANCE,
            location=(37.7749, -122.4194)
        )
        
        await search_service._apply_sorting(query, criteria)
        
        assert "sort" in query
        geo_sort = query["sort"][0]["_geo_distance"]
        assert geo_sort["location"]["lat"] == 37.7749
        assert geo_sort["location"]["lon"] == -122.4194
        assert geo_sort["order"] == "asc"
    @pytest.mark.asyncio
    async def test_apply_sorting_last_active(self, search_service):
        """Test sorting by last active"""
        query = {}
        criteria = SearchCriteria(
            search_type=SearchType.PROFILE_DISCOVERY,
            sort_by=SortOrder.LAST_ACTIVE
        )
        
        await search_service._apply_sorting(query, criteria)
        
        assert query["sort"] == [{"last_active": {"order": "desc"}}, "_score"]
    @pytest.mark.asyncio
    async def test_apply_sorting_random(self, search_service):
        """Test random sorting"""
        query = {}
        criteria = SearchCriteria(
            search_type=SearchType.PROFILE_DISCOVERY,
            sort_by=SortOrder.RANDOM
        )
        
        await search_service._apply_sorting(query, criteria)
        
        assert "sort" in query
        script_sort = query["sort"][0]["_script"]
        assert script_sort["type"] == "number"
        assert "Math.random()" in script_sort["script"]["source"]
    @pytest.mark.asyncio
    async def test_wrap_with_function_score(self, search_service):
        """Test function score wrapping"""
        query = {"query": {"bool": {"must": []}}}
        searcher_profile = {"age": 30}
        criteria = SearchCriteria(
            search_type=SearchType.PROFILE_DISCOVERY,
            location=(37.7749, -122.4194)
        )
        
        result = await search_service._wrap_with_function_score(query, searcher_profile, criteria)
        
        assert "function_score" in result["query"]
        function_score = result["query"]["function_score"]
        assert "functions" in function_score
        assert len(function_score["functions"]) >= 3  # recent activity, profile completeness, location
        assert function_score["score_mode"] == "multiply"
        assert function_score["boost_mode"] == "multiply"
    @pytest.mark.asyncio
    async def test_process_search_results(self, search_service, sample_search_response, sample_search_criteria):
        """Test search results processing"""
        with patch.object(search_service, '_calculate_compatibility_score', return_value=0.85):
            with patch.object(search_service, '_generate_match_reasons', return_value=["High compatibility", "Lives nearby"]):
                results = await search_service._process_search_results(
                    100, sample_search_response, sample_search_criteria
                )
                
                assert len(results) == 2
                assert isinstance(results[0], SearchResult)
                assert results[0].user_id == 123
                assert results[0].compatibility_score == 0.85
                assert results[0].distance_km is not None  # Should calculate distance
                assert len(results[0].match_reasons) == 2
    @pytest.mark.asyncio
    async def test_process_search_results_no_location(self, search_service, sample_search_response):
        """Test search results processing without location"""
        criteria = SearchCriteria(search_type=SearchType.PROFILE_DISCOVERY)
        
        with patch.object(search_service, '_calculate_compatibility_score', return_value=0.85):
            with patch.object(search_service, '_generate_match_reasons', return_value=["High compatibility"]):
                results = await search_service._process_search_results(
                    100, sample_search_response, criteria
                )
                
                assert len(results) == 2
                assert results[0].distance_km is None  # No location provided
    def test_generate_match_reasons(self, search_service, sample_search_criteria):
        """Test match reasons generation"""
        hit = {
            "_source": {
                "emotional_depth_score": 0.85,
                "last_active": "2024-01-15T10:30:00Z",
                "profile_completeness": 0.95,
                "verification_status": "verified",
                "photo_count": 5
            }
        }
        
        reasons = search_service._generate_match_reasons(hit, sample_search_criteria)
        
        assert isinstance(reasons, list)
        assert len(reasons) <= 3  # Should limit to 3 reasons
        assert any("emotional compatibility" in reason.lower() for reason in reasons)
        assert any("complete profile" in reason.lower() for reason in reasons)
        assert any("verified" in reason.lower() for reason in reasons)
    @pytest.mark.asyncio
    async def test_calculate_compatibility_score_cached(self, search_service, mock_redis):
        """Test compatibility score calculation with cached result"""
        mock_redis.get.return_value = "0.78"
        
        score = await search_service._calculate_compatibility_score(100, 200)
        
        assert score == 0.78
        cache_key = "compatibility:100:200"
        mock_redis.get.assert_called_once_with(cache_key)
    @pytest.mark.asyncio
    async def test_calculate_compatibility_score_uncached(self, search_service, mock_redis):
        """Test compatibility score calculation without cached result"""
        mock_redis.get.return_value = None
        
        with patch('random.uniform', return_value=0.65):
            score = await search_service._calculate_compatibility_score(100, 200)
            
            assert score == 0.65
            # Should cache the result
            mock_redis.set.assert_called_once()
            assert mock_redis.set.call_args[0][1] == "0.65"
            assert mock_redis.set.call_args[1]["ex"] == 3600
    @pytest.mark.asyncio
    async def test_calculate_compatibility_score_error(self, search_service, mock_redis):
        """Test compatibility score calculation error handling"""
        mock_redis.get.side_effect = Exception("Redis error")
        
        score = await search_service._calculate_compatibility_score(100, 200)
        
        assert score is None
    def test_get_compatible_traits(self, search_service):
        """Test compatible personality traits mapping"""
        personality_traits = {"outgoing": 0.8, "intellectual": 0.7}
        
        compatible_traits = search_service._get_compatible_traits(personality_traits)
        
        assert isinstance(compatible_traits, dict)
        assert "outgoing" in compatible_traits
        assert "intellectual" in compatible_traits
        assert all(isinstance(boost, float) for boost in compatible_traits.values())
    @pytest.mark.asyncio
    async def test_get_user_profile_found(self, search_service, mock_elasticsearch):
        """Test getting user profile when found"""
        mock_response = {
            "found": True,
            "_source": {"user_id": 123, "interests": ["travel"]}
        }
        mock_elasticsearch.get.return_value = mock_response
        
        profile = await search_service._get_user_profile(123)
        
        assert profile == {"user_id": 123, "interests": ["travel"]}
        mock_elasticsearch.get.assert_called_once_with(
            index=search_service.indexes['profiles'],
            id=123,
            ignore=404
        )
    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self, search_service, mock_elasticsearch):
        """Test getting user profile when not found"""
        mock_response = {"found": False}
        mock_elasticsearch.get.return_value = mock_response
        
        profile = await search_service._get_user_profile(123)
        
        assert profile is None
    @pytest.mark.asyncio
    async def test_get_user_profile_error(self, search_service, mock_elasticsearch):
        """Test getting user profile error handling"""
        mock_elasticsearch.get.side_effect = Exception("Elasticsearch error")
        
        profile = await search_service._get_user_profile(123)
        
        assert profile is None
    def test_generate_cache_key(self, search_service, sample_search_criteria):
        """Test cache key generation"""
        cache_key = search_service._generate_cache_key(100, sample_search_criteria)
        
        assert cache_key.startswith("search:100:")
        assert len(cache_key.split(":")) == 3
        
        # Same criteria should generate same key
        cache_key2 = search_service._generate_cache_key(100, sample_search_criteria)
        assert cache_key == cache_key2
    @pytest.mark.asyncio
    async def test_get_cached_search_found(self, search_service, mock_redis):
        """Test getting cached search results when found"""
        cached_data = {
            "results": [],
            "total_count": 50,
            "page": 0,
            "size": 20,
            "took_ms": 10,
            "search_id": "cached_123"
        }
        mock_redis.get.return_value = json.dumps(cached_data)
        
        result = await search_service._get_cached_search("test_cache_key")
        
        assert isinstance(result, SearchResponse)
        assert result.total_count == 50
        assert result.search_id == "cached_123"
    @pytest.mark.asyncio
    async def test_get_cached_search_not_found(self, search_service, mock_redis):
        """Test getting cached search results when not found"""
        mock_redis.get.return_value = None
        
        result = await search_service._get_cached_search("test_cache_key")
        
        assert result is None
    @pytest.mark.asyncio
    async def test_cache_search_results(self, search_service, mock_redis):
        """Test caching search results"""
        response = SearchResponse(
            results=[], total_count=100, page=0, size=20, took_ms=25, search_id="test_123"
        )
        
        await search_service._cache_search_results("test_cache_key", response)
        
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "test_cache_key"
        assert call_args[1]["ex"] == 300  # cache_ttl
    def test_generate_search_id(self, search_service):
        """Test search ID generation"""
        search_id = search_service._generate_search_id()
        
        assert isinstance(search_id, str)
        assert len(search_id) == 8
    @pytest.mark.asyncio
    async def test_generate_search_suggestions_no_results(self, search_service, sample_search_criteria):
        """Test search suggestions when no results"""
        response = {"hits": {"total": {"value": 0}}}
        
        suggestions = await search_service._generate_search_suggestions(sample_search_criteria, response)
        
        assert len(suggestions) == 3
        assert any("age range" in suggestion.lower() for suggestion in suggestions)
        assert any("radius" in suggestion.lower() for suggestion in suggestions)
        assert any("filters" in suggestion.lower() for suggestion in suggestions)
    @pytest.mark.asyncio
    async def test_generate_search_suggestions_few_results(self, search_service, sample_search_criteria):
        """Test search suggestions when few results"""
        response = {"hits": {"total": {"value": 3}}}
        
        suggestions = await search_service._generate_search_suggestions(sample_search_criteria, response)
        
        assert len(suggestions) == 3
        assert any("interests" in suggestion.lower() for suggestion in suggestions)
        assert any("profile" in suggestion.lower() for suggestion in suggestions)
    @pytest.mark.asyncio
    async def test_track_search_analytics(self, search_service, mock_redis, sample_search_criteria):
        """Test search analytics tracking"""
        response = SearchResponse(
            results=[], total_count=150, page=0, size=20, took_ms=45, search_id="test_123"
        )
        
        await search_service._track_search_analytics(100, sample_search_criteria, response)
        
        mock_redis.lpush.assert_called_once()
        mock_redis.ltrim.assert_called_once_with('search_analytics', 0, 9999)
        
        # Check analytics data structure
        analytics_data = json.loads(mock_redis.lpush.call_args[0][1])
        assert analytics_data['searcher_id'] == 100
        assert analytics_data['search_type'] == sample_search_criteria.search_type.value
        assert analytics_data['results_count'] == 150
    @pytest.mark.asyncio
    async def test_index_user_success(self, search_service, mock_elasticsearch):
        """Test successful user indexing"""
        user_data = {"user_id": 123, "username": "test_user", "age": 25}
        mock_elasticsearch.index.return_value = {"result": "created"}
        
        result = await search_service.index_user(user_data)
        
        assert result is True
        mock_elasticsearch.index.assert_called_once_with(
            index=search_service.indexes['users'],
            id=123,
            body=user_data
        )
    @pytest.mark.asyncio
    async def test_index_user_error(self, search_service, mock_elasticsearch):
        """Test user indexing error handling"""
        user_data = {"user_id": 123, "username": "test_user"}
        mock_elasticsearch.index.side_effect = Exception("Indexing error")
        
        result = await search_service.index_user(user_data)
        
        assert result is False
    @pytest.mark.asyncio
    async def test_index_profile_success(self, search_service, mock_elasticsearch):
        """Test successful profile indexing"""
        profile_data = {"user_id": 123, "bio": "Adventure seeker", "interests": ["travel"]}
        mock_elasticsearch.index.return_value = {"result": "created"}
        
        result = await search_service.index_profile(profile_data)
        
        assert result is True
        mock_elasticsearch.index.assert_called_once_with(
            index=search_service.indexes['profiles'],
            id=123,
            body=profile_data
        )
    @pytest.mark.asyncio
    async def test_delete_user_success(self, search_service, mock_elasticsearch):
        """Test successful user deletion"""
        mock_elasticsearch.delete.return_value = {"result": "deleted"}
        
        result = await search_service.delete_user(123)
        
        assert result is True
        # Should delete from all indexes
        assert mock_elasticsearch.delete.call_count == 3
    @pytest.mark.asyncio
    async def test_delete_user_error(self, search_service, mock_elasticsearch):
        """Test user deletion error handling"""
        mock_elasticsearch.delete.side_effect = Exception("Deletion error")
        
        result = await search_service.delete_user(123)
        
        assert result is False
    @pytest.mark.asyncio
    async def test_bulk_index_users_success(self, search_service):
        """Test successful bulk user indexing"""
        users_data = [
            {"user_id": 123, "username": "user1"},
            {"user_id": 456, "username": "user2"}
        ]
        
        with patch('app.services.search_service.async_bulk') as mock_bulk:
            mock_bulk.return_value = (2, [])
            
            result = await search_service.bulk_index_users(users_data)
            
            assert result is True
            mock_bulk.assert_called_once()
            actions = mock_bulk.call_args[0][1]
            assert len(actions) == 2
            assert actions[0]["_id"] == 123
            assert actions[1]["_id"] == 456
    @pytest.mark.asyncio
    async def test_bulk_index_users_error(self, search_service):
        """Test bulk user indexing error handling"""
        users_data = [{"user_id": 123, "username": "user1"}]
        
        with patch('app.services.search_service.async_bulk', side_effect=Exception("Bulk error")):
            result = await search_service.bulk_index_users(users_data)
            
            assert result is False
    @pytest.mark.asyncio
    async def test_get_search_suggestions_success(self, search_service, mock_elasticsearch):
        """Test getting search suggestions"""
        mock_response = {
            "suggest": {
                "user_suggest": [{
                    "options": [
                        {"text": "travel"},
                        {"text": "traveler"},
                        {"text": "adventure"}
                    ]
                }]
            }
        }
        mock_elasticsearch.search.return_value = mock_response
        
        suggestions = await search_service.get_search_suggestions("trav", 3)
        
        assert len(suggestions) == 3
        assert "travel" in suggestions
        assert "traveler" in suggestions
        assert "adventure" in suggestions
    @pytest.mark.asyncio
    async def test_get_search_suggestions_error(self, search_service, mock_elasticsearch):
        """Test search suggestions error handling"""
        mock_elasticsearch.search.side_effect = Exception("Suggestions error")
        
        suggestions = await search_service.get_search_suggestions("test")
        
        assert suggestions == []
    @pytest.mark.asyncio
    async def test_get_search_analytics_success(self, search_service, mock_redis):
        """Test getting search analytics"""
        analytics_data = [
            json.dumps({"search_type": "profile_discovery", "results_count": 50, "search_time_ms": 100}),
            json.dumps({"search_type": "interest_based", "results_count": 30, "search_time_ms": 80}),
            json.dumps({"search_type": "profile_discovery", "results_count": 40, "search_time_ms": 90})
        ]
        mock_redis.lrange.return_value = analytics_data
        
        analytics = await search_service.get_search_analytics()
        
        assert analytics['total_searches'] == 3
        assert analytics['search_types']['profile_discovery'] == 2
        assert analytics['search_types']['interest_based'] == 1
        assert analytics['avg_results'] == 40  # (50+30+40)/3
        assert analytics['avg_search_time_ms'] == 90  # (100+80+90)/3
    @pytest.mark.asyncio
    async def test_get_search_analytics_no_data(self, search_service, mock_redis):
        """Test getting search analytics with no data"""
        mock_redis.lrange.return_value = []
        
        analytics = await search_service.get_search_analytics()
        
        assert analytics == {}
    @pytest.mark.asyncio
    async def test_get_search_analytics_error(self, search_service, mock_redis):
        """Test search analytics error handling"""
        mock_redis.lrange.side_effect = Exception("Analytics error")
        
        analytics = await search_service.get_search_analytics()
        
        assert analytics == {}
    @pytest.mark.asyncio
    async def test_concurrent_search_operations(self, search_service, sample_search_criteria):
        """Test concurrent search operations"""
        with patch.object(search_service, 'search_users') as mock_search:
            mock_search.return_value = SearchResponse(
                results=[], total_count=10, page=0, size=20, took_ms=50, search_id="concurrent"
            )
            
            # Simulate concurrent searches
            tasks = []
            for i in range(5):
                task = search_service.search_users(100 + i, sample_search_criteria)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert all(isinstance(result, SearchResponse) for result in results)
            assert mock_search.call_count == 5
    @pytest.mark.asyncio
    async def test_complex_search_scenario(self, search_service, sample_search_response):
        """Test complex search scenario with all features"""
        criteria = SearchCriteria(
            search_type=SearchType.COMPATIBILITY_SEARCH,
            query="adventure travel photography",
            filters={
                "gender": "female",
                "verified_only": True,
                "has_photos": True,
                "min_profile_completeness": 0.8
            },
            location=(37.7749, -122.4194),
            radius_km=25,
            age_range=(25, 35),
            interests=["travel", "photography", "hiking"],
            sort_by=SortOrder.COMPATIBILITY_SCORE,
            page=0,
            size=20
        )
        
        with patch.object(search_service, '_get_cached_search', return_value=None):
            with patch.object(search_service, '_get_user_profile', return_value={"age": 30, "interests": ["travel"]}):
                with patch.object(search_service, '_calculate_compatibility_score', return_value=0.88):
                    search_service.es_client.search.return_value = sample_search_response
                    
                    result = await search_service.search_users(100, criteria)
                    
                    assert isinstance(result, SearchResponse)
                    assert result.total_count == 150
                    assert len(result.results) == 2
                    assert all(r.compatibility_score is not None for r in result.results)
    def test_search_service_singleton_pattern(self):
        """Test search service singleton pattern"""
        from app.services.search_service import get_search_service, init_search_service
        
        # Should raise error if not initialized
        with pytest.raises(RuntimeError, match="Search service not initialized"):
            get_search_service()
        
        # Initialize service
        mock_es = AsyncMock()
        mock_redis = Mock()
        
        with patch.object(ElasticsearchService, '_setup_indexes'):
            service = init_search_service(mock_es, mock_redis)
            
            # Get service should return same instance
            retrieved_service = get_search_service()
            assert service is retrieved_service
    def test_location_distance_calculation(self, search_service, sample_search_criteria, sample_search_response):
        """Test location distance calculation accuracy"""
        with patch.object(search_service, '_calculate_compatibility_score', return_value=0.85):
            with patch.object(search_service, '_generate_match_reasons', return_value=["Test reason"]):
                # Mock geopy distance calculation
                with patch('geopy.distance.distance') as mock_distance:
                    mock_distance.return_value.kilometers = 5.7
                    
                    results = asyncio.run(
                        search_service._process_search_results(
                            100, sample_search_response, sample_search_criteria
                        )
                    )
                    
                    assert results[0].distance_km == 5.7
                    mock_distance.assert_called()
    def test_search_performance_optimization(self, search_service):
        """Test search performance optimization features"""
        # Test boost factors are reasonable
        boost_factors = search_service.search_configs['boost_factors']
        
        # Mutual interests should have highest boost (most important for dating)
        assert boost_factors['mutual_interests'] == max(boost_factors.values())
        
        # All boost factors should be positive
        assert all(factor > 0 for factor in boost_factors.values())
        
        # Cache TTL should be reasonable (not too short or too long)
        assert 60 <= search_service.search_configs['cache_ttl'] <= 3600