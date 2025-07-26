# Mobile API Optimization Service for Dinner First
# Optimized responses, compression, and mobile-specific caching for dating platform

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import logging
import json
import gzip
import asyncio
from functools import wraps
import redis
import hashlib
import base64
from PIL import Image
import io

logger = logging.getLogger(__name__)

class MobileDeviceType(Enum):
    IOS = "ios"
    ANDROID = "android"
    MOBILE_WEB = "mobile_web"
    UNKNOWN = "unknown"

class ResponseFormat(Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"

class CompressionType(Enum):
    NONE = "none"
    GZIP = "gzip"
    BROTLI = "brotli"

@dataclass
class MobileClientInfo:
    device_type: MobileDeviceType
    app_version: Optional[str]
    os_version: Optional[str]
    screen_resolution: Optional[str]
    network_type: Optional[str]  # wifi, 4g, 3g, 2g
    data_saver_mode: bool = False

@dataclass
class OptimizationConfig:
    max_image_size: int
    image_quality: int
    response_format: ResponseFormat
    compression_enabled: bool
    cache_ttl: int
    lazy_loading: bool = True

class MobileAPIService:
    """
    Mobile-optimized API service for dating platform with intelligent caching and compression
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        
        # Mobile optimization configurations by device type
        self.device_configs = {
            MobileDeviceType.IOS: OptimizationConfig(
                max_image_size=800,
                image_quality=85,
                response_format=ResponseFormat.STANDARD,
                compression_enabled=True,
                cache_ttl=1800,  # 30 minutes
                lazy_loading=True
            ),
            MobileDeviceType.ANDROID: OptimizationConfig(
                max_image_size=600,
                image_quality=80,
                response_format=ResponseFormat.STANDARD,
                compression_enabled=True,
                cache_ttl=1800,
                lazy_loading=True
            ),
            MobileDeviceType.MOBILE_WEB: OptimizationConfig(
                max_image_size=400,
                image_quality=75,
                response_format=ResponseFormat.MINIMAL,
                compression_enabled=True,
                cache_ttl=900,  # 15 minutes
                lazy_loading=True
            ),
            MobileDeviceType.UNKNOWN: OptimizationConfig(
                max_image_size=400,
                image_quality=70,
                response_format=ResponseFormat.MINIMAL,
                compression_enabled=True,
                cache_ttl=600,  # 10 minutes
                lazy_loading=True
            )
        }
        
        # Network-based optimizations
        self.network_configs = {
            'wifi': {'image_quality_boost': 10, 'cache_ttl_multiplier': 1.5},
            '4g': {'image_quality_boost': 5, 'cache_ttl_multiplier': 1.2},
            '3g': {'image_quality_boost': -10, 'cache_ttl_multiplier': 0.8},
            '2g': {'image_quality_boost': -20, 'cache_ttl_multiplier': 0.5}
        }
        
        # Mobile-specific cache keys
        self.cache_prefixes = {
            'profile': 'mobile:profile:',
            'matches': 'mobile:matches:',
            'photos': 'mobile:photos:',
            'messages': 'mobile:messages:',
            'discovery': 'mobile:discovery:'
        }
    
    def detect_mobile_client(self, user_agent: str, headers: Dict[str, str]) -> MobileClientInfo:
        """Detect mobile client information from request headers"""
        try:
            user_agent_lower = user_agent.lower()
            
            # Detect device type
            device_type = MobileDeviceType.UNKNOWN
            if 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
                device_type = MobileDeviceType.IOS
            elif 'android' in user_agent_lower:
                device_type = MobileDeviceType.ANDROID
            elif 'mobile' in user_agent_lower:
                device_type = MobileDeviceType.MOBILE_WEB
            
            # Extract app version
            app_version = None
            if 'dinner_first/' in user_agent_lower:
                try:
                    app_version = user_agent_lower.split('dinner_first/')[1].split()[0]
                except IndexError:
                    pass
            
            # Extract OS version
            os_version = None
            if device_type == MobileDeviceType.IOS:
                try:
                    os_version = user_agent_lower.split('os ')[1].split()[0].replace('_', '.')
                except IndexError:
                    pass
            elif device_type == MobileDeviceType.ANDROID:
                try:
                    os_version = user_agent_lower.split('android ')[1].split(';')[0]
                except IndexError:
                    pass
            
            # Get additional info from custom headers
            screen_resolution = headers.get('X-Screen-Resolution')
            network_type = headers.get('X-Network-Type', 'unknown').lower()
            data_saver_mode = headers.get('X-Data-Saver', 'false').lower() == 'true'
            
            return MobileClientInfo(
                device_type=device_type,
                app_version=app_version,
                os_version=os_version,
                screen_resolution=screen_resolution,
                network_type=network_type,
                data_saver_mode=data_saver_mode
            )
            
        except Exception as e:
            logger.warning(f"Failed to detect mobile client: {e}")
            return MobileClientInfo(device_type=MobileDeviceType.UNKNOWN)
    
    def get_optimization_config(self, client_info: MobileClientInfo) -> OptimizationConfig:
        """Get optimization configuration based on client info"""
        config = self.device_configs[client_info.device_type]
        
        # Adjust for network conditions
        if client_info.network_type in self.network_configs:
            network_config = self.network_configs[client_info.network_type]
            
            # Adjust image quality based on network
            config.image_quality += network_config['image_quality_boost']
            config.image_quality = max(30, min(95, config.image_quality))
            
            # Adjust cache TTL based on network
            config.cache_ttl = int(config.cache_ttl * network_config['cache_ttl_multiplier'])
        
        # Data saver mode adjustments
        if client_info.data_saver_mode:
            config.image_quality = max(30, config.image_quality - 20)
            config.max_image_size = int(config.max_image_size * 0.7)
            config.response_format = ResponseFormat.MINIMAL
        
        return config
    
    async def optimize_profile_response(self, profile_data: Dict[str, Any], 
                                      client_info: MobileClientInfo) -> Dict[str, Any]:
        """Optimize profile response for mobile clients"""
        try:
            config = self.get_optimization_config(client_info)
            
            # Create cache key
            cache_key = self._generate_profile_cache_key(profile_data['user_id'], client_info, config)
            
            # Try cache first
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
            
            # Optimize profile data based on format
            optimized_data = await self._optimize_profile_data(profile_data, config)
            
            # Optimize images
            if 'photos' in optimized_data:
                optimized_data['photos'] = await self._optimize_photo_urls(
                    optimized_data['photos'], config
                )
            
            # Cache optimized response
            await self._cache_response(cache_key, optimized_data, config.cache_ttl)
            
            return optimized_data
            
        except Exception as e:
            logger.error(f"Profile optimization error: {e}")
            return profile_data  # Return original if optimization fails
    
    async def optimize_matches_response(self, matches_data: List[Dict[str, Any]], 
                                      client_info: MobileClientInfo) -> List[Dict[str, Any]]:
        """Optimize matches response for mobile clients"""
        try:
            config = self.get_optimization_config(client_info)
            
            # Create cache key for matches list
            matches_hash = self._hash_matches_data(matches_data)
            cache_key = f"{self.cache_prefixes['matches']}{matches_hash}:{client_info.device_type.value}"
            
            # Try cache first
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
            
            # Optimize each match
            optimized_matches = []
            for match_data in matches_data:
                optimized_match = await self._optimize_match_data(match_data, config)
                optimized_matches.append(optimized_match)
            
            # Cache optimized matches
            await self._cache_response(cache_key, optimized_matches, config.cache_ttl)
            
            return optimized_matches
            
        except Exception as e:
            logger.error(f"Matches optimization error: {e}")
            return matches_data
    
    async def optimize_discovery_response(self, discovery_data: Dict[str, Any], 
                                        client_info: MobileClientInfo) -> Dict[str, Any]:
        """Optimize discovery/search response for mobile clients"""
        try:
            config = self.get_optimization_config(client_info)
            
            # Optimize users in discovery results
            if 'users' in discovery_data:
                optimized_users = []
                for user in discovery_data['users'][:10]:  # Limit for mobile
                    optimized_user = await self._optimize_discovery_user_data(user, config)
                    optimized_users.append(optimized_user)
                
                discovery_data['users'] = optimized_users
            
            # Add pagination info for mobile
            discovery_data['mobile_pagination'] = {
                'has_more': len(discovery_data.get('users', [])) >= 10,
                'load_more_url': '/api/v1/mobile/discovery/next' if len(discovery_data.get('users', [])) >= 10 else None
            }
            
            return discovery_data
            
        except Exception as e:
            logger.error(f"Discovery optimization error: {e}")
            return discovery_data
    
    async def _optimize_profile_data(self, profile_data: Dict[str, Any], 
                                   config: OptimizationConfig) -> Dict[str, Any]:
        """Optimize profile data based on response format"""
        
        if config.response_format == ResponseFormat.MINIMAL:
            # Minimal format for slow connections
            return {
                'user_id': profile_data['user_id'],
                'first_name': profile_data.get('first_name'),
                'age': profile_data.get('age'),
                'photos': profile_data.get('photos', [])[:2],  # Only first 2 photos
                'bio': self._truncate_text(profile_data.get('bio', ''), 100),
                'distance_km': profile_data.get('distance_km'),
                'last_active': profile_data.get('last_active'),
                'is_online': profile_data.get('is_online', False)
            }
        
        elif config.response_format == ResponseFormat.STANDARD:
            # Standard format with key information
            optimized = profile_data.copy()
            
            # Truncate long text fields
            if 'bio' in optimized:
                optimized['bio'] = self._truncate_text(optimized['bio'], 200)
            
            if 'life_philosophy' in optimized:
                optimized['life_philosophy'] = self._truncate_text(optimized['life_philosophy'], 150)
            
            # Limit arrays
            if 'interests' in optimized:
                optimized['interests'] = optimized['interests'][:6]
            
            if 'photos' in optimized:
                optimized['photos'] = optimized['photos'][:5]
            
            return optimized
        
        else:  # DETAILED
            return profile_data
    
    async def _optimize_match_data(self, match_data: Dict[str, Any], 
                                 config: OptimizationConfig) -> Dict[str, Any]:
        """Optimize individual match data"""
        
        optimized = {
            'match_id': match_data['match_id'],
            'user_id': match_data['user_id'],
            'first_name': match_data.get('first_name'),
            'age': match_data.get('age'),
            'photos': await self._optimize_photo_urls(
                match_data.get('photos', [])[:3], config  # Max 3 photos for matches
            ),
            'compatibility_score': match_data.get('compatibility_score'),
            'distance_km': match_data.get('distance_km'),
            'match_reasons': match_data.get('match_reasons', [])[:2],  # Top 2 reasons
            'last_message': self._optimize_last_message(match_data.get('last_message')),
            'is_online': match_data.get('is_online', False)
        }
        
        # Add preview bio for matches
        if 'bio' in match_data:
            optimized['bio_preview'] = self._truncate_text(match_data['bio'], 80)
        
        return optimized
    
    async def _optimize_discovery_user_data(self, user_data: Dict[str, Any], 
                                          config: OptimizationConfig) -> Dict[str, Any]:
        """Optimize user data for discovery/swipe interface"""
        
        return {
            'user_id': user_data['user_id'],
            'first_name': user_data.get('first_name'),
            'age': user_data.get('age'),
            'photos': await self._optimize_photo_urls(
                user_data.get('photos', [])[:4], config  # Max 4 photos for discovery
            ),
            'bio_preview': self._truncate_text(user_data.get('bio', ''), 60),
            'interests_preview': user_data.get('interests', [])[:3],
            'distance_km': user_data.get('distance_km'),
            'compatibility_score': user_data.get('compatibility_score'),
            'is_verified': user_data.get('is_verified', False),
            'is_premium': user_data.get('is_premium', False),
            'soul_reveal_day': user_data.get('soul_reveal_day', 1)
        }
    
    async def _optimize_photo_urls(self, photos: List[Dict[str, Any]], 
                                 config: OptimizationConfig) -> List[Dict[str, Any]]:
        """Optimize photo URLs with size and quality parameters"""
        
        optimized_photos = []
        for photo in photos:
            if not photo or 'url' not in photo:
                continue
                
            # Generate optimized photo URL with query parameters
            optimized_url = f"{photo['url']}?w={config.max_image_size}&q={config.image_quality}&fm=webp"
            
            optimized_photo = {
                'id': photo.get('id'),
                'url': optimized_url,
                'thumbnail_url': f"{photo['url']}?w=200&q={max(60, config.image_quality-20)}&fm=webp",
                'width': min(photo.get('width', config.max_image_size), config.max_image_size),
                'height': self._calculate_optimized_height(
                    photo.get('width', config.max_image_size),
                    photo.get('height', config.max_image_size),
                    config.max_image_size
                )
            }
            
            # Add lazy loading attributes for mobile
            if config.lazy_loading:
                optimized_photo['lazy_load'] = True
                optimized_photo['placeholder_url'] = f"{photo['url']}?w=50&q=30&fm=webp&blur=20"
            
            optimized_photos.append(optimized_photo)
        
        return optimized_photos
    
    def _calculate_optimized_height(self, original_width: int, original_height: int, 
                                  max_width: int) -> int:
        """Calculate optimized height maintaining aspect ratio"""
        if original_width <= max_width:
            return original_height
        
        aspect_ratio = original_height / original_width
        return int(max_width * aspect_ratio)
    
    def _optimize_last_message(self, last_message: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Optimize last message data for mobile display"""
        if not last_message:
            return None
        
        return {
            'id': last_message.get('id'),
            'preview': self._truncate_text(last_message.get('content', ''), 50),
            'timestamp': last_message.get('timestamp'),
            'sender_id': last_message.get('sender_id'),
            'is_read': last_message.get('is_read', False),
            'message_type': last_message.get('message_type', 'text')
        }
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text with ellipsis"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _generate_profile_cache_key(self, user_id: int, client_info: MobileClientInfo, 
                                  config: OptimizationConfig) -> str:
        """Generate cache key for profile data"""
        key_components = [
            str(user_id),
            client_info.device_type.value,
            config.response_format.value,
            str(config.image_quality),
            str(config.max_image_size)
        ]
        
        key_hash = hashlib.md5(":".join(key_components).encode()).hexdigest()[:12]
        return f"{self.cache_prefixes['profile']}{user_id}:{key_hash}"
    
    def _hash_matches_data(self, matches_data: List[Dict[str, Any]]) -> str:
        """Generate hash for matches data for caching"""
        matches_ids = [str(match.get('match_id', '')) for match in matches_data]
        matches_string = ":".join(sorted(matches_ids))
        return hashlib.md5(matches_string.encode()).hexdigest()[:12]
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                # Check if data is compressed
                if cached_data.startswith(b'\x1f\x8b'):  # gzip magic number
                    cached_data = gzip.decompress(cached_data)
                
                return json.loads(cached_data.decode('utf-8'))
        except Exception as e:
            logger.warning(f"Cache retrieval error for key {cache_key}: {e}")
        
        return None
    
    async def _cache_response(self, cache_key: str, response_data: Any, ttl: int):
        """Cache response with optional compression"""
        try:
            json_data = json.dumps(response_data, default=str).encode('utf-8')
            
            # Compress if data is large enough
            if len(json_data) > 1024:  # 1KB threshold
                json_data = gzip.compress(json_data)
            
            self.redis_client.set(cache_key, json_data, ex=ttl)
            
        except Exception as e:
            logger.warning(f"Cache storage error for key {cache_key}: {e}")
    
    def compress_response(self, response_data: str, compression_type: CompressionType) -> bytes:
        """Compress response data"""
        if compression_type == CompressionType.GZIP:
            return gzip.compress(response_data.encode('utf-8'))
        elif compression_type == CompressionType.BROTLI:
            try:
                import brotli
                return brotli.compress(response_data.encode('utf-8'))
            except ImportError:
                logger.warning("Brotli compression not available, falling back to gzip")
                return gzip.compress(response_data.encode('utf-8'))
        else:
            return response_data.encode('utf-8')
    
    async def get_mobile_metrics(self) -> Dict[str, Any]:
        """Get mobile API performance metrics"""
        try:
            # Get cache hit ratios
            cache_stats = {}
            for prefix in self.cache_prefixes.values():
                keys = self.redis_client.keys(f"{prefix}*")
                cache_stats[prefix.replace('mobile:', '').replace(':', '')] = len(keys)
            
            # Calculate optimization savings (mock data)
            optimization_stats = {
                'total_requests_optimized': 15420,
                'avg_response_size_reduction': '68%',
                'avg_load_time_improvement': '2.3s',
                'cache_hit_ratio': '84%',
                'data_saved_mb': 142.7
            }
            
            return {
                'cache_stats': cache_stats,
                'optimization_stats': optimization_stats,
                'device_distribution': {
                    'ios': '45%',
                    'android': '42%',
                    'mobile_web': '13%'
                },
                'network_distribution': {
                    'wifi': '52%',
                    '4g': '35%',
                    '3g': '10%',
                    '2g': '3%'
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Mobile metrics error: {e}")
            return {}
    
    async def preload_user_data(self, user_id: int, client_info: MobileClientInfo):
        """Preload and cache user data for faster mobile experience"""
        try:
            config = self.get_optimization_config(client_info)
            
            # Preload tasks
            preload_tasks = [
                'profile_data',
                'recent_matches',
                'discovery_users',
                'messages_preview'
            ]
            
            for task in preload_tasks:
                cache_key = f"mobile:preload:{user_id}:{task}:{client_info.device_type.value}"
                
                # Check if already cached
                if not self.redis_client.exists(cache_key):
                    # Mock preloading - in real implementation, fetch actual data
                    preload_data = {'preloaded': True, 'task': task, 'timestamp': datetime.utcnow().isoformat()}
                    await self._cache_response(cache_key, preload_data, config.cache_ttl)
            
            logger.info(f"Preloaded mobile data for user {user_id}")
            
        except Exception as e:
            logger.error(f"Preload error for user {user_id}: {e}")
    
    async def clear_user_cache(self, user_id: int):
        """Clear cached data for a specific user"""
        try:
            # Clear profile cache
            profile_keys = self.redis_client.keys(f"{self.cache_prefixes['profile']}{user_id}:*")
            
            # Clear matches cache involving this user
            matches_keys = self.redis_client.keys(f"{self.cache_prefixes['matches']}*")
            
            # Clear preload cache
            preload_keys = self.redis_client.keys(f"mobile:preload:{user_id}:*")
            
            all_keys = profile_keys + matches_keys + preload_keys
            
            if all_keys:
                self.redis_client.delete(*all_keys)
                logger.info(f"Cleared {len(all_keys)} cache entries for user {user_id}")
            
        except Exception as e:
            logger.error(f"Cache clearing error for user {user_id}: {e}")

# Global mobile API service instance
_mobile_api_service: Optional[MobileAPIService] = None

def get_mobile_api_service() -> MobileAPIService:
    """Get global mobile API service instance"""
    global _mobile_api_service
    if _mobile_api_service is None:
        raise RuntimeError("Mobile API service not initialized")
    return _mobile_api_service

def init_mobile_api_service(redis_client: redis.Redis) -> MobileAPIService:
    """Initialize global mobile API service"""
    global _mobile_api_service
    _mobile_api_service = MobileAPIService(redis_client)
    return _mobile_api_service

# Decorator for automatic mobile optimization
def mobile_optimized(cache_ttl: int = 1800):
    """Decorator to automatically optimize API responses for mobile clients"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request info (this would be passed from FastAPI)
            request = kwargs.get('request')
            if not request:
                return await func(*args, **kwargs)
            
            # Detect mobile client
            mobile_service = get_mobile_api_service()
            user_agent = request.headers.get('user-agent', '')
            client_info = mobile_service.detect_mobile_client(user_agent, dict(request.headers))
            
            # Execute original function
            response_data = await func(*args, **kwargs)
            
            # Optimize response for mobile if it's a mobile client
            if client_info.device_type != MobileDeviceType.UNKNOWN:
                if isinstance(response_data, dict):
                    # Determine optimization type based on endpoint
                    if 'profile' in str(func.__name__).lower():
                        response_data = await mobile_service.optimize_profile_response(
                            response_data, client_info
                        )
                    elif 'matches' in str(func.__name__).lower():
                        response_data = await mobile_service.optimize_matches_response(
                            response_data if isinstance(response_data, list) else [response_data], 
                            client_info
                        )
                    elif 'discovery' in str(func.__name__).lower():
                        response_data = await mobile_service.optimize_discovery_response(
                            response_data, client_info
                        )
            
            return response_data
        
        return wrapper
    return decorator