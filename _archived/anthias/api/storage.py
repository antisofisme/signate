"""
Minimal Storage API for Anthias
Only handles file upload, serve, and delete
All business logic (scheduling, playlists) is in Backend (FastAPI)
"""

from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from anthias_app.models import Asset
import hashlib
import os
import uuid
from pathlib import Path

STORAGE_PATH = Path('/data/screenly_assets')
STORAGE_PATH.mkdir(parents=True, exist_ok=True)


def generate_asset_id():
    """Generate unique asset ID"""
    return str(uuid.uuid4())


@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    """
    Upload file and return asset info

    POST /api/storage/upload
    Form data:
        - file: File to upload

    Returns:
        {
            "success": true,
            "data": {
                "asset_id": "uuid",
                "uri": "/data/screenly_assets/uuid_filename.ext",
                "md5": "md5hash",
                "size": 12345,
                "mimetype": "video/mp4"
            }
        }
    """
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'No file provided'}, status=400)

        # Calculate MD5
        md5_hash = hashlib.md5()
        for chunk in file.chunks():
            md5_hash.update(chunk)
        md5_hex = md5_hash.hexdigest()

        # Generate unique asset ID
        asset_id = generate_asset_id()

        # Save file
        filename = f"{asset_id}_{file.name}"
        file_path = STORAGE_PATH / filename

        # Reset file pointer after MD5 calculation
        file.seek(0)

        with open(file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)

        # Create asset record (minimal)
        asset = Asset.objects.create(
            asset_id=asset_id,
            name=file.name,
            uri=str(file_path),
            md5=md5_hex,
            mimetype=file.content_type or 'application/octet-stream'
        )

        return JsonResponse({
            'success': True,
            'data': {
                'asset_id': asset_id,
                'uri': str(file_path),
                'md5': md5_hex,
                'size': file.size,
                'mimetype': asset.mimetype
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def serve_file(request, asset_id):
    """
    Serve file by asset ID

    GET /api/storage/serve/{asset_id}

    Returns: File content
    """
    try:
        asset = Asset.objects.get(asset_id=asset_id)

        if not os.path.exists(asset.uri):
            return JsonResponse({'error': 'File not found on disk'}, status=404)

        response = FileResponse(open(asset.uri, 'rb'))
        response['Content-Type'] = asset.mimetype
        response['Content-Disposition'] = f'inline; filename="{asset.name}"'
        return response

    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_asset_info(request, asset_id):
    """
    Get asset metadata

    GET /api/storage/{asset_id}

    Returns:
        {
            "success": true,
            "data": {
                "asset_id": "uuid",
                "name": "filename.mp4",
                "uri": "/data/screenly_assets/...",
                "md5": "hash",
                "mimetype": "video/mp4"
            }
        }
    """
    try:
        asset = Asset.objects.get(asset_id=asset_id)

        return JsonResponse({
            'success': True,
            'data': {
                'asset_id': asset.asset_id,
                'name': asset.name,
                'uri': asset.uri,
                'md5': asset.md5,
                'mimetype': asset.mimetype
            }
        })

    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_file(request, asset_id):
    """
    Delete file

    DELETE /api/storage/{asset_id}

    Returns:
        {"success": true}
    """
    try:
        asset = Asset.objects.get(asset_id=asset_id)

        # Delete file from disk
        if os.path.exists(asset.uri):
            os.remove(asset.uri)

        # Delete database record
        asset.delete()

        return JsonResponse({'success': True})

    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint

    GET /api/storage/health

    Returns:
        {
            "status": "ok",
            "mode": "minimal_storage",
            "version": "1.0"
        }
    """
    return JsonResponse({
        'status': 'ok',
        'mode': 'minimal_storage',
        'version': '1.0',
        'storage_path': str(STORAGE_PATH),
        'storage_exists': STORAGE_PATH.exists()
    })
