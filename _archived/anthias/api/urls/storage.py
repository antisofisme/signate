"""
Minimal Storage API URL Configuration

Only includes file storage operations:
- Upload file
- Serve file
- Get asset info
- Delete file
- Health check
"""

from django.urls import path
from api import storage

urlpatterns = [
    # Health check
    path('health', storage.health_check, name='storage_health'),

    # File operations
    path('upload', storage.upload_file, name='storage_upload'),
    path('serve/<str:asset_id>', storage.serve_file, name='storage_serve'),
    path('<str:asset_id>', storage.get_asset_info, name='storage_info'),
    path('delete/<str:asset_id>', storage.delete_file, name='storage_delete'),
]
