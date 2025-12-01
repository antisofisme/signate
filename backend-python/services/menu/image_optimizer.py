"""
Menu Image Optimizer Service

Optimizes menu media images by generating WebP variants for different resolutions.
Supports:
- JPEG, PNG, WebP, GIF (including animated), HEIC/HEIF
- Multiple resolution variants: thumb, small, hd, 4k, original
- JPEG fallback for older browsers
- Animated GIF to animated WebP conversion
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import io
from loguru import logger

# Register HEIC/HEIF opener
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    logger.warning("pillow-heif not installed, HEIC support disabled")


class MenuImageOptimizer:
    """
    Generates optimized WebP variants for menu images.

    Variants:
    - thumb: 200x200, quality 80 - for grid previews
    - small: 640x640, quality 82 - for mobile/thumbnails
    - hd: 1280x1280, quality 85 - for Full HD displays
    - 4k: 2560x2560, quality 88 - for 4K displays (only if source is large enough)
    - original: original size, quality 92 - archive/future-proof
    - fallback: hd size as JPEG for older browsers
    """

    VARIANTS = {
        'thumb':    {'max_size': 200,  'quality': 80},
        'small':    {'max_size': 640,  'quality': 82},
        'hd':       {'max_size': 1280, 'quality': 85},
        '4k':       {'max_size': 2560, 'quality': 88},
        'original': {'max_size': None, 'quality': 92},
    }

    # Minimum source size to generate 4K variant
    MIN_SIZE_FOR_4K = 2000

    def __init__(self, base_storage_path: str = "/data/signage/menu_media"):
        """
        Initialize optimizer with storage path.

        Args:
            base_storage_path: Base directory for storing optimized images
        """
        self.base_storage_path = Path(base_storage_path)

    def optimize_image(
        self,
        media_id: int,
        organization_id: int,
        source_path: str,
        source_content: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Generate all WebP variants for an image.

        Args:
            media_id: Menu media ID
            organization_id: Organization ID
            source_path: Path to source image file
            source_content: Optional bytes content (if not reading from file)

        Returns:
            Dict with variants info and metadata:
            {
                "variants": {...},
                "content_hash": "...",
                "original_width": 1920,
                "original_height": 1080,
                "is_animated": False,
                "processing_status": "completed"
            }
        """
        try:
            # Load source image
            if source_content:
                img = Image.open(io.BytesIO(source_content))
            else:
                img = Image.open(source_path)

            # Get original dimensions
            original_width, original_height = img.size

            # Check if animated GIF
            is_animated = self._is_animated(img)

            # Auto-orient based on EXIF
            img = self._auto_orient(img)

            # Create output directory
            output_dir = self.base_storage_path / f"org_{organization_id}" / str(media_id)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate variants
            variants = {}

            if is_animated:
                # Handle animated GIF separately
                variants = self._generate_animated_variants(
                    img, source_path, output_dir, media_id
                )
            else:
                # Generate static variants
                variants = self._generate_static_variants(
                    img, output_dir, media_id, original_width, original_height
                )

            # Calculate content hash from original webp
            content_hash = self._calculate_content_hash(output_dir / "original.webp")

            return {
                "variants": variants,
                "content_hash": content_hash,
                "original_width": original_width,
                "original_height": original_height,
                "is_animated": is_animated,
                "processing_status": "completed",
                "optimized_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Image optimization failed for media {media_id}: {e}")
            return {
                "variants": None,
                "content_hash": None,
                "original_width": None,
                "original_height": None,
                "is_animated": False,
                "processing_status": "failed",
                "error": str(e)
            }

    def _is_animated(self, img: Image.Image) -> bool:
        """Check if image is animated (multi-frame)."""
        try:
            return hasattr(img, 'n_frames') and img.n_frames > 1
        except Exception:
            return False

    def _auto_orient(self, img: Image.Image) -> Image.Image:
        """Auto-orient image based on EXIF data."""
        try:
            # Get EXIF orientation
            exif = img.getexif()
            if exif:
                orientation = exif.get(274)  # 274 is Orientation tag

                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)

            return img
        except Exception:
            return img

    def _generate_static_variants(
        self,
        img: Image.Image,
        output_dir: Path,
        media_id: int,
        original_width: int,
        original_height: int
    ) -> Dict[str, Dict[str, Any]]:
        """Generate WebP variants for static images."""
        variants = {}

        # Convert to RGB if necessary (for PNG with transparency, convert to RGBA for WebP)
        if img.mode == 'RGBA':
            working_img = img
        elif img.mode in ('P', 'LA'):
            working_img = img.convert('RGBA')
        else:
            working_img = img.convert('RGB')

        for variant_name, config in self.VARIANTS.items():
            max_size = config['max_size']
            quality = config['quality']

            # Skip 4K if source is too small
            if variant_name == '4k' and max(original_width, original_height) < self.MIN_SIZE_FOR_4K:
                continue

            # Resize if needed
            if max_size and max(working_img.size) > max_size:
                resized = self._resize_contain(working_img, max_size)
            else:
                resized = working_img.copy() if max_size else working_img

            # Save as WebP
            output_path = output_dir / f"{variant_name}.webp"
            resized.save(
                output_path,
                format='WEBP',
                quality=quality,
                method=5 if variant_name in ('hd', '4k', 'original') else 4
            )

            # Get file stats
            file_size = output_path.stat().st_size

            variants[variant_name] = {
                "path": str(output_path),
                "url": f"/menu-media-optimized/org_{output_dir.parent.name.split('_')[1]}/{media_id}/{variant_name}.webp",
                "width": resized.width,
                "height": resized.height,
                "size": file_size,
                "format": "webp"
            }

        # Generate JPEG fallback (hd size)
        fallback_path = output_dir / "hd.jpg"
        hd_size = self.VARIANTS['hd']['max_size']

        if max(working_img.size) > hd_size:
            fallback_img = self._resize_contain(working_img, hd_size)
        else:
            fallback_img = working_img

        # Convert to RGB for JPEG (no transparency)
        if fallback_img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', fallback_img.size, (255, 255, 255))
            background.paste(fallback_img, mask=fallback_img.split()[3])
            fallback_img = background
        elif fallback_img.mode != 'RGB':
            fallback_img = fallback_img.convert('RGB')

        fallback_img.save(fallback_path, format='JPEG', quality=85, optimize=True)

        variants['fallback'] = {
            "path": str(fallback_path),
            "url": f"/menu-media-optimized/org_{output_dir.parent.name.split('_')[1]}/{media_id}/hd.jpg",
            "width": fallback_img.width,
            "height": fallback_img.height,
            "size": fallback_path.stat().st_size,
            "format": "jpeg"
        }

        return variants

    def _generate_animated_variants(
        self,
        img: Image.Image,
        source_path: str,
        output_dir: Path,
        media_id: int
    ) -> Dict[str, Dict[str, Any]]:
        """Generate animated WebP variants for animated GIFs."""
        variants = {}

        # Extract frames and durations
        frames = []
        durations = []

        try:
            for frame_idx in range(img.n_frames):
                img.seek(frame_idx)
                frame = img.copy().convert('RGBA')
                frames.append(frame)
                durations.append(img.info.get('duration', 100))
        except Exception as e:
            logger.warning(f"Failed to extract animated frames: {e}")
            # Fall back to static processing
            return self._generate_static_variants(
                img, output_dir, media_id, img.width, img.height
            )

        original_width, original_height = frames[0].size

        # Generate animated variants for specific sizes
        animated_variants = ['thumb', 'small', 'hd', 'original']

        for variant_name in animated_variants:
            config = self.VARIANTS[variant_name]
            max_size = config['max_size']
            quality = config['quality']

            # Resize frames if needed
            if max_size and max(original_width, original_height) > max_size:
                resized_frames = [self._resize_contain(f, max_size) for f in frames]
            else:
                resized_frames = frames

            # Save as animated WebP
            output_path = output_dir / f"{variant_name}.webp"

            resized_frames[0].save(
                output_path,
                format='WEBP',
                save_all=True,
                append_images=resized_frames[1:],
                duration=durations,
                loop=0,
                quality=quality
            )

            file_size = output_path.stat().st_size

            variants[variant_name] = {
                "path": str(output_path),
                "url": f"/menu-media-optimized/org_{output_dir.parent.name.split('_')[1]}/{media_id}/{variant_name}.webp",
                "width": resized_frames[0].width,
                "height": resized_frames[0].height,
                "size": file_size,
                "format": "webp",
                "animated": True,
                "frames": len(frames)
            }

        # Generate static JPEG fallback (first frame)
        fallback_path = output_dir / "hd.jpg"
        hd_size = self.VARIANTS['hd']['max_size']

        first_frame = frames[0]
        if max(first_frame.size) > hd_size:
            fallback_img = self._resize_contain(first_frame, hd_size)
        else:
            fallback_img = first_frame

        # Convert to RGB for JPEG
        background = Image.new('RGB', fallback_img.size, (255, 255, 255))
        background.paste(fallback_img, mask=fallback_img.split()[3])

        background.save(fallback_path, format='JPEG', quality=85, optimize=True)

        variants['fallback'] = {
            "path": str(fallback_path),
            "url": f"/menu-media-optimized/org_{output_dir.parent.name.split('_')[1]}/{media_id}/hd.jpg",
            "width": background.width,
            "height": background.height,
            "size": fallback_path.stat().st_size,
            "format": "jpeg",
            "animated": False
        }

        return variants

    def _resize_contain(self, img: Image.Image, max_size: int) -> Image.Image:
        """Resize image to fit within max_size while maintaining aspect ratio."""
        ratio = min(max_size / img.width, max_size / img.height)
        if ratio >= 1:
            return img.copy()

        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)

        return img.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )

    def _calculate_content_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        if not file_path.exists():
            return ""

        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def delete_variants(self, organization_id: int, media_id: int) -> bool:
        """Delete all variants for a media item."""
        try:
            variant_dir = self.base_storage_path / f"org_{organization_id}" / str(media_id)
            if variant_dir.exists():
                import shutil
                shutil.rmtree(variant_dir)
                logger.info(f"Deleted variants for media {media_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete variants for media {media_id}: {e}")
            return False

    def get_variant_url(
        self,
        organization_id: int,
        media_id: int,
        variant: str = 'hd'
    ) -> Optional[str]:
        """Get URL for a specific variant."""
        variant_path = (
            self.base_storage_path /
            f"org_{organization_id}" /
            str(media_id) /
            f"{variant}.webp"
        )

        if variant_path.exists():
            return f"/menu-media-optimized/org_{organization_id}/{media_id}/{variant}.webp"

        return None


# Singleton instance
_optimizer_instance: Optional[MenuImageOptimizer] = None


def get_image_optimizer() -> MenuImageOptimizer:
    """Get or create singleton optimizer instance."""
    global _optimizer_instance
    if _optimizer_instance is None:
        from shared.config import settings
        # Use UPLOAD_DIR/menu_media_optimized for storing WebP variants
        import os
        storage_path = os.path.join(settings.UPLOAD_DIR, 'menu_media_optimized')
        _optimizer_instance = MenuImageOptimizer(storage_path)
    return _optimizer_instance
