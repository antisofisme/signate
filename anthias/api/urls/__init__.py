"""
Minimal Storage API URL Configuration
Only includes storage endpoints
"""

from django.urls import path, include

app_name = 'api'

urlpatterns = [
    path('storage/', include('api.urls.storage')),
]
