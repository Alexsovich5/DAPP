"""
Optimized Discovery Service - High-Performance User Matching
Implements cached and indexed discovery queries for improved performance
"""

import logging
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text
from sqlalchemy.sql import select

from app.models.user import User
from app.models.profile import Profile
from app.models.soul_connection import SoulConnection
from app.services.compatibility import CompatibilityCalculator

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryResult:
    """Optimized discovery result with caching metadata"""
    users: List[Dict[str, Any]]
    total_count: int
    processing_time_ms: float
    cache_hit: bool
    query_optimization_applied: bool


@dataclass
class DiscoveryFilters:
    """Structured discovery filters for optimization"""
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    location: Optional[str] = None
    min_compatibility: float = 50.0
    max_distance_km: Optional[float] = None
    interests: Optional[List[str]] = None
    exclude_user_ids: Optional[List[int]] = None


class OptimizedDiscoveryService:
    """High-performance discovery service with caching and optimization"""
    
    def __init__(self):
        self.calculator = CompatibilityCalculator()
        self.cache = {}  # In-memory cache for development
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 1000
        
    def discover_users(
        self, 
        db: Session, 
        current_user: User, 
        filters: DiscoveryFilters,
        limit: int = 20,
        offset: int = 0
    ) -> DiscoveryResult:
        """
        Optimized user discovery with caching and performance monitoring
        """
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(current_user.id, filters, limit, offset)
        
        # Check cache first
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return DiscoveryResult(
                users=cached_result['users'],
                total_count=cached_result['total_count'],
                processing_time_ms=(time.time() - start_time) * 1000,
                cache_hit=True,
                query_optimization_applied=False
            )
        
        # Execute optimized query
        try:
            result = self._execute_optimized_discovery(db, current_user, filters, limit, offset)
            
            # Cache result
            self._cache_result(cache_key, result)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DiscoveryResult(
                users=result['users'],
                total_count=result['total_count'],
                processing_time_ms=processing_time,
                cache_hit=False,
                query_optimization_applied=True
            )
            
        except Exception as e:
            logger.error(f"Discovery query failed: {str(e)}")
            # Fallback to basic query
            return self._fallback_discovery(db, current_user, filters, limit, offset, start_time)
    
    def _execute_optimized_discovery(
        self, 
        db: Session, 
        current_user: User, 
        filters: DiscoveryFilters,
        limit: int,
        offset: int
    ) -> Dict[str, Any]:
        """Execute optimized discovery query with proper indexing"""
        
        # Build optimized base query using indexes
        base_query = db.query(User).options(
            joinedload(User.profile)  # Eager load profiles to reduce N+1 queries
        )
        
        # Apply indexed filters first (most selective)
        base_query = base_query.filter(
            and_(
                User.id != current_user.id,
                User.is_active == True,
                # Use indexed fields first
                User.is_verified == True  # Assuming verified users are preferred
            )
        )
        
        # Apply age filters using indexed date_of_birth
        if filters.age_min is not None or filters.age_max is not None:
            age_filter = self._build_age_filter(filters.age_min, filters.age_max)
            if age_filter is not None:
                base_query = base_query.filter(age_filter)
        
        # Apply location filter if specified
        if filters.location:
            base_query = base_query.filter(User.location.ilike(f"%{filters.location}%"))
        
        # Exclude users already connected
        existing_connections = db.query(SoulConnection.user1_id, SoulConnection.user2_id).filter(
            or_(
                SoulConnection.user1_id == current_user.id,
                SoulConnection.user2_id == current_user.id
            )
        ).subquery()
        
        base_query = base_query.filter(
            and_(
                User.id.notin_(
                    select([existing_connections.c.user1_id]).where(
                        existing_connections.c.user2_id == current_user.id
                    )
                ),
                User.id.notin_(
                    select([existing_connections.c.user2_id]).where(
                        existing_connections.c.user1_id == current_user.id
                    )
                )
            )
        )
        
        # Order by last active for better matches
        base_query = base_query.order_by(
            User.last_active_at.desc().nullslast(),
            User.created_at.desc()
        )
        
        # Get total count for pagination (optimized count query)
        count_query = base_query.statement.with_only_columns([func.count(User.id)])
        total_count = db.execute(count_query).scalar()
        
        # Apply pagination and get results
        candidates = base_query.offset(offset).limit(limit * 2).all()  # Get extra for compatibility filtering
        
        # Calculate compatibility scores efficiently
        compatible_users = self._calculate_compatibility_batch(
            current_user, candidates, filters.min_compatibility
        )
        
        # Sort by compatibility and apply final limit
        compatible_users.sort(key=lambda x: x['compatibility_score'], reverse=True)
        final_users = compatible_users[:limit]
        
        return {
            'users': final_users,
            'total_count': min(total_count, len(compatible_users)),
            'optimization_applied': True
        }
    
    def _build_age_filter(self, age_min: Optional[int], age_max: Optional[int]):
        """Build optimized age filter using date calculations"""
        current_date = datetime.now().date()
        
        filters = []
        if age_min is not None:
            max_birth_date = current_date.replace(year=current_date.year - age_min)
            filters.append(User.date_of_birth <= max_birth_date)
        
        if age_max is not None:
            min_birth_date = current_date.replace(year=current_date.year - age_max - 1)
            filters.append(User.date_of_birth > min_birth_date)
        
        return and_(*filters) if filters else None
    
    def _calculate_compatibility_batch(
        self, 
        current_user: User, 
        candidates: List[User], 
        min_compatibility: float
    ) -> List[Dict[str, Any]]:
        """Calculate compatibility scores in batch for better performance"""
        
        current_user_data = {
            'interests': current_user.interests or [],
            'core_values': getattr(current_user, 'core_values', {}) or {},
            'age': self._calculate_age(current_user.date_of_birth),
            'location': current_user.location
        }
        
        compatible_users = []
        
        for candidate in candidates:
            candidate_data = {
                'interests': candidate.interests or [],
                'core_values': getattr(candidate, 'core_values', {}) or {},
                'age': self._calculate_age(candidate.date_of_birth),
                'location': candidate.location
            }
            
            # Fast compatibility calculation
            compatibility_result = self.calculator.calculate_overall_compatibility(
                current_user_data, candidate_data
            )
            
            compatibility_score = compatibility_result['total_compatibility']
            
            if compatibility_score >= min_compatibility:
                user_data = {
                    'id': candidate.id,
                    'first_name': candidate.first_name or "Anonymous",
                    'age': candidate_data['age'],
                    'location': candidate.location,
                    'bio': candidate.bio,
                    'interests': candidate.interests or [],
                    'compatibility_score': compatibility_score,
                    'compatibility_breakdown': compatibility_result['breakdown'],
                    'match_quality': compatibility_result['match_quality'],
                    'online_status': self._get_online_status(candidate),
                    'last_active': candidate.last_active_at.isoformat() if candidate.last_active_at else None
                }
                compatible_users.append(user_data)
        
        return compatible_users
    
    def _calculate_age(self, date_of_birth) -> Optional[int]:
        """Calculate age efficiently"""
        if not date_of_birth:
            return None
        return (datetime.now().date() - date_of_birth).days // 365
    
    def _get_online_status(self, user: User) -> str:
        """Determine user online status efficiently"""
        if not user.last_active_at:
            return "offline"
        
        time_diff = datetime.now() - user.last_active_at
        if time_diff.total_seconds() < 300:  # 5 minutes
            return "online"
        elif time_diff.total_seconds() < 3600:  # 1 hour
            return "recently_online"
        else:
            return "offline"
    
    def _generate_cache_key(
        self, 
        user_id: int, 
        filters: DiscoveryFilters, 
        limit: int, 
        offset: int
    ) -> str:
        """Generate cache key for discovery results"""
        filter_str = f"{filters.age_min}-{filters.age_max}-{filters.location}-{filters.min_compatibility}-{limit}-{offset}"
        cache_input = f"discovery:{user_id}:{filter_str}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached discovery result if valid"""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['data']
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache discovery result with TTL"""
        # Simple cache size management
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest entries
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        self.cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }
    
    def _fallback_discovery(
        self, 
        db: Session, 
        current_user: User, 
        filters: DiscoveryFilters,
        limit: int,
        offset: int,
        start_time: float
    ) -> DiscoveryResult:
        """Fallback discovery method for error cases"""
        
        try:
            # Simple query without complex optimizations
            basic_users = db.query(User).filter(
                and_(
                    User.id != current_user.id,
                    User.is_active == True
                )
            ).offset(offset).limit(limit).all()
            
            # Basic compatibility calculation
            results = []
            for user in basic_users:
                results.append({
                    'id': user.id,
                    'first_name': user.first_name or "Anonymous",
                    'age': self._calculate_age(user.date_of_birth),
                    'location': user.location,
                    'bio': user.bio,
                    'interests': user.interests or [],
                    'compatibility_score': 75.0,  # Default score
                    'online_status': "offline"
                })
            
            return DiscoveryResult(
                users=results,
                total_count=len(results),
                processing_time_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                query_optimization_applied=False
            )
            
        except Exception as e:
            logger.error(f"Fallback discovery failed: {str(e)}")
            return DiscoveryResult(
                users=[],
                total_count=0,
                processing_time_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                query_optimization_applied=False
            )
    
    def clear_cache(self):
        """Clear discovery cache"""
        self.cache.clear()
        logger.info("Discovery cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        return {
            "cache_size": len(self.cache),
            "max_cache_size": self.max_cache_size,
            "cache_ttl_seconds": self.cache_ttl,
            "oldest_entry_age": min(
                (time.time() - entry['timestamp'] for entry in self.cache.values()),
                default=0
            ),
            "cache_utilization": len(self.cache) / self.max_cache_size * 100
        }


# Global service instance
optimized_discovery_service = OptimizedDiscoveryService()


def get_optimized_discovery_service() -> OptimizedDiscoveryService:
    """Factory function to get optimized discovery service"""
    return optimized_discovery_service