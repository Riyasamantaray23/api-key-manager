# api_key_manager/admin.py
from django.contrib import admin
from .models import APIKey

# Register your models here.
admin.site.register(APIKey)
