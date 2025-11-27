"""
Unit Tests for shared/auth.py
Tests password hashing, JWT tokens, and role-based access control
"""

import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

# Mock settings before importing auth module
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for all tests"""
    with patch('shared.auth.settings') as mock:
        mock.SECRET_KEY = "test-secret-key-for-unit-tests-only"
        mock.ALGORITHM = "HS256"
        mock.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        yield mock


# Now import after mocking
from shared.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_device_token,
    decode_token,
    verify_access_token,
    verify_refresh_token,
    verify_device_token,
    create_token_payload,
    extract_user_from_token,
    extract_device_from_token,
    get_role_level,
    has_role,
    is_super_admin,
    is_admin,
    is_manager,
    is_same_organization,
    can_access_organization,
    CurrentUser,
    Role,
    PermissionChecker,
)
from shared.errors import AuthenticationError


# =============================================================================
# PASSWORD HASHING TESTS
# =============================================================================

class TestPasswordHashing:
    """Tests for password hashing functions"""

    def test_hash_password(self):
        """Password should be hashed"""
        password = "SecurePass123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Correct password should verify"""
        password = "SecurePass123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Wrong password should not verify"""
        password = "SecurePass123!"
        hashed = get_password_hash(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_same_password_different_hashes(self):
        """Same password should produce different hashes (salt)"""
        password = "SecurePass123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2  # Different salts
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


# =============================================================================
# JWT TOKEN GENERATION TESTS
# =============================================================================

class TestAccessToken:
    """Tests for access token generation"""

    def test_create_access_token(self):
        """Should create valid access token"""
        data = {"sub": "1", "username": "testuser", "role": "admin"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    def test_access_token_contains_type(self):
        """Access token should have type=access"""
        data = {"sub": "1", "username": "testuser", "role": "admin"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload["type"] == "access"

    def test_access_token_contains_data(self):
        """Access token should contain provided data"""
        data = {"sub": "1", "username": "testuser", "role": "admin"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload["sub"] == "1"
        assert payload["username"] == "testuser"
        assert payload["role"] == "admin"

    def test_access_token_has_expiration(self):
        """Access token should have exp claim"""
        data = {"sub": "1", "username": "testuser", "role": "admin"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert "exp" in payload
        assert "iat" in payload


class TestRefreshToken:
    """Tests for refresh token generation"""

    def test_create_refresh_token(self):
        """Should create valid refresh token"""
        data = {"sub": "1"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

    def test_refresh_token_type(self):
        """Refresh token should have type=refresh"""
        data = {"sub": "1"}
        token = create_refresh_token(data)
        payload = decode_token(token)

        assert payload["type"] == "refresh"


class TestDeviceToken:
    """Tests for device token generation"""

    def test_create_device_token(self):
        """Should create valid device token"""
        token = create_device_token(device_id=1, organization_id=10)

        assert token is not None
        assert isinstance(token, str)

    def test_device_token_type(self):
        """Device token should have type=device"""
        token = create_device_token(device_id=1, organization_id=10)
        payload = decode_token(token)

        assert payload["type"] == "device"

    def test_device_token_contains_device_info(self):
        """Device token should contain device and org info"""
        token = create_device_token(device_id=1, organization_id=10)
        payload = decode_token(token)

        assert payload["sub"] == "1"
        assert payload["organization_id"] == 10


# =============================================================================
# TOKEN VALIDATION TESTS
# =============================================================================

class TestTokenValidation:
    """Tests for token validation functions"""

    def test_verify_access_token_valid(self):
        """Should verify valid access token"""
        data = {"sub": "1", "username": "testuser", "role": "admin"}
        token = create_access_token(data)

        payload = verify_access_token(token)
        assert payload["sub"] == "1"

    def test_verify_access_token_wrong_type(self):
        """Should reject refresh token when expecting access"""
        data = {"sub": "1"}
        token = create_refresh_token(data)

        with pytest.raises(AuthenticationError):
            verify_access_token(token)

    def test_verify_refresh_token_valid(self):
        """Should verify valid refresh token"""
        data = {"sub": "1"}
        token = create_refresh_token(data)

        payload = verify_refresh_token(token)
        assert payload["sub"] == "1"

    def test_verify_device_token_valid(self):
        """Should verify valid device token"""
        token = create_device_token(device_id=1, organization_id=10)

        payload = verify_device_token(token)
        assert payload["sub"] == "1"
        assert payload["organization_id"] == 10

    def test_verify_device_token_wrong_type(self):
        """Should reject user token when expecting device"""
        data = {"sub": "1", "username": "testuser", "role": "admin"}
        token = create_access_token(data)

        with pytest.raises(AuthenticationError):
            verify_device_token(token)

    def test_invalid_token_rejected(self):
        """Should reject invalid token"""
        with pytest.raises(AuthenticationError):
            decode_token("invalid.token.here")


# =============================================================================
# TOKEN PAYLOAD HELPERS TESTS
# =============================================================================

class TestTokenPayloadHelpers:
    """Tests for token payload helper functions"""

    def test_create_token_payload(self):
        """Should create standardized payload"""
        payload = create_token_payload(
            user_id=1,
            username="testuser",
            role="admin",
            organization_id=10
        )

        assert payload["sub"] == "1"
        assert payload["username"] == "testuser"
        assert payload["role"] == "admin"
        assert payload["organization_id"] == 10

    def test_create_token_payload_with_permissions(self):
        """Should include permissions in payload"""
        permissions = {"users": ["view", "create"], "devices": ["view"]}
        payload = create_token_payload(
            user_id=1,
            username="testuser",
            role="admin",
            permissions=permissions
        )

        assert payload["permissions"] == permissions

    def test_extract_user_from_token(self):
        """Should extract user info from token"""
        data = create_token_payload(
            user_id=1,
            username="testuser",
            role="admin",
            organization_id=10,
            permissions={"users": ["view"]}
        )
        token = create_access_token(data)

        user_info = extract_user_from_token(token)

        assert user_info["user_id"] == 1
        assert user_info["username"] == "testuser"
        assert user_info["role"] == "admin"
        assert user_info["organization_id"] == 10
        assert user_info["permissions"] == {"users": ["view"]}

    def test_extract_device_from_token(self):
        """Should extract device info from token"""
        token = create_device_token(device_id=5, organization_id=10)

        device_info = extract_device_from_token(token)

        assert device_info["device_id"] == 5
        assert device_info["organization_id"] == 10


# =============================================================================
# ROLE HIERARCHY TESTS
# =============================================================================

class TestRoleHierarchy:
    """Tests for role hierarchy and permission checks"""

    def test_get_role_level_super_admin(self):
        """Super admin should have highest level"""
        assert get_role_level("super_admin") == 4
        assert get_role_level("SUPER_ADMIN") == 4

    def test_get_role_level_admin(self):
        """Admin should have level 3"""
        assert get_role_level("admin") == 3

    def test_get_role_level_manager(self):
        """Manager should have level 2"""
        assert get_role_level("manager") == 2

    def test_get_role_level_viewer(self):
        """Viewer should have level 1"""
        assert get_role_level("viewer") == 1

    def test_get_role_level_unknown(self):
        """Unknown role should have level 0"""
        assert get_role_level("unknown_role") == 0


class TestHasRole:
    """Tests for has_role function"""

    def test_super_admin_has_all_roles(self):
        """Super admin should have all roles"""
        user = CurrentUser(id=1, username="admin", role="super_admin")

        assert has_role(user, "super_admin") is True
        assert has_role(user, "admin") is True
        assert has_role(user, "manager") is True
        assert has_role(user, "viewer") is True

    def test_admin_has_admin_and_below(self):
        """Admin should have admin and below"""
        user = CurrentUser(id=1, username="admin", role="admin")

        assert has_role(user, "super_admin") is False
        assert has_role(user, "admin") is True
        assert has_role(user, "manager") is True
        assert has_role(user, "viewer") is True

    def test_viewer_only_has_viewer(self):
        """Viewer should only have viewer role"""
        user = CurrentUser(id=1, username="user", role="viewer")

        assert has_role(user, "super_admin") is False
        assert has_role(user, "admin") is False
        assert has_role(user, "manager") is False
        assert has_role(user, "viewer") is True


class TestRoleCheckers:
    """Tests for specific role checker functions"""

    def test_is_super_admin(self):
        """Should correctly identify super admin"""
        super_admin = CurrentUser(id=1, username="sa", role="super_admin")
        admin = CurrentUser(id=2, username="admin", role="admin")

        assert is_super_admin(super_admin) is True
        assert is_super_admin(admin) is False

    def test_is_admin(self):
        """Should correctly identify admin or higher"""
        super_admin = CurrentUser(id=1, username="sa", role="super_admin")
        admin = CurrentUser(id=2, username="admin", role="admin")
        manager = CurrentUser(id=3, username="mgr", role="manager")

        assert is_admin(super_admin) is True
        assert is_admin(admin) is True
        assert is_admin(manager) is False

    def test_is_manager(self):
        """Should correctly identify manager or higher"""
        admin = CurrentUser(id=1, username="admin", role="admin")
        manager = CurrentUser(id=2, username="mgr", role="manager")
        viewer = CurrentUser(id=3, username="user", role="viewer")

        assert is_manager(admin) is True
        assert is_manager(manager) is True
        assert is_manager(viewer) is False


# =============================================================================
# ORGANIZATION ACCESS TESTS
# =============================================================================

class TestOrganizationAccess:
    """Tests for organization access control"""

    def test_is_same_organization(self):
        """Should correctly check organization membership"""
        user = CurrentUser(id=1, username="user", role="viewer", organization_id=10)

        assert is_same_organization(user, 10) is True
        assert is_same_organization(user, 20) is False

    def test_admin_can_access_any_org(self):
        """Admin should access any organization"""
        admin = CurrentUser(id=1, username="admin", role="admin", organization_id=10)

        assert can_access_organization(admin, 10) is True
        assert can_access_organization(admin, 20) is True

    def test_viewer_can_only_access_own_org(self):
        """Viewer should only access own organization"""
        viewer = CurrentUser(id=1, username="user", role="viewer", organization_id=10)

        assert can_access_organization(viewer, 10) is True
        assert can_access_organization(viewer, 20) is False


# =============================================================================
# PERMISSION CHECKER CLASS TESTS
# =============================================================================

class TestPermissionChecker:
    """Tests for PermissionChecker class"""

    def test_super_admin_can_edit_any_user(self):
        """Super admin should edit any user"""
        super_admin = CurrentUser(id=1, username="sa", role="super_admin")
        checker = PermissionChecker(super_admin)

        assert checker.can_edit_user(target_user_id=2, target_organization_id=10) is True
        assert checker.can_edit_user(target_user_id=3, target_organization_id=20) is True

    def test_admin_can_edit_any_user(self):
        """Admin should edit any user"""
        admin = CurrentUser(id=1, username="admin", role="admin", organization_id=10)
        checker = PermissionChecker(admin)

        assert checker.can_edit_user(target_user_id=2, target_organization_id=10) is True
        assert checker.can_edit_user(target_user_id=3, target_organization_id=20) is True

    def test_manager_can_edit_same_org_only(self):
        """Manager should only edit users in same org"""
        manager = CurrentUser(id=1, username="mgr", role="manager", organization_id=10)
        checker = PermissionChecker(manager)

        assert checker.can_edit_user(target_user_id=2, target_organization_id=10) is True
        assert checker.can_edit_user(target_user_id=3, target_organization_id=20) is False

    def test_viewer_cannot_edit_anyone(self):
        """Viewer should not edit anyone"""
        viewer = CurrentUser(id=1, username="user", role="viewer", organization_id=10)
        checker = PermissionChecker(viewer)

        assert checker.can_edit_user(target_user_id=2, target_organization_id=10) is False

    def test_cannot_delete_self(self):
        """User should not delete themselves"""
        admin = CurrentUser(id=1, username="admin", role="admin", organization_id=10)
        checker = PermissionChecker(admin)

        assert checker.can_delete_user(
            target_user_id=1,  # Same as current user
            target_organization_id=10,
            target_role="admin"
        ) is False

    def test_admin_can_create_non_super_admin_roles(self):
        """Admin should create any role except super_admin"""
        admin = CurrentUser(id=1, username="admin", role="admin", organization_id=10)
        checker = PermissionChecker(admin)

        assert checker.can_create_user_with_role("admin", 10) is True
        assert checker.can_create_user_with_role("manager", 10) is True
        assert checker.can_create_user_with_role("viewer", 10) is True
        assert checker.can_create_user_with_role(Role.SUPER_ADMIN, 10) is False

    def test_only_admins_can_manage_organizations(self):
        """Only admins should manage organizations"""
        admin = CurrentUser(id=1, username="admin", role="admin")
        manager = CurrentUser(id=2, username="mgr", role="manager", organization_id=10)

        assert PermissionChecker(admin).can_manage_organization() is True
        assert PermissionChecker(manager).can_manage_organization() is False
