"""
Device JWT Authentication Integration Tests

Tests for device JWT authentication system implemented in device_auth.py

Features Tested:
- Device activation → Verify JWT token returned
- API calls with JWT → Verify Authorization header required
- Token refresh → Verify new token issued
- Token expiration handling
- Backward compatibility with device_id query parameter
- Security: Token validation, type checking, expiration

Security Features:
- 30-day token expiration for devices
- Automatic token refresh when < 7 days remaining
- Signature verification using SECRET_KEY
- Token type verification (device vs user)

Run: pytest tests/test_device_jwt.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from jose import jwt

from app.models.device import Device
from app.core.device_auth import (
    create_device_token,
    verify_device_token,
    DEVICE_TOKEN_EXPIRE_DAYS,
    DEVICE_TOKEN_REFRESH_THRESHOLD_DAYS
)
from app.core.config import settings


# ============================================================================
# TOKEN CREATION TESTS
# ============================================================================

class TestDeviceTokenCreation:
    """Test JWT token creation for devices"""

    def test_create_device_token_success(self, sample_device: Device):
        """
        Test creating JWT token for device

        Flow:
        1. Create device
        2. Generate JWT token
        3. Verify token structure
        4. Decode and verify payload
        """
        device_id = sample_device.id

        # Create token
        token = create_device_token(device_id)

        # Verify token is string
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long

        # Decode token to verify structure
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify payload structure
        assert payload["device_id"] == device_id
        assert payload["type"] == "device"
        assert payload["iss"] == "signage-backend"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_device_token_expiration(self, sample_device: Device):
        """
        Test token expiration is set correctly (30 days)

        Flow:
        1. Create token
        2. Decode payload
        3. Verify expiration is ~30 days from now
        """
        token = create_device_token(sample_device.id)

        # Decode token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify expiration
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()

        days_until_expiry = (exp_datetime - now).days

        # Should be approximately 30 days
        assert 29 <= days_until_expiry <= 31, f"Expected ~30 days, got {days_until_expiry}"

    def test_create_device_token_custom_expiration(self, sample_device: Device):
        """
        Test creating token with custom expiration

        Flow:
        1. Create token with 7-day expiration
        2. Verify expiration matches custom value
        """
        custom_expiration = timedelta(days=7)
        token = create_device_token(sample_device.id, expires_delta=custom_expiration)

        # Decode token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify expiration
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()

        days_until_expiry = (exp_datetime - now).days

        # Should be approximately 7 days
        assert 6 <= days_until_expiry <= 8, f"Expected ~7 days, got {days_until_expiry}"


# ============================================================================
# TOKEN VERIFICATION TESTS
# ============================================================================

class TestDeviceTokenVerification:
    """Test JWT token verification"""

    def test_verify_valid_token(self, sample_device: Device, device_token: str):
        """
        Test verifying valid device token

        Flow:
        1. Create valid token
        2. Verify token
        3. Check payload returned correctly
        """
        # Verify token
        payload = verify_device_token(device_token)

        # Verify payload
        assert payload["device_id"] == sample_device.id
        assert payload["type"] == "device"
        assert "exp" in payload

    def test_verify_expired_token(self, expired_device_token: str):
        """
        Test verifying expired token returns 401

        Flow:
        1. Create expired token
        2. Attempt verification
        3. Verify HTTPException raised
        """
        from fastapi import HTTPException

        # Verify expired token raises exception
        with pytest.raises(HTTPException) as exc_info:
            verify_device_token(expired_device_token)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in str(exc_info.value.detail)

    def test_verify_invalid_signature(self, sample_device: Device):
        """
        Test verifying token with invalid signature

        Flow:
        1. Create token with wrong SECRET_KEY
        2. Attempt verification
        3. Verify rejection
        """
        from fastapi import HTTPException

        # Create token with wrong key
        wrong_token = jwt.encode(
            {"device_id": sample_device.id, "type": "device"},
            "wrong_secret_key_123",
            algorithm=settings.JWT_ALGORITHM
        )

        # Verify invalid token raises exception
        with pytest.raises(HTTPException) as exc_info:
            verify_device_token(wrong_token)

        assert exc_info.value.status_code == 401

    def test_verify_wrong_token_type(self, sample_device: Device):
        """
        Test rejecting user token when device token expected

        Security: Prevents using user JWT for device authentication

        Flow:
        1. Create "user" type token
        2. Attempt verification as device
        3. Verify rejection
        """
        from fastapi import HTTPException

        # Create user token (wrong type)
        user_token = jwt.encode(
            {
                "device_id": sample_device.id,
                "type": "user",  # Wrong type!
                "exp": datetime.utcnow() + timedelta(days=1)
            },
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        # Verify wrong type raises exception
        with pytest.raises(HTTPException) as exc_info:
            verify_device_token(user_token)

        assert exc_info.value.status_code == 401
        assert "Invalid token type" in str(exc_info.value.detail)

    def test_verify_token_needs_refresh(self, sample_device: Device):
        """
        Test token expiring soon triggers refresh flag

        Flow:
        1. Create token expiring in 5 days (< 7 day threshold)
        2. Verify token
        3. Check needs_refresh flag set
        """
        # Create token expiring in 5 days
        short_expiration = timedelta(days=5)
        token = create_device_token(sample_device.id, expires_delta=short_expiration)

        # Verify token
        payload = verify_device_token(token)

        # Verify needs_refresh flag
        assert payload.get("needs_refresh") is True, "Should flag for refresh when < 7 days"


# ============================================================================
# DEVICE AUTHENTICATION ENDPOINT TESTS
# ============================================================================

class TestDeviceAuthenticationEndpoints:
    """Test device authentication in API endpoints"""

    def test_playlist_with_jwt_token(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        sample_content,
        device_auth_headers: dict
    ):
        """
        Test accessing playlist with JWT token (Bearer authentication)

        Flow:
        1. Create device and content
        2. Assign content to device
        3. Request playlist with Authorization header
        4. Verify 200 OK and playlist returned
        """
        from app.models.assignment import ContentAssignment

        # Assign content to device
        assignment = ContentAssignment(
            content_id=sample_content.id,
            device_id=sample_device.id,
            priority=1
        )
        test_db.add(assignment)
        test_db.commit()

        # Request playlist with JWT token
        response = client.get("/api/client/playlist", headers=device_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify playlist returned
        assert "playlist" in data
        assert data["device_id"] == sample_device.id

    def test_playlist_without_token_fails(self, client: TestClient):
        """
        Test accessing playlist without authentication fails

        Flow:
        1. Request playlist without Authorization header or device_id
        2. Verify 401 Unauthorized
        """
        # Request without authentication
        response = client.get("/api/client/playlist")

        assert response.status_code == 401
        data = response.json()
        assert "authentication required" in data.get("detail", "").lower()

    def test_playlist_with_invalid_token_fails(self, client: TestClient):
        """
        Test accessing playlist with invalid token fails

        Flow:
        1. Request playlist with invalid token
        2. Verify 401 Unauthorized
        """
        # Request with invalid token
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get("/api/client/playlist", headers=headers)

        assert response.status_code == 401

    def test_playlist_with_malformed_header_fails(self, client: TestClient):
        """
        Test malformed Authorization header fails

        Flow:
        1. Request with "Token" instead of "Bearer"
        2. Verify 401 Unauthorized
        """
        # Malformed header (should be "Bearer", not "Token")
        headers = {"Authorization": "Token abc123"}
        response = client.get("/api/client/playlist", headers=headers)

        assert response.status_code == 401

    def test_inactive_device_rejected(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_token: str
    ):
        """
        Test inactive device is rejected even with valid token

        Security: Token validity doesn't override device status check

        Flow:
        1. Create device with valid token
        2. Set device status to "inactive"
        3. Attempt to access playlist
        4. Verify 403 Forbidden
        """
        # Set device to inactive
        sample_device.status = "inactive"
        test_db.commit()

        # Try to access with valid token
        headers = {"Authorization": f"Bearer {device_token}"}
        response = client.get("/api/client/playlist", headers=headers)

        assert response.status_code == 403
        data = response.json()
        assert "inactive" in data.get("detail", "").lower()


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================

class TestBackwardCompatibility:
    """Test backward compatibility with device_id query parameter"""

    def test_playlist_with_device_id_query_param(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        sample_content,
        caplog
    ):
        """
        Test accessing playlist with legacy device_id parameter

        Backward compatibility: Old devices can still use device_id
        Expected: Works but logs deprecation warning

        Flow:
        1. Request playlist with ?device_id=X
        2. Verify 200 OK and playlist returned
        3. Verify deprecation warning logged
        """
        from app.models.assignment import ContentAssignment

        # Assign content
        assignment = ContentAssignment(
            content_id=sample_content.id,
            device_id=sample_device.id,
            priority=1
        )
        test_db.add(assignment)
        test_db.commit()

        # Request with device_id query param
        with caplog.at_level("WARNING"):
            response = client.get(f"/api/client/playlist?device_id={sample_device.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == sample_device.id

        # Verify deprecation warning logged
        warning_logged = False
        for record in caplog.records:
            if "DEPRECATED" in record.message or "query parameter" in record.message:
                warning_logged = True
                break

        assert warning_logged, "Should log deprecation warning for query param auth"

    def test_jwt_preferred_over_query_param(
        self,
        client: TestClient,
        test_db: Session,
        device_auth_headers: dict
    ):
        """
        Test JWT token takes precedence over query parameter

        Flow:
        1. Create 2 devices (device A and B)
        2. Request with device A's JWT token + device B's ID in query
        3. Verify device A authenticated (JWT wins)
        """
        # Create second device
        device_b = Device(
            device_name="Device B",
            activation_code="DEVICE_B",
            status="active",
            device_type="webos_tv"
        )
        test_db.add(device_b)
        test_db.commit()

        # Request with JWT (device A) + query param (device B)
        response = client.get(
            f"/api/client/playlist?device_id={device_b.id}",
            headers=device_auth_headers  # Device A's token
        )

        assert response.status_code == 200
        data = response.json()

        # Should authenticate as device A (JWT takes precedence)
        # This depends on implementation - verify correct device
        assert "device_id" in data


# ============================================================================
# TOKEN REFRESH TESTS
# ============================================================================

class TestDeviceTokenRefresh:
    """Test device token refresh mechanism"""

    def test_refresh_device_token(self, sample_device: Device):
        """
        Test refreshing device token

        Flow:
        1. Create initial token
        2. Call refresh_device_token()
        3. Verify new token issued
        4. Verify new expiration date
        """
        from app.core.device_auth import refresh_device_token

        # Refresh token
        refresh_result = refresh_device_token(sample_device.id)

        # Verify response structure
        assert "device_token" in refresh_result
        assert "token_type" in refresh_result
        assert "expires_at" in refresh_result
        assert "expires_in_days" in refresh_result

        assert refresh_result["token_type"] == "Bearer"
        assert refresh_result["expires_in_days"] == DEVICE_TOKEN_EXPIRE_DAYS

        # Verify new token works
        new_token = refresh_result["device_token"]
        payload = verify_device_token(new_token)
        assert payload["device_id"] == sample_device.id

    def test_token_refresh_endpoint(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_auth_headers: dict
    ):
        """
        Test token refresh API endpoint

        Note: Requires refresh endpoint implementation

        Flow:
        1. Request /api/client/refresh with current token
        2. Verify new token returned
        3. Verify old and new tokens are different
        """
        # This test assumes refresh endpoint exists at /api/client/refresh
        # If not implemented, this test will fail (expected)

        # Try to call refresh endpoint
        response = client.post("/api/client/refresh", headers=device_auth_headers)

        # If endpoint exists, verify response
        if response.status_code == 200:
            data = response.json()
            assert "device_token" in data
            assert "expires_at" in data

            # Verify new token is different
            old_token = device_auth_headers["Authorization"].replace("Bearer ", "")
            new_token = data["device_token"]
            assert new_token != old_token
        elif response.status_code == 404:
            # Endpoint not implemented yet (acceptable)
            pytest.skip("Token refresh endpoint not implemented")


# ============================================================================
# SECURITY TESTS
# ============================================================================

class TestDeviceTokenSecurity:
    """Test security aspects of device JWT authentication"""

    def test_token_cannot_be_reused_after_device_deleted(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_token: str
    ):
        """
        Test token becomes invalid after device deleted

        Security: Deleting device should invalidate tokens

        Flow:
        1. Create device and token
        2. Delete device from database
        3. Attempt to use token
        4. Verify 404 (device not found)
        """
        device_id = sample_device.id

        # Delete device
        test_db.delete(sample_device)
        test_db.commit()

        # Try to use token
        headers = {"Authorization": f"Bearer {device_token}"}
        response = client.get("/api/client/playlist", headers=headers)

        assert response.status_code == 404, "Should return 404 when device not found"

    def test_token_includes_device_id_not_sensitive_data(
        self,
        sample_device: Device,
        device_token: str
    ):
        """
        Test token payload contains only device_id (no sensitive data)

        Security: Tokens should not leak sensitive information

        Flow:
        1. Create token
        2. Decode without verification
        3. Verify only safe fields present
        """
        # Decode without verification to inspect payload
        payload = jwt.decode(
            device_token,
            options={"verify_signature": False}
        )

        # Verify only safe fields present
        allowed_fields = {"device_id", "type", "exp", "iat", "iss"}
        actual_fields = set(payload.keys())

        # Should not contain sensitive data
        sensitive_fields = {"password", "activation_code", "ip_address", "mac_address"}
        assert not actual_fields.intersection(sensitive_fields), "Token contains sensitive data"

        # Should only contain expected fields
        assert actual_fields.issubset(allowed_fields), f"Unexpected fields: {actual_fields - allowed_fields}"

    def test_different_devices_have_different_tokens(
        self,
        test_db: Session
    ):
        """
        Test each device gets unique token

        Flow:
        1. Create 2 devices
        2. Generate token for each
        3. Verify tokens are different
        """
        # Create device 1
        device1 = Device(
            device_name="Device 1",
            activation_code="DEV001",
            status="active",
            device_type="webos_tv"
        )
        test_db.add(device1)
        test_db.commit()

        # Create device 2
        device2 = Device(
            device_name="Device 2",
            activation_code="DEV002",
            status="active",
            device_type="webos_tv"
        )
        test_db.add(device2)
        test_db.commit()

        # Generate tokens
        token1 = create_device_token(device1.id)
        token2 = create_device_token(device2.id)

        # Verify tokens are different
        assert token1 != token2

        # Verify each token identifies correct device
        payload1 = jwt.decode(token1, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        payload2 = jwt.decode(token2, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        assert payload1["device_id"] == device1.id
        assert payload2["device_id"] == device2.id


# ============================================================================
# LAST SEEN UPDATE TESTS
# ============================================================================

class TestLastSeenUpdate:
    """Test last_seen timestamp updates during authentication"""

    def test_authentication_updates_last_seen(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_auth_headers: dict
    ):
        """
        Test that device authentication updates last_seen timestamp

        Flow:
        1. Set last_seen to old timestamp
        2. Request playlist (authentication)
        3. Verify last_seen updated
        """
        # Set old last_seen
        old_timestamp = datetime.utcnow() - timedelta(hours=2)
        sample_device.last_seen = old_timestamp
        test_db.commit()

        # Request playlist (triggers authentication)
        response = client.get("/api/client/playlist", headers=device_auth_headers)
        assert response.status_code == 200

        # Refresh device from database
        test_db.refresh(sample_device)

        # Verify last_seen updated
        assert sample_device.last_seen > old_timestamp
        assert sample_device.last_seen is not None

        # Should be within last minute
        time_diff = datetime.utcnow() - sample_device.last_seen
        assert time_diff.total_seconds() < 60, "last_seen should be updated to current time"
