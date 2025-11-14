"""
File Security Utilities
Provides secure file handling and validation
"""

import os
import re
import hashlib
import magic
from pathlib import Path
from typing import Optional, Set, Tuple
from fastapi import HTTPException, status


class SecureFileHandler:
    """
    Handles file operations securely, preventing path traversal and other attacks
    """
    
    # Allowed file extensions by content type
    ALLOWED_EXTENSIONS = {
        "image": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"},
        "video": {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv"},
        "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
        "document": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"},
    }
    
    # MIME type mapping
    MIME_TYPES = {
        "image": {
            "image/jpeg", "image/png", "image/gif", "image/webp", 
            "image/bmp", "image/x-ms-bmp"
        },
        "video": {
            "video/mp4", "video/x-msvideo", "video/x-matroska",
            "video/quicktime", "video/webm", "video/x-flv", "video/x-ms-wmv"
        },
        "audio": {
            "audio/mpeg", "audio/wav", "audio/x-wav", "audio/flac",
            "audio/aac", "audio/ogg", "audio/mp4", "audio/x-ms-wma"
        },
    }
    
    # Maximum filename length
    MAX_FILENAME_LENGTH = 255
    
    # Regex for safe filenames (alphanumeric, dash, underscore, dot)
    SAFE_FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9._-]+$')
    
    # Dangerous path components to block
    DANGEROUS_PATHS = {"..", "~", "/", "\\", "\x00"}
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks
        
        Args:
            filename: Original filename from user
            
        Returns:
            Sanitized safe filename
            
        Raises:
            ValueError: If filename is invalid or dangerous
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        # Remove any path components (both forward and back slashes)
        filename = os.path.basename(filename.replace("\\", "/"))
        
        # Remove null bytes
        filename = filename.replace("\x00", "")
        
        # Check for dangerous path components
        for dangerous in cls.DANGEROUS_PATHS:
            if dangerous in filename:
                raise ValueError(f"Filename contains dangerous component: {dangerous}")
        
        # Limit filename length
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            # Preserve extension if possible
            name, ext = os.path.splitext(filename)
            max_name_length = cls.MAX_FILENAME_LENGTH - len(ext) - 1
            filename = name[:max_name_length] + ext
        
        # Validate filename format
        if not cls.SAFE_FILENAME_REGEX.match(filename):
            # Replace unsafe characters with underscores
            filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
            
            # Remove multiple underscores
            filename = re.sub(r'_+', '_', filename)
            
            # Remove leading/trailing underscores and dots
            filename = filename.strip('_.')
        
        # Ensure filename is not empty after sanitization
        if not filename:
            raise ValueError("Filename became empty after sanitization")
        
        # Validate extension
        _, ext = os.path.splitext(filename.lower())
        if not ext:
            raise ValueError("Filename must have an extension")
        
        return filename
    
    @classmethod
    def validate_file_extension(cls, filename: str, content_type: str) -> bool:
        """
        Validate file extension against content type
        
        Args:
            filename: Filename to validate
            content_type: Expected content type (image/video/audio)
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If extension is not allowed
        """
        _, ext = os.path.splitext(filename.lower())
        
        allowed = cls.ALLOWED_EXTENSIONS.get(content_type, set())
        if ext not in allowed:
            raise ValueError(
                f"File extension '{ext}' not allowed for {content_type}. "
                f"Allowed: {', '.join(sorted(allowed))}"
            )
        
        return True
    
    @classmethod
    def validate_file_content(cls, file_path: Path, expected_type: str) -> bool:
        """
        Validate actual file content matches expected type using magic bytes
        
        Args:
            file_path: Path to uploaded file
            expected_type: Expected content type
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If content doesn't match expected type
        """
        try:
            # Use python-magic to detect actual file type
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_file(str(file_path))
            
            allowed_mimes = cls.MIME_TYPES.get(expected_type, set())
            
            if detected_mime not in allowed_mimes:
                raise ValueError(
                    f"File content ({detected_mime}) doesn't match "
                    f"expected type ({expected_type})"
                )
            
            return True
            
        except Exception as e:
            raise ValueError(f"Failed to validate file content: {str(e)}")
    
    @classmethod
    def generate_safe_path(cls, base_dir: Path, filename: str, 
                          organization_id: int, content_type: str) -> Path:
        """
        Generate a safe file path with proper directory structure
        
        Args:
            base_dir: Base directory for uploads
            filename: Sanitized filename
            organization_id: Organization ID for isolation
            content_type: Content type for categorization
            
        Returns:
            Safe absolute path for file storage
        """
        # Create directory structure: /base/org_id/content_type/YYYY/MM/
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        dir_path = base_dir / str(organization_id) / content_type / \
                   str(now.year) / f"{now.month:02d}"
        
        # Create directories if they don't exist
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename to avoid collisions
        name, ext = os.path.splitext(filename)
        unique_suffix = hashlib.md5(f"{now.timestamp()}".encode()).hexdigest()[:8]
        unique_filename = f"{name}_{unique_suffix}{ext}"
        
        full_path = dir_path / unique_filename
        
        # Ensure the path is within base directory (prevent traversal)
        try:
            full_path = full_path.resolve()
            base_dir = base_dir.resolve()
            
            if not str(full_path).startswith(str(base_dir)):
                raise ValueError("Path traversal attempt detected")
                
        except Exception:
            raise ValueError("Invalid file path")
        
        return full_path
    
    @classmethod
    def calculate_file_hash(cls, file_path: Path) -> str:
        """
        Calculate SHA256 hash of file for integrity checking
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex string of file hash
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    @classmethod
    def validate_image_file(cls, file_path: Path, max_dimensions: Tuple[int, int] = (10000, 10000)) -> dict:
        """
        Additional validation for image files
        
        Args:
            file_path: Path to image file
            max_dimensions: Maximum allowed (width, height)
            
        Returns:
            Dict with image metadata
            
        Raises:
            ValueError: If image is invalid or too large
        """
        try:
            from PIL import Image
            
            with Image.open(file_path) as img:
                # Check dimensions
                if img.width > max_dimensions[0] or img.height > max_dimensions[1]:
                    raise ValueError(
                        f"Image dimensions ({img.width}x{img.height}) exceed "
                        f"maximum allowed ({max_dimensions[0]}x{max_dimensions[1]})"
                    )
                
                # Check for image bombs
                if img.width * img.height > 100_000_000:  # 100 megapixels
                    raise ValueError("Image resolution too high (potential decompression bomb)")
                
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode
                }
                
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")


def create_secure_upload_validator(
    allowed_types: Set[str] = {"image", "video", "audio"},
    max_file_size: int = 500 * 1024 * 1024  # 500MB
):
    """
    Create a dependency for secure file upload validation
    
    Args:
        allowed_types: Set of allowed content types
        max_file_size: Maximum file size in bytes
        
    Returns:
        Dependency function for FastAPI
    """
    def validate_upload(file):
        # Check file size
        if file.size > max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {max_file_size // (1024*1024)}MB"
            )
        
        # Sanitize filename
        try:
            safe_filename = SecureFileHandler.sanitize_filename(file.filename)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename: {str(e)}"
            )
        
        # Detect content type from filename
        ext = os.path.splitext(safe_filename.lower())[1]
        content_type = None
        
        for ctype, extensions in SecureFileHandler.ALLOWED_EXTENSIONS.items():
            if ext in extensions and ctype in allowed_types:
                content_type = ctype
                break
        
        if not content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            )
        
        return {
            "file": file,
            "safe_filename": safe_filename,
            "content_type": content_type
        }
    
    return validate_upload