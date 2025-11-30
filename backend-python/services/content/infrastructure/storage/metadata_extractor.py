"""
Metadata Extractor using FFprobe
Extracts media information from video, audio, and image files

OPTIMIZED: Uses asyncio.create_subprocess_exec() for non-blocking FFprobe calls
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image


class MetadataExtractor:
    """Extract metadata from media files using FFprobe"""

    async def extract(
        self,
        file_path: str,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from file

        Args:
            file_path: Path to file
            content_type: Type of content ('image', 'video', 'audio')

        Returns:
            Dictionary with metadata
        """
        if content_type == 'image':
            return await self._extract_image_metadata(file_path)
        elif content_type in ['video', 'audio']:
            return await self._extract_media_metadata(file_path, content_type)
        else:
            return {}

    async def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from image using Pillow"""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                return {
                    'width': width,
                    'height': height,
                    'resolution': f"{width}x{height}",
                    'codec': img.format.lower() if img.format else None,
                }
        except Exception as e:
            print(f"Image metadata extraction failed: {e}")
            return {}

    async def _extract_media_metadata(
        self,
        file_path: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Extract metadata from video/audio using FFprobe (async)"""
        try:
            # FFprobe timeout
            timeout = int(os.getenv('FFPROBE_TIMEOUT', '30'))

            # Use async subprocess for non-blocking execution
            process = await asyncio.create_subprocess_exec(
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                print(f"FFprobe timeout for {file_path}")
                return {}

            if process.returncode != 0:
                print(f"FFprobe failed: {stderr.decode()}")
                return {}

            data = json.loads(stdout.decode())

            # Extract relevant information
            metadata = {}

            # Format information
            if 'format' in data:
                format_data = data['format']
                if 'duration' in format_data:
                    metadata['duration'] = float(format_data['duration'])
                if 'bit_rate' in format_data:
                    metadata['bitrate'] = int(format_data['bit_rate']) // 1000  # kbps

            # Stream information
            if 'streams' in data:
                for stream in data['streams']:
                    codec_type = stream.get('codec_type')

                    if codec_type == 'video':
                        # Video stream metadata
                        metadata['codec'] = stream.get('codec_name')
                        metadata['width'] = stream.get('width')
                        metadata['height'] = stream.get('height')

                        if metadata.get('width') and metadata.get('height'):
                            metadata['resolution'] = f"{metadata['width']}x{metadata['height']}"

                        # FPS (frames per second)
                        if 'r_frame_rate' in stream:
                            try:
                                num, den = stream['r_frame_rate'].split('/')
                                if int(den) != 0:
                                    metadata['fps'] = float(num) / float(den)
                            except:
                                pass

                        # Bitrate
                        if 'bit_rate' in stream:
                            metadata['bitrate'] = int(stream['bit_rate']) // 1000

                    elif codec_type == 'audio' and content_type == 'audio':
                        # Audio stream metadata (for audio files)
                        metadata['audio_codec'] = stream.get('codec_name')
                        metadata['audio_channels'] = stream.get('channels', 2)
                        metadata['audio_sample_rate'] = stream.get('sample_rate')

                        if 'bit_rate' in stream:
                            metadata['audio_bitrate'] = int(stream['bit_rate']) // 1000

            return metadata

        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return {}


# Singleton instance
_metadata_extractor: Optional[MetadataExtractor] = None


def get_metadata_extractor() -> MetadataExtractor:
    """Get metadata extractor instance (dependency injection)"""
    global _metadata_extractor

    if _metadata_extractor is None:
        _metadata_extractor = MetadataExtractor()

    return _metadata_extractor
