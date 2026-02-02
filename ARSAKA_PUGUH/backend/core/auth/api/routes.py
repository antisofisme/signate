"""
Auth API Routes

FastAPI router for authentication endpoints.
Source: INFRA-LAY2-005-identity-api-contracts.md
"""

import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

# Cookie security settings based on environment
# In development/staging without HTTPS, we can't use Secure cookies
_ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
_IS_PRODUCTION = _ENVIRONMENT in ("production", "prod", "live")
COOKIE_SECURE = _IS_PRODUCTION  # Only Secure in production with HTTPS
COOKIE_SAMESITE = "strict" if _IS_PRODUCTION else "lax"  # Lax allows cross-origin in dev

from ..use_cases import (
    RegisterUseCase,
    RegisterRequest as RegisterInput,
    LoginUseCase,
    LoginRequest as LoginInput,
    VerifyEmailUseCase,
    ForgotPasswordUseCase,
    ResetPasswordUseCase,
)
from ..exceptions import (
    ValidationError,
    EmailExistsError,
    InvalidCredentialsError,
    AccountNotVerifiedError,
    AccountSuspendedError,
    TokenExpiredError,
    TokenInvalidError,
)
from .schemas import (
    RegisterRequest,
    RegisterResponse,
    RegisterData,
    LoginRequest,
    LoginResponse,
    LoginData,
    UserInfo,
    TenantInfo,
    ProjectInfo,
    VerifyEmailResponse,
    VerifyEmailData,
    VerifyEmailUserInfo,
    VerifyEmailTenant,
    VerifyEmailProject,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ForgotPasswordData,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ResetPasswordData,
    RefreshResponse,
    RefreshData,
    LogoutResponse,
    LogoutData,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResendVerificationData,
    ErrorResponse,
    ErrorDetail,
)
from .dependencies import (
    get_register_use_case,
    get_login_use_case,
    get_verify_email_use_case,
    get_forgot_password_use_case,
    get_reset_password_use_case,
    get_current_user,
    get_token_service,
    get_client_ip,
    get_user_agent,
    get_user_repository,
    get_tenant_loader,
)
from ..interfaces.token_service import ITokenService, TokenPayload


router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# Registration
# ============================================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Email already exists"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
)
async def register(
    request: RegisterRequest,
    use_case: RegisterUseCase = Depends(get_register_use_case),
):
    """
    Register a new user with email and password.

    Source: INFRA-LAY2-005 §1
    """
    try:
        input_dto = RegisterInput(
            email=request.email,
            password=request.password,
            display_name=request.display_name,
        )
        result = await use_case.execute(input_dto)

        return RegisterResponse(
            data=RegisterData(
                user_id=result.user_id,
                email=result.email,
                display_name=request.display_name,
                status=result.status,
            )
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": e.message,
                "field": e.field,
            }
        )
    except EmailExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "EMAIL_EXISTS",
                "message": "An account with this email already exists",
            }
        )


# ============================================================================
# Email Verification
# ============================================================================

@router.get(
    "/verify-email",
    response_model=VerifyEmailResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    },
)
async def verify_email(
    token: str = Query(..., description="Verification token from email"),
    use_case: VerifyEmailUseCase = Depends(get_verify_email_use_case),
):
    """
    Verify user's email address using token from email link.

    Source: INFRA-LAY2-005 §2
    """
    try:
        result = await use_case.execute(token)

        tenant = None
        if result.tenant:
            tenant = VerifyEmailTenant(
                tenant_id=result.tenant["tenant_id"],
                name=result.tenant["name"],
                slug=result.tenant["slug"],
            )

        project = None
        if result.project:
            project = VerifyEmailProject(
                project_id=result.project["project_id"],
                name=result.project["name"],
                slug=result.project["slug"],
            )

        return VerifyEmailResponse(
            data=VerifyEmailData(
                user=VerifyEmailUserInfo(
                    user_id=result.user_id,
                    email=result.email,
                    display_name=None,  # Not returned by use case
                    status=result.status,
                ),
                access_token=result.access_token,
                refresh_token=result.refresh_token,
                expires_in=result.expires_in,
                tenant=tenant,
                project=project,
                redirect_url=result.redirect_url,
            )
        )
    except (TokenExpiredError, TokenInvalidError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Verification link is invalid or expired",
            }
        )


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
)
async def resend_verification(
    request: ResendVerificationRequest,
):
    """
    Resend verification email.

    Always returns success to prevent email enumeration.
    Source: INFRA-LAY2-005 §2
    """
    # TODO: Implement resend verification logic
    # For now, return generic success message
    return ResendVerificationResponse(
        data=ResendVerificationData()
    )


