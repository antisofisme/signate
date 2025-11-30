"""Slug Generation Utilities"""

import re
from typing import Optional


def generate_portal_slug(name: str, org_id: int) -> str:
    """
    Generate URL-friendly slug from organization name + ID.

    Examples:
        "Hotel Signage Demo" (id=22) → "hotel-signage-demo-22"
        "Grand Hotel" (id=45) → "grand-hotel-45"
        "Spa & Wellness Center" (id=78) → "spa-wellness-center-78"

    Args:
        name: Organization name
        org_id: Organization ID (ensures uniqueness)

    Returns:
        URL-friendly slug string
    """
    # Convert to lowercase
    slug = name.lower()

    # Remove special characters (keep alphanumeric, spaces, and dashes)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)

    # Replace spaces with dashes
    slug = re.sub(r'\s+', '-', slug)

    # Replace multiple dashes with single dash
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing dashes
    slug = slug.strip('-')

    # Append ID for uniqueness
    return f"{slug}-{org_id}"


def slugify(text: str, max_length: Optional[int] = None) -> str:
    """
    Generic slugify function for any text.

    Args:
        text: Text to slugify
        max_length: Optional maximum length for the slug

    Returns:
        URL-friendly slug string
    """
    # Convert to lowercase
    slug = text.lower()

    # Remove special characters
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)

    # Replace spaces with dashes
    slug = re.sub(r'\s+', '-', slug)

    # Replace multiple dashes with single dash
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing dashes
    slug = slug.strip('-')

    # Truncate if max_length specified
    if max_length and len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')

    return slug
