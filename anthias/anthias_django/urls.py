"""
Minimal Storage Service URL Configuration
Only includes storage API
"""

from django.urls import include, path

urlpatterns = [
    path('', include('anthias_app.urls')),
    path('api/', include('api.urls')),
]
