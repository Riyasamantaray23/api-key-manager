# api_key_manager/urls.py
from django.urls import path
from .views import IssueAPIKeyView, RevokeAPIKeyView, ProtectedTestView 

urlpatterns = [
    path('issue/', IssueAPIKeyView.as_view(), name='issue_api_key'),
    path('revoke/', RevokeAPIKeyView.as_view(), name='revoke_api_key'),
     path('test-protected/', ProtectedTestView.as_view(), name='test_protected_api'),
]