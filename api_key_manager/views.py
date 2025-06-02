# api_key_manager/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import APIKey
from .serializers import APIKeySerializer, APIKeyRevokeSerializer
import redis
from django.conf import settings

# Initialize Redis client (ensure Redis server is running!)
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


class IssueAPIKeyView(generics.CreateAPIView): # <-- This class definition is crucial
    """
    API endpoint to issue a new API Key.
    Requires a 'name' for the key. The key itself is auto-generated.
    """
    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer

    def perform_create(self, serializer):
        api_key_instance = serializer.save()

        # Store key status and rate limits in Redis for fast lookup
        # We'll use a Redis Hash for each API key's metadata
        redis_key_name = f"api_key:{api_key_instance.key}"
        r.hset(redis_key_name, 'status', api_key_instance.status)
        r.hset(redis_key_name, 'rate_limit_per_window', api_key_instance.rate_limit_per_window)
        r.hset(redis_key_name, 'rate_limit_window_seconds', api_key_instance.rate_limit_window_seconds)

        # If the key has an expiration, set a Redis TTL on the hash
        if api_key_instance.expires_at:
            # Calculate seconds until expiration.
            # Ensure timezone awareness.
            from django.utils import timezone
            delta = api_key_instance.expires_at - timezone.now()
            if delta.total_seconds() > 0:
                r.expire(redis_key_name, int(delta.total_seconds()))

        # Print the key to console for easy copy during development (remove in production)
        print(f"--- NEW API KEY ISSUED ---")
        print(f"Name: {api_key_instance.name}")
        print(f"Key:  {api_key_instance.key}")
        print(f"--------------------------")


class RevokeAPIKeyView(APIView): # <-- This class definition is crucial
    """
    API endpoint to revoke an API Key.
    Requires the 'key' string in the request body.
    """
    def post(self, request, *args, **kwargs):
        serializer = APIKeyRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        key_to_revoke = serializer.validated_data['key']

        try:
            api_key_instance = APIKey.objects.get(key=key_to_revoke)
        except APIKey.DoesNotExist:
            return Response(
                {"detail": "API Key not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if api_key_instance.status == 'revoked':
            return Response(
                {"detail": "API Key is already revoked."},
                status=status.HTTP_200_OK # Or 409 Conflict, but 200 is fine if idempotent
            )

        # Update status in database
        api_key_instance.status = 'revoked'
        api_key_instance.save()

        # Remove/update status in Redis immediately
        redis_key_name = f"api_key:{api_key_instance.key}"
        # Option 1: Delete the key from Redis (fastest way to stop access)
        r.delete(redis_key_name)
        # Option 2: Update status in Redis (if you want to keep other metadata)
        # r.hset(redis_key_name, 'status', 'revoked')

        return Response(
            {"detail": "API Key revoked successfully."},
            status=status.HTTP_200_OK
        )
# api_key_manager/views.py (add this at the bottom)
from rest_framework.permissions import IsAuthenticated # We'll still use this for general authentication if you later add user auth
from .permissions import HasAPIKey # <-- Import your custom permission

class ProtectedTestView(APIView):
    """
    A simple protected API endpoint that requires a valid API Key.
    """
    authentication_classes = [] 
    permission_classes = [HasAPIKey] # <--- Apply your custom permission here

    def get(self, request, *args, **kwargs):
        # If the request reaches here, it means HasAPIKey permission passed.
        # You can access the APIKey instance attached by the permission like this:
        key_name = getattr(request, 'api_key', None) # Get api_key_instance from request, if attached
        if key_name:
            return Response({
                "message": f"Hello from protected endpoint! You used API Key: {key_name.name}",
                "api_key_status": key_name.status
            }, status=status.HTTP_200_OK)
        else:
            # Fallback in case api_key was not attached for some reason (shouldn't happen with HasAPIKey)
            return Response({"message": "Hello from protected endpoint! (API Key detected but not attached)"}, status=status.HTTP_200_OK)