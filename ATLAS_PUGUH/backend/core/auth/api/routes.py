"""
Auth API Routes

FastAPI router for authentication endpoints.
Source: INFRA-LAY2-005-identity-api-contracts.md
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

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

        return LoginResponse(
            data=LoginData(
                user=UserInfo(
                    user_id=result.user_id,
                    email=result.email,
                    display_name=result.display_name,
                ),
                access_token=result.access_token,
                refresh_token=result.refresh_token,
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
    token_service: ITokenService = Depends(get_token_service),
):
    """
    Refresh access token using refresh token from cookie.

    Source: INFRA-LAY2-005 §6
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_REFRESH_TOKEN",
                "message": "Please log in again",
            }
        )

    try:
        # Verify refresh token and get user_id
        user_id = await token_service.verify_refresh_token(refresh_token)

        # Create new access token
        # TODO: Load user and tenant context to create full token
        access_token = await token_service.create_access_token(
            user_id=user_id,
            email="",  # Would need to load from DB
            display_name=None,
            tenants=[],
            active_tenant_id=None,
            active_project_id=None,
        )

        return RefreshResponse(
            data=RefreshData(
                access_token=access_token,
                expires_in=900,  # 15 minutes
            )
        )
    except (TokenExpiredError, TokenInvalidError):
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

    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/",
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return LogoutResponse(
        data=LogoutData()
    )