# ============================================================================
# Login
# ============================================================================

@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account not verified or suspended"},
        423: {"model": ErrorResponse, "description": "Account locked"},
    },
)
async def login(
    request: LoginRequest,
    http_request: Request,
    response: Response,
    use_case: LoginUseCase = Depends(get_login_use_case),
):
    """
    Login with email and password.

    Source: INFRA-LAY2-005 §3
    """
    try:
        input_dto = LoginInput(
            email=request.email,
            password=request.password,
            remember_me=request.remember_me,
            ip_address=get_client_ip(http_request),
            user_agent=get_user_agent(http_request),
        )
        result = await use_case.execute(input_dto)

        # Convert tenants
        tenants = [
            TenantInfo(
                tenant_id=t.tenant_id,
                name=t.name,
                slug=t.slug,
                role=t.role,
                projects=[
                    ProjectInfo(
                        project_id=p["project_id"],
                        name=p["name"],
                        slug=p["slug"],
                        is_default=p.get("is_default", False),
                    )
                    for p in t.projects
                ],
            )
            for t in result.tenants
        ]

        # Convert active tenant
        active_tenant = None
        if result.active_tenant:
            active_tenant = TenantInfo(
                tenant_id=result.active_tenant.tenant_id,
                name=result.active_tenant.name,
                slug=result.active_tenant.slug,
                role=result.active_tenant.role,
                projects=[
                    ProjectInfo(
                        project_id=p["project_id"],
                        name=p["name"],
                        slug=p["slug"],
                        is_default=p.get("is_default", False),
                    )
                    for p in result.active_tenant.projects
                ],
            )

        # Convert active project
        active_project = None
        if result.active_project:
            active_project = ProjectInfo(
                project_id=result.active_project["project_id"],
                name=result.active_project["name"],
                slug=result.active_project["slug"],
                is_default=result.active_project.get("is_default", False),
            )

        # Set tokens in httpOnly cookies for security
        # Access token - shorter expiry, used for API requests
        response.set_cookie(
            key="access_token",
            value=result.access_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=result.expires_in,
            path="/",
        )

        # Refresh token - longer expiry, used only for token refresh
        refresh_max_age = 7 * 24 * 60 * 60  # 7 days
        if request.remember_me:
            refresh_max_age = 30 * 24 * 60 * 60  # 30 days
        response.set_cookie(
            key="refresh_token",
            value=result.refresh_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=refresh_max_age,
            path="/api/v1/auth",  # Only sent to auth endpoints
        )

        return LoginResponse(
            data=LoginData(
                user=UserInfo(
                    user_id=result.user_id,
                    email=result.email,
                    display_name=result.display_name,
                ),
                access_token=None,  # Don't expose in response body
                refresh_token=None,  # Don't expose in response body
                expires_in=result.expires_in,
                tenants=tenants,
                active_tenant=active_tenant,
                active_project=active_project,
                requires_context_selection=result.requires_context_selection,
                redirect_url=result.redirect_url,
            )
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password",
            }
        )
    except AccountNotVerifiedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCOUNT_NOT_VERIFIED",
                "message": "Please verify your email before logging in",
                "can_resend": True,
            }
        )
    except AccountSuspendedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCOUNT_SUSPENDED",
                "message": "Your account has been suspended. Please contact support.",
            }
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": e.message,
                "field": e.field,
            }
        )


# ============================================================================
# Password Reset
# ============================================================================

@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
async def forgot_password(
    request: ForgotPasswordRequest,
    use_case: ForgotPasswordUseCase = Depends(get_forgot_password_use_case),
):
    """
    Request password reset email.

    Always returns success to prevent email enumeration.
    Source: INFRA-LAY2-005 §7
    """
    result = await use_case.execute(request.email)

    return ForgotPasswordResponse(
        data=ForgotPasswordData(message=result.message)
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    },
)
async def reset_password(
    request: ResetPasswordRequest,
    use_case: ResetPasswordUseCase = Depends(get_reset_password_use_case),
):
    """
    Reset password using token from email.

    Source: INFRA-LAY2-005 §7
    """
    try:
        result = await use_case.execute(request.token, request.new_password)

        return ResetPasswordResponse(
            data=ResetPasswordData(message=result.message)
        )
    except (TokenExpiredError, TokenInvalidError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Reset link is invalid or expired",
            }
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": e.message,
                "field": e.field,
            }
        )


