# api_key_manager/permissions.py
from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from datetime import timedelta
import redis
from django.utils import timezone

from .models import APIKey

# Initialize Redis client
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

# Cache TTL for API Key lookups in Redis (e.g., 5 minutes)
API_KEY_CACHE_TTL_SECONDS = 300 # 5 minutes

class HasAPIKey(permissions.BasePermission):
    """
    Custom permission to check for a valid API Key in the X-API-KEY header.
    Uses Redis for fast lookups with a database fallback.
    """
    message = "Invalid or missing API Key."

    def has_permission(self, request, view):
        # Allow OPTIONS requests without an API key (for CORS preflight)
        if request.method == 'OPTIONS':
            return True

        api_key_str = request.headers.get('X-API-KEY')

        if not api_key_str:
            self.message = "API Key is missing from X-API-KEY header."
            return False

        # 1. Try to get key details from Redis (fast lookup)
        redis_key_name = f"api_key:{api_key_str}"
        api_key_data_from_redis = r.hgetall(redis_key_name)

        if api_key_data_from_redis:
            try:
                # Decode bytes to string
                status = api_key_data_from_redis.get(b'status', b'').decode('utf-8')
                expires_at_timestamp = api_key_data_from_redis.get(b'expires_at_timestamp') # May be None

                if status != 'active':
                    self.message = "API Key is not active or has been revoked."
                    return False

                if expires_at_timestamp:
                    # Convert timestamp to datetime object
                    expires_at = timezone.datetime.fromtimestamp(float(expires_at_timestamp), tz=timezone.utc)
                    if expires_at <= timezone.now():
                        self.message = "API Key has expired."
                        # Optionally delete from Redis if expired
                        r.delete(redis_key_name)
                        return False

                # If key found in Redis and valid, attach it to the request for later use
                # We'll retrieve the full object from DB for request.api_key for now,
                # a more advanced setup might store more in Redis.
                try:
                    api_key_instance = APIKey.objects.get(key=api_key_str)
                    request.api_key = api_key_instance
                    return True
                except APIKey.DoesNotExist:
                    # Key was in Redis but not in DB? Invalidate Redis entry.
                    r.delete(redis_key_name)
                    self.message = "Invalid API Key (DB mismatch)."
                    return False

            except Exception as e:
                # Log the error (e.g., malformed data in Redis)
                print(f"Error parsing Redis API key data for {api_key_str}: {e}")
                r.delete(redis_key_name) # Invalidate corrupted Redis entry
                self.message = "Invalid API Key."
                return False

        # 2. If not in Redis or Redis data was stale/corrupted, fall back to Database
        try:
            api_key_instance = APIKey.objects.get(key=api_key_str)

            if api_key_instance.status != 'active':
                self.message = "API Key is not active or has been revoked."
                return False

            if api_key_instance.expires_at and api_key_instance.expires_at <= timezone.now():
                self.message = "API Key has expired."
                # Update status in DB if expired
                api_key_instance.status = 'expired'
                api_key_instance.save()
                # Also update Redis with new status and TTL
                redis_key_name = f"api_key:{api_key_instance.key}"
                r.hset(redis_key_name, 'status', 'expired')
                r.expire(redis_key_name, 10) # Keep in Redis for a short while as expired
                return False

            # If found in DB and valid, cache it in Redis for future requests
            redis_key_name = f"api_key:{api_key_instance.key}"
            r.hset(redis_key_name, 'status', api_key_instance.status)
            r.hset(redis_key_name, 'rate_limit_per_window', api_key_instance.rate_limit_per_window)
            r.hset(redis_key_name, 'rate_limit_window_seconds', api_key_instance.rate_limit_window_seconds)

            if api_key_instance.expires_at:
                # Store timestamp for Redis
                expires_at_timestamp = api_key_instance.expires_at.timestamp()
                r.hset(redis_key_name, 'expires_at_timestamp', str(expires_at_timestamp))
                # Set Redis TTL based on actual expiration if close, else a default cache TTL
                delta = api_key_instance.expires_at - timezone.now()
                if delta.total_seconds() > 0:
                    r.expire(redis_key_name, min(int(delta.total_seconds()), API_KEY_CACHE_TTL_SECONDS))
                else:
                    r.expire(redis_key_name, 1) # Immediately expire if already passed
            else:
                r.expire(redis_key_name, API_KEY_CACHE_TTL_SECONDS) # Apply general cache TTL

            request.api_key = api_key_instance # Attach the APIKey instance to the request
            return True

        except APIKey.DoesNotExist:
            self.message = "Invalid API Key."
            return False