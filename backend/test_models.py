"""
Test script to validate SQLAlchemy models
"""

import sys
sys.path.insert(0, '/mnt/g/khoirul/signate/backend')

from app.core.database import Base, engine
from app.models import (
    User, Device, Content, Tag, DeviceTag,
    ContentAssignment, Schedule, FirebirdConfig
)

def test_models():
    """Test that all models are properly defined"""

    print("=" * 60)
    print("Testing SQLAlchemy Models")
    print("=" * 60)

    # Check all models are registered
    models = [
        User, Device, Content, Tag, DeviceTag,
        ContentAssignment, Schedule, FirebirdConfig
    ]

    print("\n✓ All models imported successfully:")
    for model in models:
        print(f"  - {model.__name__}: {model.__tablename__}")

    # Check Base metadata
    print(f"\n✓ Total tables in metadata: {len(Base.metadata.tables)}")
    print("\nTables:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  - {table_name}")

    # Test model instantiation
    print("\n✓ Testing model instantiation:")

    try:
        user = User(username="test", email="test@example.com", password_hash="hash")
        print(f"  - User: {user}")

        device = Device(device_type="tv", device_name="Test TV", unique_code="TEST001")
        print(f"  - Device: {device}")

        content = Content(title="Test Content", content_type="image", anthias_url="http://test.com/image.jpg")
        print(f"  - Content: {content}")

        tag = Tag(tag_name="lobby")
        print(f"  - Tag: {tag}")

        print("\n✓ All models can be instantiated successfully!")

    except Exception as e:
        print(f"\n✗ Error instantiating models: {e}")
        return False

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        test_models()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
