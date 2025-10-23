"""
Media Metadata Extraction Utility
Uses FFprobe to extract detailed metadata from video and image files
"""

import json
import subprocess
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class MediaMetadataExtractor:
    """Extract metadata from media files using FFprobe"""

    @staticmethod
    def extract_video_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from video file

        Args:
            file_path: Path to video file

        Returns:
            Dictionary containing video metadata:
            - resolution: Video resolution (e.g., "1920x1080")
            - width: Video width in pixels
            - height: Video height in pixels
            - codec: Video codec name
            - fps: Frame rate
            - bitrate: Bitrate in kbps
            - duration: Duration in seconds
            - audio_codec: Audio codec name (if available)
            - audio_bitrate: Audio bitrate in kbps (if available)
            - audio_sample_rate: Audio sample rate in Hz (if available)
            - file_size: File size in bytes
        """
        try:
            # Run ffprobe command
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            data = json.loads(result.stdout)

            # Extract video stream info
            video_stream = next(
                (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
                None
            )

            # Extract audio stream info
            audio_stream = next(
                (s for s in data.get('streams', []) if s.get('codec_type') == 'audio'),
                None
            )

            # Extract format info
            format_info = data.get('format', {})

            metadata = {}

            # Video metadata
            if video_stream:
                width = int(video_stream.get('width', 0))
                height = int(video_stream.get('height', 0))
                metadata['resolution'] = f"{width}x{height}" if width and height else None
                metadata['width'] = width
                metadata['height'] = height
                metadata['codec'] = video_stream.get('codec_name')

                # Calculate FPS
                fps_str = video_stream.get('r_frame_rate', '0/1')
                if fps_str and '/' in fps_str:
                    num, den = fps_str.split('/')
                    fps = float(num) / float(den) if float(den) != 0 else 0
                    metadata['fps'] = round(fps, 2)
                else:
                    metadata['fps'] = None

                # Bitrate (convert to kbps)
                bitrate = video_stream.get('bit_rate')
                if bitrate:
                    metadata['bitrate'] = int(int(bitrate) / 1000)
                elif format_info.get('bit_rate'):
                    metadata['bitrate'] = int(int(format_info['bit_rate']) / 1000)
                else:
                    metadata['bitrate'] = None

            # Audio metadata
            if audio_stream:
                metadata['audio_codec'] = audio_stream.get('codec_name')
                audio_bitrate = audio_stream.get('bit_rate')
                if audio_bitrate:
                    metadata['audio_bitrate'] = int(int(audio_bitrate) / 1000)
                else:
                    metadata['audio_bitrate'] = None
                metadata['audio_sample_rate'] = int(audio_stream.get('sample_rate', 0)) or None
            else:
                metadata['audio_codec'] = None
                metadata['audio_bitrate'] = None
                metadata['audio_sample_rate'] = None

            # Duration
            duration = format_info.get('duration')
            metadata['duration'] = float(duration) if duration else None

            # File size
            file_size = format_info.get('size')
            metadata['file_size'] = int(file_size) if file_size else None

            logger.info(f"Extracted video metadata from {file_path}: {metadata}")
            return metadata

        except subprocess.TimeoutExpired:
            logger.error(f"FFprobe timeout for file: {file_path}")
            return {}
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error for file {file_path}: {e.stderr}")
            return {}
        except Exception as e:
            logger.error(f"Error extracting video metadata from {file_path}: {str(e)}")
            return {}

    @staticmethod
    def extract_image_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from image file

        Args:
            file_path: Path to image file

        Returns:
            Dictionary containing image metadata:
            - resolution: Image resolution (e.g., "1920x1080")
            - width: Image width in pixels
            - height: Image height in pixels
            - codec: Image format/codec
            - file_size: File size in bytes
        """
        try:
            # Run ffprobe command
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            data = json.loads(result.stdout)

            # Extract video stream (images are treated as video with 1 frame)
            stream = next(
                (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
                None
            )

            # Extract format info
            format_info = data.get('format', {})

            metadata = {}

            if stream:
                width = int(stream.get('width', 0))
                height = int(stream.get('height', 0))
                metadata['resolution'] = f"{width}x{height}" if width and height else None
                metadata['width'] = width
                metadata['height'] = height
                metadata['codec'] = stream.get('codec_name')

            # File size
            file_size = format_info.get('size')
            metadata['file_size'] = int(file_size) if file_size else None

            logger.info(f"Extracted image metadata from {file_path}: {metadata}")
            return metadata

        except subprocess.TimeoutExpired:
            logger.error(f"FFprobe timeout for file: {file_path}")
            return {}
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error for file {file_path}: {e.stderr}")
            return {}
        except Exception as e:
            logger.error(f"Error extracting image metadata from {file_path}: {str(e)}")
            return {}

    @staticmethod
    def extract_metadata(file_path: str, content_type: str) -> Dict[str, Any]:
        """
        Extract metadata based on content type

        Args:
            file_path: Path to media file
            content_type: Type of content ('video' or 'image')

        Returns:
            Dictionary containing metadata
        """
        if content_type.lower() == 'video':
            return MediaMetadataExtractor.extract_video_metadata(file_path)
        elif content_type.lower() == 'image':
            return MediaMetadataExtractor.extract_image_metadata(file_path)
        else:
            logger.warning(f"Unknown content type: {content_type}")
            return {}
