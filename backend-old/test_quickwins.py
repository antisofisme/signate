#!/usr/bin/env python3
"""
Quick Wins Test Script
Tests all 4 Quick Wins implementations without starting the server
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def test_response_schemas():
    """Test Quick Win #1: Response Format Wrapper"""
    print("\n" + "="*60)
    print("TEST 1: Response Format Wrapper")
    print("="*60)

    from app.schemas.common import (
        success_response,
        paginated_response,
        error_response,
        APIResponse,
        PaginatedAPIResponse,
        ErrorResponse
    )

    # Test success response
    resp = success_response(
        data={"message": "Hello World"},
        request_id="test-123"
    )
    print("✅ success_response created:")
    print(f"   - success: {resp.success}")
    print(f"   - data: {resp.data}")
    print(f"   - meta.request_id: {resp.meta.request_id}")
    print(f"   - meta.timestamp: {resp.meta.timestamp}")

    # Test paginated response
    resp = paginated_response(
        data=[{"id": 1}, {"id": 2}],
        total=100,
        page=1,
        page_size=2,
        request_id="test-456"
    )
    print("✅ paginated_response created:")
    print(f"   - total: {resp.meta.total}")
    print(f"   - page: {resp.meta.page}")
    print(f"   - total_pages: {resp.meta.total_pages}")

    # Test error response
    resp, status = error_response(
        code="NOT_FOUND",
        message="Resource not found",
        status_code=404,
        request_id="test-789"
    )
    print("✅ error_response created:")
    print(f"   - success: {resp.success}")
    print(f"   - error.code: {resp.error.code}")
    print(f"   - error.message: {resp.error.message}")
    print(f"   - status_code: {status}")

    print("\n✅ Quick Win #1: PASSED")
    return True


def test_request_id_middleware():
    """Test Quick Win #2: Request ID Middleware"""
    print("\n" + "="*60)
    print("TEST 2: Request ID Middleware")
    print("="*60)

    from app.middleware.request_id import RequestIDMiddleware, get_request_id
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.testclient import TestClient
    from fastapi import FastAPI

    # Create test app
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        request_id = get_request_id(request)
        return {"request_id": request_id}

    client = TestClient(app)
    response = client.get("/test")

    print("✅ Middleware created and attached")
    print(f"   - Response status: {response.status_code}")
    print(f"   - X-Request-ID header: {response.headers.get('X-Request-ID')}")
    print(f"   - Request ID in body: {response.json()['request_id']}")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.json()["request_id"] == response.headers["X-Request-ID"]

    print("\n✅ Quick Win #2: PASSED")
    return True


def test_exceptions():
    """Test Quick Win #3: Standardized Error Responses"""
    print("\n" + "="*60)
    print("TEST 3: Standardized Error Responses")
    print("="*60)

    from app.core.exceptions import (
        APIException,
        NotFoundException,
        ValidationException,
        ConflictException,
        UnauthorizedException,
        register_exception_handlers
    )
    from fastapi import FastAPI, Request
    from starlette.testclient import TestClient
    from app.middleware.request_id import RequestIDMiddleware

    # Create test app
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)

    @app.get("/test/not-found")
    async def test_not_found():
        raise NotFoundException(
            message="Device not found",
            resource_type="Device",
            resource_id=999
        )

    @app.get("/test/validation")
    async def test_validation():
        raise ValidationException(
            message="Invalid email",
            field="email"
        )

    @app.get("/test/conflict")
    async def test_conflict():
        raise ConflictException(
            message="Duplicate entry",
            field="name"
        )

    client = TestClient(app)

    # Test NotFoundException
    response = client.get("/test/not-found")
    print("✅ NotFoundException:")
    print(f"   - Status: {response.status_code}")
    print(f"   - Error code: {response.json()['error']['code']}")
    print(f"   - Message: {response.json()['error']['message']}")
    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "NOT_FOUND"

    # Test ValidationException
    response = client.get("/test/validation")
    print("✅ ValidationException:")
    print(f"   - Status: {response.status_code}")
    print(f"   - Error code: {response.json()['error']['code']}")
    print(f"   - Field: {response.json()['error']['field']}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    # Test ConflictException
    response = client.get("/test/conflict")
    print("✅ ConflictException:")
    print(f"   - Status: {response.status_code}")
    print(f"   - Error code: {response.json()['error']['code']}")
    assert response.status_code == 409

    print("\n✅ Quick Win #3: PASSED")
    return True


def test_structured_logging():
    """Test Quick Win #4: Structured Logging"""
    print("\n" + "="*60)
    print("TEST 4: Structured Logging")
    print("="*60)

    from app.core.logging import (
        setup_logging,
        StructuredLogger,
        CustomJsonFormatter
    )
    import logging
    import io

    # Setup logging with JSON format
    setup_logging(log_level="INFO", log_format="json")
    logger = StructuredLogger(__name__)

    print("✅ Logging configured:")
    print(f"   - Root logger level: {logging.getLogger().level}")
    print(f"   - Handlers: {len(logging.getLogger().handlers)}")

    # Test different log levels
    logger.info("Test info log", test_field="value1")
    logger.warning("Test warning log", test_field="value2")
    logger.error("Test error log", test_field="value3")

    print("✅ Log methods work:")
    print("   - info() ✓")
    print("   - warning() ✓")
    print("   - error() ✓")

    print("\n✅ Quick Win #4: PASSED")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("QUICK WINS IMPLEMENTATION TEST SUITE")
    print("="*60)

    tests = [
        ("Response Format Wrapper", test_response_schemas),
        ("Request ID Middleware", test_request_id_middleware),
        ("Standardized Error Responses", test_exceptions),
        ("Structured Logging", test_structured_logging),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, True, None))
        except Exception as e:
            print(f"\n❌ {name}: FAILED")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False, str(e)))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result, _ in results if result)
    total = len(results)

    for name, result, error in results:
        status = "✅ PASSED" if result else f"❌ FAILED: {error}"
        print(f"{name}: {status}")

    print("\n" + "="*60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Quick Wins implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
