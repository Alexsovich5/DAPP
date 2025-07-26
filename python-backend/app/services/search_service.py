# Advanced Search Service for Dinner First
# Elasticsearch-powered search with intelligent matching and recommendation algorithms

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import logging
import json
import asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
import redis
import geopy.distance
from geopy import Point

logger = logging.getLogger(__name__)

class SearchType(Enum):
    PROFILE_DISCOVERY = "profile_discovery"
    COMPATIBILITY_SEARCH = "compatibility_search"
    INTEREST_BASED = "interest_based"
    LOCATION_BASED = "location_based"
    KEYWORD_SEARCH = "keyword_search"
    ADVANCED_FILTERS = "advanced_filters"

class SortOrder(Enum):
    RELEVANCE = "relevance"
    COMPATIBILITY_SCORE = "compatibility_score"
    DISTANCE = "distance"
    LAST_ACTIVE = "last_active"
    NEWEST_FIRST = "newest_first"
    RANDOM = "random"

@dataclass
class SearchCriteria:
    search_type: SearchType
    query: Optional[str] = None
    filters: Dict[str, Any] = None
    location: Optional[Tuple[float, float]] = None  # (lat, lon)
    radius_km: Optional[int] = None
    age_range: Optional[Tuple[int, int]] = None
    interests: Optional[List[str]] = None
    sort_by: SortOrder = SortOrder.RELEVANCE
    page: int = 0
    size: int = 20
    include_hidden: bool = False

@dataclass
class SearchResult:
    user_id: int
    score: float
    compatibility_score: Optional[float]
    distance_km: Optional[float]
    match_reasons: List[str]
    profile_data: Dict[str, Any]
    last_active: datetime

@dataclass
class SearchResponse:
    results: List[SearchResult]
    total_count: int
    page: int
    size: int
    took_ms: int
    search_id: str
    suggestions: List[str] = None