# ============================================================================
# Token Management
# ============================================================================

@router.post(
    "/refresh",
    response_model=RefreshResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
    },
)
async def refresh_token(
    request: Request,
    response: Response,
    token_service: ITokenService = Depends(get_token_service),
    user_repo = Depends(get_user_repository),
    tenant_loader = Depends(get_tenant_loader),
):
    """
    Refresh access token using refresh token from cookie.

    SECURITY: Implements refresh token rotation.
    - Old refresh token is revoked immediately after use
    - New refresh token is issued with each refresh
    - If an old token is used again (replay attack), it will fail

    Source: INFRA-LAY2-005 §6
    """
    from uuid import UUID
    import jwt

    # Get refresh token from cookie
    old_refresh_token = request.cookies.get("refresh_token")
    if not old_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_REFRESH_TOKEN",
                "message": "Please log in again",
            }
        )

    try:
        # SECURITY: Verify refresh token and get user_id
        user_id = await token_service.verify_refresh_token(old_refresh_token)

        # SECURITY: Immediately revoke the old refresh token to prevent reuse
        # This protects against refresh token theft - if attacker uses stolen token,
        # legitimate user's next refresh will fail, alerting them to compromise
        try:
            # Decode to get jti and exp for revocation
            old_payload = jwt.decode(
                old_refresh_token,
                options={"verify_signature": False}  # Already verified above
            )
            old_jti = old_payload.get("jti")
            if old_jti:
                from datetime import datetime
                old_exp = datetime.fromtimestamp(old_payload.get("exp", 0))
                await token_service.revoke_token(old_jti, old_exp)
        except Exception:
            pass  # Continue even if revocation fails

        # Load user from database
        user = await user_repo.get_by_id(UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "USER_NOT_FOUND",
                    "message": "User not found. Please log in again.",
                }
            )

        # Check if user is still active
        if user.status.value not in ("verified", "active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ACCOUNT_INACTIVE",
                    "message": "Your account is no longer active.",
                }
            )

        # Load tenant context
        tenants = await tenant_loader.get_user_tenants(user_id)

        # Determine active tenant/project (use first tenant if available)
        active_tenant_id = None
        active_project_id = None
        if tenants:
            active_tenant_id = tenants[0].tenant_id

        # SECURITY: Create new token pair (rotation)
        # This includes a new refresh token with a fresh jti
        from ..interfaces.token_service import TenantContext
        tenant_contexts = [
            TenantContext(
                tenant_id=t.tenant_id,
                slug=t.slug,
                role=t.role,
                projects=getattr(t, 'projects', []),
            )
            for t in tenants
        ]

        token_pair = await token_service.create_token_pair(
            user_id=user_id,
            email=user.email,
            display_name=user.display_name,
            tenants=tenant_contexts,
            active_tenant_id=active_tenant_id,
            active_project_id=active_project_id,
            remember_me=False,  # Don't extend on refresh
        )

        # Set new access token in httpOnly cookie
        response.set_cookie(
            key="access_token",
            value=token_pair.access_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=token_pair.expires_in,
            path="/",
        )

        # SECURITY: Set NEW refresh token in httpOnly cookie (rotation)
        refresh_max_age = 7 * 24 * 60 * 60  # 7 days
        response.set_cookie(
            key="refresh_token",
            value=token_pair.refresh_token,  # NEW token, not the old one
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=refresh_max_age,
            path="/api/v1/auth",  # Only sent to auth endpoints
        )

        return RefreshResponse(
            data=RefreshData(
                access_token=None,  # Don't expose in response body
                expires_in=token_pair.expires_in,
            )
        )
    except (TokenExpiredError, TokenInvalidError):
        # SECURITY: Clear cookies on invalid token to force re-login
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/api/v1/auth")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_REFRESH_TOKEN",
                "message": "Please log in again",
            }
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
async def logout(
    response: Response,
    current_user: TokenPayload = Depends(get_current_user),
    token_service: ITokenService = Depends(get_token_service),
):
    """
    Logout and invalidate tokens.

    Source: INFRA-LAY2-005 §6
    """
    # Revoke the current access token
    if current_user.jti and current_user.exp:
        await token_service.revoke_token(current_user.jti, current_user.exp)

    # Clear access token cookie
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=True,
        samesite="strict",
    )

    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return LogoutResponse(
        data=LogoutData()
    )
