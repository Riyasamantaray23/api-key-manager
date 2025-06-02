# api_key_manager/models.py
from django.db import models
import secrets
from django.utils import timezone

class APIKey(models.Model):
    # The actual API key string
    key = models.CharField(max_length=64, unique=True, db_index=True,  blank=True)

    # A descriptive name for the key (e.g., "Mobile App Key", "Partnership A")
    name = models.CharField(max_length=255, unique=True)

    # Status of the key (active or revoked)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('revoked', 'Revoked'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    # When the key was created
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional expiration date for the key
    expires_at = models.DateTimeField(null=True, blank=True)

    # Rate limiting details for this specific key
    # Maximum requests allowed within a specific window
    rate_limit_per_window = models.IntegerField(
        default=1000,
        help_text="Max requests allowed within the rate limit window."
    )
    # Duration of the rate limit window in seconds (e.g., 3600 for 1 hour)
    rate_limit_window_seconds = models.IntegerField(
        default=3600, # 1 hour
        help_text="Duration of the rate limit window in seconds (e.g., 3600 for 1 hour)."
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.key:
            # Generate a secure, random 64-character hexadecimal key
            self.key = secrets.token_hex(32) # 32 bytes = 64 hex characters
        super().save(*args, **kwargs)

    def is_active(self):
        """
        Checks if the API key is active and not expired.
        """
        is_currently_active = self.status == 'active'
        is_not_expired = self.expires_at is None or self.expires_at > timezone.now()
        return is_currently_active and is_not_expired