class ElasticsearchService:
    """
    Advanced Elasticsearch service for dating platform search and discovery
    """
    
    def __init__(self, elasticsearch_client: AsyncElasticsearch, redis_client: redis.Redis):
        self.es_client = elasticsearch_client
        self.redis_client = redis_client
        
        # Index configurations
        self.indexes = {
            'users': 'dinner_first_users',
            'profiles': 'dinner_first_profiles',
            'activities': 'dinner_first_activities'
        }
        
        # Search configurations for dating platform
        self.search_configs = {
            'default_radius_km': 50,
            'max_results': 100,
            'cache_ttl': 300,  # 5 minutes
            'min_compatibility_score': 0.3,
            'boost_factors': {
                'recent_activity': 2.0,
                'profile_completeness': 1.5,
                'mutual_interests': 3.0,
                'location_proximity': 1.8,
                'age_compatibility': 1.2
            }
        }
        
        # Initialize indexes
        asyncio.create_task(self._setup_indexes())
    
    async def _setup_indexes(self):
        """Setup Elasticsearch indexes with optimized mappings for dating platform"""
        try:
            await self._create_users_index()
            await self._create_profiles_index()
            await self._create_activities_index()
            logger.info("Elasticsearch indexes initialized successfully")
        except Exception as e:
            logger.error(f"Failed to setup Elasticsearch indexes: {e}")
    
    async def _create_users_index(self):
        """Create users index with optimized mapping"""
        mapping = {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {
                        "dating_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop", "snowball"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "user_id": {"type": "integer"},
                    "username": {
                        "type": "text",
                        "analyzer": "dating_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "first_name": {
                        "type": "text",
                        "analyzer": "dating_analyzer"
                    },
                    "age": {"type": "integer"},
                    "gender": {"type": "keyword"},
                    "location": {"type": "geo_point"},
                    "city": {"type": "keyword"},
                    "last_active": {"type": "date"},
                    "created_at": {"type": "date"},
                    "is_active": {"type": "boolean"},
                    "is_premium": {"type": "boolean"},
                    "profile_completeness": {"type": "float"},
                    "verification_status": {"type": "keyword"},
                    "photo_count": {"type": "integer"},
                    "soul_profile_visibility": {"type": "keyword"},
                    "emotional_depth_score": {"type": "float"}
                }
            }
        }
        
        try:
            await self.es_client.indices.create(
                index=self.indexes['users'],
                body=mapping,
                ignore=400  # Ignore if index already exists
            )
        except Exception as e:
            logger.warning(f"Users index creation warning: {e}")
    
    async def _create_profiles_index(self):
        """Create profiles index for detailed search"""
        mapping = {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {
                        "profile_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop", "snowball", "synonym"]
                        }
                    },
                    "filter": {
                        "synonym": {
                            "type": "synonym",
                            "synonyms": [
                                "travel,adventure,explore",
                                "fitness,gym,workout,exercise",
                                "music,singing,dancing",
                                "food,cooking,culinary,dining",
                                "books,reading,literature",
                                "movies,films,cinema",
                                "art,creative,artistic,design"
                            ]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "user_id": {"type": "integer"},
                    "bio": {
                        "type": "text",
                        "analyzer": "profile_analyzer"
                    },
                    "life_philosophy": {
                        "type": "text",
                        "analyzer": "profile_analyzer"
                    },
                    "interests": {
                        "type": "text",
                        "analyzer": "profile_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "core_values": {
                        "type": "nested",
                        "properties": {
                            "category": {"type": "keyword"},
                            "value": {"type": "text"},
                            "importance": {"type": "float"}
                        }
                    },
                    "personality_traits": {
                        "type": "nested",
                        "properties": {
                            "trait": {"type": "keyword"},
                            "score": {"type": "float"}
                        }
                    },
                    "communication_style": {
                        "type": "object",
                        "properties": {
                            "style": {"type": "keyword"},
                            "preference": {"type": "float"}
                        }
                    },
                    "relationship_goals": {"type": "keyword"},
                    "education_level": {"type": "keyword"},
                    "profession": {"type": "text"},
                    "lifestyle": {"type": "keyword"},
                    "languages": {"type": "keyword"},
                    "smoking": {"type": "keyword"},
                    "drinking": {"type": "keyword"},
                    "religion": {"type": "keyword"},
                    "updated_at": {"type": "date"}
                }
            }
        }
        
        try:
            await self.es_client.indices.create(
                index=self.indexes['profiles'],
                body=mapping,
                ignore=400
            )
        except Exception as e:
            logger.warning(f"Profiles index creation warning: {e}")
    
    async def _create_activities_index(self):
        """Create activities index for behavioral search"""
        mapping = {
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "user_id": {"type": "integer"},
                    "activity_type": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "interaction_score": {"type": "float"},
                    "engagement_level": {"type": "keyword"},
                    "location": {"type": "geo_point"},
                    "metadata": {"type": "object"}
                }
            }
        }
        
        try:
            await self.es_client.indices.create(
                index=self.indexes['activities'],
                body=mapping,
                ignore=400
            )
        except Exception as e:
            logger.warning(f"Activities index creation warning: {e}")
    
    async def search_users(self, searcher_id: int, criteria: SearchCriteria) -> SearchResponse:
        """
        Advanced user search with multiple algorithms and personalization
        """
        try:
            search_start_time = datetime.now()
            
            # Generate cache key
            cache_key = self._generate_cache_key(searcher_id, criteria)
            
            # Try cache first
            cached_result = await self._get_cached_search(cache_key)
            if cached_result:
                return cached_result
            
            # Build Elasticsearch query
            query = await self._build_search_query(searcher_id, criteria)
            
            # Execute search
            response = await self.es_client.search(
                index=self.indexes['users'],
                body=query,
                size=criteria.size,
                from_=criteria.page * criteria.size
            )
            
            # Process results
            search_results = await self._process_search_results(
                searcher_id, response, criteria
            )
            
            # Calculate search time
            search_time = (datetime.now() - search_start_time).total_seconds() * 1000
            
            # Create response
            search_response = SearchResponse(
                results=search_results,
                total_count=response['hits']['total']['value'],
                page=criteria.page,
                size=criteria.size,
                took_ms=int(search_time),
                search_id=self._generate_search_id(),
                suggestions=await self._generate_search_suggestions(criteria, response)
            )
            
            # Cache results
            await self._cache_search_results(cache_key, search_response)
            
            # Track search analytics
            await self._track_search_analytics(searcher_id, criteria, search_response)
            
            return search_response
            
        except Exception as e:
            logger.error(f"Search failed for user {searcher_id}: {e}")
            return SearchResponse(
                results=[],
                total_count=0,
                page=0,
                size=0,
                took_ms=0,
                search_id="error"
            )
    
    async def _build_search_query(self, searcher_id: int, criteria: SearchCriteria) -> Dict[str, Any]:
        """Build optimized Elasticsearch query for dating platform"""
        
        # Get searcher profile for personalization
        searcher_profile = await self._get_user_profile(searcher_id)
        
        # Base query structure
        query = {
            "query": {
                "bool": {
                    "must": [],
                    "must_not": [],
                    "should": [],
                    "filter": []
                }
            },
            "sort": [],
            "_source": {
                "includes": [
                    "user_id", "username", "first_name", "age", "gender",
                    "location", "city", "last_active", "profile_completeness",
                    "photo_count", "emotional_depth_score"
                ]
            }
        }
        
        # Basic filters
        query["query"]["bool"]["filter"].extend([
            {"term": {"is_active": True}},
            {"range": {"last_active": {"gte": "now-30d"}}},  # Active in last 30 days
        ])
        
        # Exclude searcher from results
        query["query"]["bool"]["must_not"].append(
            {"term": {"user_id": searcher_id}}
        )
        
        # Age range filter
        if criteria.age_range:
            query["query"]["bool"]["filter"].append({
                "range": {
                    "age": {
                        "gte": criteria.age_range[0],
                        "lte": criteria.age_range[1]
                    }
                }
            })
        
        # Location-based search
        if criteria.location:
            radius = criteria.radius_km or self.search_configs['default_radius_km']
            query["query"]["bool"]["filter"].append({
                "geo_distance": {
                    "distance": f"{radius}km",
                    "location": {
                        "lat": criteria.location[0],
                        "lon": criteria.location[1]
                    }
                }
            })
        
        # Search type specific queries
        if criteria.search_type == SearchType.KEYWORD_SEARCH and criteria.query:
            query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": criteria.query,
                    "fields": [
                        "username^2",
                        "first_name^2",
                        "bio^1.5",
                        "interests^3"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        elif criteria.search_type == SearchType.INTEREST_BASED and criteria.interests:
            query["query"]["bool"]["should"].extend([
                {
                    "terms": {
                        "interests.keyword": criteria.interests,
                        "boost": self.search_configs['boost_factors']['mutual_interests']
                    }
                }
            ])
        
        elif criteria.search_type == SearchType.COMPATIBILITY_SEARCH:
            # Add compatibility boosting based on searcher profile
            await self._add_compatibility_boosting(query, searcher_profile)
        
        # Additional filters
        if criteria.filters:
            await self._apply_advanced_filters(query, criteria.filters)
        
        # Sorting
        await self._apply_sorting(query, criteria)
        
        # Add function score for advanced relevance
        query = await self._wrap_with_function_score(query, searcher_profile, criteria)
        
        return query
    
    async def _add_compatibility_boosting(self, query: Dict, searcher_profile: Dict):
        """Add compatibility-based boosting to query"""
        if not searcher_profile:
            return
        
        # Boost users with similar interests
        if searcher_profile.get('interests'):
            query["query"]["bool"]["should"].append({
                "terms": {
                    "interests.keyword": searcher_profile['interests'],
                    "boost": 2.0
                }
            })
        
        # Boost users with compatible personality traits
        if searcher_profile.get('personality_traits'):
            compatible_traits = self._get_compatible_traits(
                searcher_profile['personality_traits']
            )
            for trait, boost in compatible_traits.items():
                query["query"]["bool"]["should"].append({
                    "nested": {
                        "path": "personality_traits",
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {"personality_traits.trait": trait}},
                                    {"range": {"personality_traits.score": {"gte": 0.6}}}
                                ]
                            }
                        },
                        "boost": boost
                    }
                })
    
    async def _apply_advanced_filters(self, query: Dict, filters: Dict[str, Any]):
        """Apply advanced filtering options"""
        
        # Gender preference
        if 'gender' in filters:
            query["query"]["bool"]["filter"].append({
                "term": {"gender": filters['gender']}
            })
        
        # Education level
        if 'education_level' in filters:
            query["query"]["bool"]["filter"].append({
                "term": {"education_level": filters['education_level']}
            })
        
        # Verification status
        if 'verified_only' in filters and filters['verified_only']:
            query["query"]["bool"]["filter"].append({
                "term": {"verification_status": "verified"}
            })
        
        # Photo requirement
        if 'has_photos' in filters and filters['has_photos']:
            query["query"]["bool"]["filter"].append({
                "range": {"photo_count": {"gte": 1}}
            })
        
        # Premium users only
        if 'premium_only' in filters and filters['premium_only']:
            query["query"]["bool"]["filter"].append({
                "term": {"is_premium": True}
            })
        
        # Profile completeness threshold
        if 'min_profile_completeness' in filters:
            query["query"]["bool"]["filter"].append({
                "range": {
                    "profile_completeness": {"gte": filters['min_profile_completeness']}
                }
            })
    
    async def _apply_sorting(self, query: Dict, criteria: SearchCriteria):
        """Apply sorting based on search criteria"""
        
        if criteria.sort_by == SortOrder.COMPATIBILITY_SCORE:
            query["sort"] = [
                {"emotional_depth_score": {"order": "desc"}},
                {"profile_completeness": {"order": "desc"}},
                "_score"
            ]
        
        elif criteria.sort_by == SortOrder.DISTANCE and criteria.location:
            query["sort"] = [
                {
                    "_geo_distance": {
                        "location": {
                            "lat": criteria.location[0],
                            "lon": criteria.location[1]
                        },
                        "order": "asc",
                        "unit": "km"
                    }
                }
            ]
        
        elif criteria.sort_by == SortOrder.LAST_ACTIVE:
            query["sort"] = [
                {"last_active": {"order": "desc"}},
                "_score"
            ]
        
        elif criteria.sort_by == SortOrder.NEWEST_FIRST:
            query["sort"] = [
                {"created_at": {"order": "desc"}},
                "_score"
            ]
        
        elif criteria.sort_by == SortOrder.RANDOM:
            query["sort"] = [
                {
                    "_script": {
                        "type": "number",
                        "script": {
                            "source": "Math.random()"
                        }
                    }
                }
            ]
        
        else:  # RELEVANCE
            query["sort"] = ["_score"]
    
    async def _wrap_with_function_score(self, query: Dict, searcher_profile: Dict, 
                                      criteria: SearchCriteria) -> Dict[str, Any]:
        """Wrap query with function score for advanced relevance"""
        
        functions = []
        
        # Boost recent activity
        functions.append({
            "gauss": {
                "last_active": {
                    "origin": "now",
                    "scale": "7d",
                    "offset": "1d",
                    "decay": 0.5
                }
            },
            "weight": self.search_configs['boost_factors']['recent_activity']
        })
        
        # Boost profile completeness
        functions.append({
            "field_value_factor": {
                "field": "profile_completeness",
                "factor": self.search_configs['boost_factors']['profile_completeness'],
                "modifier": "sqrt",
                "missing": 0.1
            }
        })
        
        # Distance-based boosting
        if criteria.location:
            functions.append({
                "gauss": {
                    "location": {
                        "origin": {
                            "lat": criteria.location[0],
                            "lon": criteria.location[1]
                        },
                        "scale": "10km",
                        "offset": "2km",
                        "decay": 0.33
                    }
                },
                "weight": self.search_configs['boost_factors']['location_proximity']
            })
        
        # Age compatibility boosting
        if searcher_profile and searcher_profile.get('age'):
            searcher_age = searcher_profile['age']
            functions.append({
                "gauss": {
                    "age": {
                        "origin": searcher_age,
                        "scale": "5",
                        "offset": "2",
                        "decay": 0.5
                    }
                },
                "weight": self.search_configs['boost_factors']['age_compatibility']
            })
        
        return {
            "query": {
                "function_score": {
                    "query": query["query"],
                    "functions": functions,
                    "score_mode": "multiply",
                    "boost_mode": "multiply",
                    "min_score": 0.1
                }
            },
            "sort": query.get("sort", ["_score"]),
            "_source": query.get("_source")
        }
    
    async def _process_search_results(self, searcher_id: int, response: Dict, 
                                    criteria: SearchCriteria) -> List[SearchResult]:
        """Process Elasticsearch response into SearchResult objects"""
        
        results = []
        searcher_location = criteria.location
        
        for hit in response['hits']['hits']:
            source = hit['_source']
            
            # Calculate distance if location available
            distance_km = None
            if searcher_location and source.get('location'):
                try:
                    searcher_point = Point(searcher_location[0], searcher_location[1])
                    user_point = Point(source['location']['lat'], source['location']['lon'])
                    distance_km = round(geopy.distance.distance(searcher_point, user_point).kilometers, 1)
                except Exception as e:
                    logger.warning(f"Distance calculation error: {e}")
            
            # Generate match reasons
            match_reasons = self._generate_match_reasons(hit, criteria)
            
            # Calculate compatibility score (simplified)
            compatibility_score = await self._calculate_compatibility_score(
                searcher_id, source['user_id']
            )
            
            result = SearchResult(
                user_id=source['user_id'],
                score=hit['_score'],
                compatibility_score=compatibility_score,
                distance_km=distance_km,
                match_reasons=match_reasons,
                profile_data=source,
                last_active=datetime.fromisoformat(source['last_active'].replace('Z', '+00:00'))
            )
            
            results.append(result)
        
        return results
    
    def _generate_match_reasons(self, hit: Dict, criteria: SearchCriteria) -> List[str]:
        """Generate human-readable match reasons"""
        reasons = []
        source = hit['_source']
        
        # High compatibility score
        if source.get('emotional_depth_score', 0) > 0.8:
            reasons.append("High emotional compatibility")
        
        # Recent activity
        last_active = datetime.fromisoformat(source['last_active'].replace('Z', '+00:00'))
        if (datetime.now(last_active.tzinfo) - last_active).days < 3:
            reasons.append("Recently active")
        
        # Complete profile
        if source.get('profile_completeness', 0) > 0.9:
            reasons.append("Complete profile")
        
        # Verified user
        if source.get('verification_status') == 'verified':
            reasons.append("Verified profile")
        
        # Multiple photos
        if source.get('photo_count', 0) >= 3:
            reasons.append("Multiple photos")
        
        # Location proximity (if applicable)
        if criteria.location and 'sort' in hit and hit['sort']:
            try:
                distance = hit['sort'][0]
                if distance < 10:
                    reasons.append("Lives nearby")
            except (IndexError, TypeError):
                pass
        
        return reasons[:3]  # Limit to top 3 reasons
    
    async def _calculate_compatibility_score(self, user1_id: int, user2_id: int) -> Optional[float]:
        """Calculate compatibility score between two users"""
        try:
            # This would use the existing compatibility calculation service
            # For now, return a mock score
            cache_key = f"compatibility:{min(user1_id, user2_id)}:{max(user1_id, user2_id)}"
            
            cached_score = self.redis_client.get(cache_key)
            if cached_score:
                return float(cached_score)
            
            # Mock compatibility calculation
            import random
            score = random.uniform(0.3, 0.95)
            
            # Cache for 1 hour
            self.redis_client.set(cache_key, str(score), ex=3600)
            
            return score
            
        except Exception as e:
            logger.error(f"Compatibility calculation error: {e}")
            return None
    
    def _get_compatible_traits(self, personality_traits: Dict) -> Dict[str, float]:
        """Get compatible personality traits with boost values"""
        # Simplified compatibility mapping
        compatible_traits = {
            'outgoing': 1.5,
            'adventurous': 1.3,
            'intellectual': 1.4,
            'creative': 1.2,
            'empathetic': 1.6
        }
        
        return compatible_traits
    
    async def _get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get user profile for personalization"""
        try:
            # This would fetch from the profiles index
            response = await self.es_client.get(
                index=self.indexes['profiles'],
                id=user_id,
                ignore=404
            )
            
            if response['found']:
                return response['_source']
            
        except Exception as e:
            logger.warning(f"Failed to get user profile {user_id}: {e}")
        
        return None
    
    def _generate_cache_key(self, searcher_id: int, criteria: SearchCriteria) -> str:
        """Generate cache key for search results"""
        import hashlib
        
        criteria_str = json.dumps(asdict(criteria), sort_keys=True, default=str)
        criteria_hash = hashlib.md5(criteria_str.encode()).hexdigest()[:16]
        
        return f"search:{searcher_id}:{criteria_hash}"
    
    async def _get_cached_search(self, cache_key: str) -> Optional[SearchResponse]:
        """Get cached search results"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # Reconstruct SearchResponse object
                return SearchResponse(**data)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        
        return None
    
    async def _cache_search_results(self, cache_key: str, response: SearchResponse):
        """Cache search results"""
        try:
            data = asdict(response)
            self.redis_client.set(
                cache_key,
                json.dumps(data, default=str),
                ex=self.search_configs['cache_ttl']
            )
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    def _generate_search_id(self) -> str:
        """Generate unique search ID for tracking"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    async def _generate_search_suggestions(self, criteria: SearchCriteria, 
                                         response: Dict) -> List[str]:
        """Generate search suggestions based on results"""
        suggestions = []
        
        # If no results, suggest expanding search
        if response['hits']['total']['value'] == 0:
            suggestions.extend([
                "Try expanding your age range",
                "Consider increasing your search radius",
                "Remove some filters to see more matches"
            ])
        
        # If few results, suggest improvements
        elif response['hits']['total']['value'] < 5:
            suggestions.extend([
                "Add more interests to your profile for better matches",
                "Complete your profile to attract more users",
                "Try searching at different times of day"
            ])
        
        return suggestions[:3]
    
    async def _track_search_analytics(self, searcher_id: int, criteria: SearchCriteria, 
                                    response: SearchResponse):
        """Track search analytics for optimization"""
        try:
            analytics_data = {
                'searcher_id': searcher_id,
                'search_type': criteria.search_type.value,
                'results_count': response.total_count,
                'search_time_ms': response.took_ms,
                'page': criteria.page,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Store in Redis for real-time analytics
            self.redis_client.lpush(
                'search_analytics',
                json.dumps(analytics_data)
            )
            self.redis_client.ltrim('search_analytics', 0, 9999)
            
        except Exception as e:
            logger.error(f"Search analytics tracking error: {e}")
    
    # Public utility methods
    
    async def index_user(self, user_data: Dict[str, Any]) -> bool:
        """Index or update user in Elasticsearch"""
        try:
            await self.es_client.index(
                index=self.indexes['users'],
                id=user_data['user_id'],
                body=user_data
            )
            return True
        except Exception as e:
            logger.error(f"User indexing error: {e}")
            return False
    
    async def index_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Index or update user profile in Elasticsearch"""
        try:
            await self.es_client.index(
                index=self.indexes['profiles'],
                id=profile_data['user_id'],
                body=profile_data
            )
            return True
        except Exception as e:
            logger.error(f"Profile indexing error: {e}")
            return False
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user from all indexes"""
        try:
            for index in self.indexes.values():
                await self.es_client.delete(
                    index=index,
                    id=user_id,
                    ignore=404
                )
            return True
        except Exception as e:
            logger.error(f"User deletion error: {e}")
            return False
    
    async def bulk_index_users(self, users_data: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple users"""
        try:
            actions = []
            for user_data in users_data:
                actions.append({
                    "_index": self.indexes['users'],
                    "_id": user_data['user_id'],
                    "_source": user_data
                })
            
            await async_bulk(self.es_client, actions)
            return True
        except Exception as e:
            logger.error(f"Bulk indexing error: {e}")
            return False
    
    async def get_search_suggestions(self, query: str, size: int = 5) -> List[str]:
        """Get search suggestions based on partial query"""
        try:
            response = await self.es_client.search(
                index=self.indexes['users'],
                body={
                    "suggest": {
                        "user_suggest": {
                            "prefix": query,
                            "completion": {
                                "field": "username.suggest",
                                "size": size
                            }
                        }
                    }
                }
            )
            
            suggestions = []
            for option in response['suggest']['user_suggest'][0]['options']:
                suggestions.append(option['text'])
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Search suggestions error: {e}")
            return []
    
    async def get_search_analytics(self) -> Dict[str, Any]:
        """Get search analytics and performance metrics"""
        try:
            # Get recent search analytics
            analytics_data = self.redis_client.lrange('search_analytics', 0, 999)
            
            total_searches = len(analytics_data)
            if total_searches == 0:
                return {}
            
            # Process analytics
            search_types = {}
            avg_results = 0
            avg_time = 0
            
            for data_str in analytics_data:
                data = json.loads(data_str)
                search_type = data['search_type']
                search_types[search_type] = search_types.get(search_type, 0) + 1
                avg_results += data['results_count']
                avg_time += data['search_time_ms']
            
            return {
                'total_searches': total_searches,
                'search_types': search_types,
                'avg_results': avg_results / total_searches,
                'avg_search_time_ms': avg_time / total_searches,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Search analytics error: {e}")
            return {}

# Global search service instance
_search_service: Optional[ElasticsearchService] = None

def get_search_service() -> ElasticsearchService:
    """Get global search service instance"""
    global _search_service
    if _search_service is None:
        raise RuntimeError("Search service not initialized")
    return _search_service

def init_search_service(elasticsearch_client: AsyncElasticsearch, 
                       redis_client: redis.Redis) -> ElasticsearchService:
    """Initialize global search service"""
    global _search_service
    _search_service = ElasticsearchService(elasticsearch_client, redis_client)
    return _search_service