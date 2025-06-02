# api_key_manager/serializers.py
from rest_framework import serializers
from .models import APIKey

class APIKeySerializer(serializers.ModelSerializer):
    # The 'key' field is read-only because it's auto-generated and shouldn't be set manually via the API
    key = serializers.CharField(read_only=True)

    class Meta:
        model = APIKey
        fields = ['key', 'name', 'status', 'created_at', 'expires_at', 'rate_limit_per_window', 'rate_limit_window_seconds']
        read_only_fields = ['created_at'] # created_at is auto-set

class APIKeyRevokeSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=64, help_text="The API key string to revoke.")
    # We don't need 'name' or other fields for revocation, just the key.
    # We also don't need 'status' here as we'll force it to 'revoked' in the view.