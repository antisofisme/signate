"""
Tenant API Routes

FastAPI router for tenant management endpoints.

Source: INFRA-LAY2-005-identity-api-contracts.md
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .schemas import (
    # Request
    CreateTenantRequest,
    UpdateTenantRequest,
    InviteMemberRequest,
    AcceptInvitationRequest,
    UpdateMemberRoleRequest,
    # Response
    TenantCreateResponse,
    TenantDetailResponse,
    TenantUpdateResponse,
    TenantDeleteResponse,
    ListTenantsResponse,
    TenantWithMembershipResponse,
    TenantResponse,
    TenantPlanLimits,
    InvitationCreateResponse,
    InvitationResponse,
    InvitationAcceptResponse,
    ListMembersResponse,
    MemberResponse,
    MembershipResponse,
    MemberRoleUpdateResponse,
    MemberRemoveResponse,
    ListInvitationsResponse,
)
from .dependencies import (
    get_create_tenant_use_case,
    get_update_tenant_use_case,
    get_delete_tenant_use_case,
    get_get_tenant_use_case,
    get_list_tenants_use_case,
    get_invite_member_use_case,
    get_accept_invitation_use_case,
    get_remove_member_use_case,
    get_update_member_role_use_case,
    get_list_members_use_case,
    get_invitation_repo,
)
from ..use_cases.create_tenant import CreateTenantInput
from ..use_cases.update_tenant import UpdateTenantInput
from ..use_cases.delete_tenant import DeleteTenantInput
from ..use_cases.get_tenant import GetTenantInput
from ..use_cases.list_tenants import ListTenantsInput
from ..use_cases.invite_member import InviteMemberInput
from ..use_cases.accept_invitation import AcceptInvitationInput
from ..use_cases.remove_member import RemoveMemberInput
from ..use_cases.update_member_role import UpdateMemberRoleInput
from ..use_cases.list_members import ListMembersInput
from ..domain.membership import MemberRole
from ..exceptions import (
    TenantNotFoundError,
    TenantSlugExistsError,
    NotMemberError,
    InsufficientPermissionError,
    AlreadyMemberError,
    CannotRemoveOwnerError,
    CannotDemoteOwnerError,
    MaxMembersExceededError,
    InvitationNotFoundError,
    InvitationExpiredError,
    InvitationAlreadyUsedError,
    InvitationAlreadyPendingError,
)


router = APIRouter(prefix="/tenants", tags=["tenants"])
security = HTTPBearer()


# Helper to get current user ID from token
# In real implementation, this would decode JWT
async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UUID:
    """Extract user ID from JWT token.

    This is a placeholder - real implementation would decode the JWT.
    """
    # TODO: Implement JWT decoding
    # For now, return a placeholder
    # token = credentials.credentials
    # decoded = decode_jwt(token)
    # return UUID(decoded["sub"])
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated"
    )


def _tenant_to_response(tenant) -> TenantResponse:
    """Convert tenant entity to response model."""
    return TenantResponse(
        tenant_id=str(tenant.tenant_id),
        name=tenant.name,
        slug=tenant.slug,
        owner_user_id=str(tenant.owner_user_id),
        plan=tenant.plan.value,
        status=tenant.status.value,
        settings=tenant.settings,
        billing_email=tenant.billing_email,
        limits=TenantPlanLimits(
            max_projects=tenant.get_limit("max_projects"),
            max_members=tenant.get_limit("max_members"),
            max_decisions_per_month=tenant.get_limit("max_decisions_per_month"),
        ),
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


def _membership_to_response(membership) -> MembershipResponse:
    """Convert membership entity to response model."""
    return MembershipResponse(
        membership_id=str(membership.membership_id),
        user_id=str(membership.user_id),
        tenant_id=str(membership.tenant_id),
        role=membership.role.value,
        status=membership.status.value,
        invited_by_user_id=str(membership.invited_by_user_id) if membership.invited_by_user_id else None,
        invited_at=membership.invited_at,
        joined_at=membership.joined_at,
        created_at=membership.created_at,
    )


def _invitation_to_response(invitation) -> InvitationResponse:
    """Convert invitation entity to response model."""
    return InvitationResponse(
        invitation_id=str(invitation.invitation_id),
        email=invitation.email,
        tenant_id=str(invitation.tenant_id),
        role=invitation.role.value,
        status=invitation.status.value,
        invited_by_user_id=str(invitation.invited_by_user_id),
        message=invitation.message,
        expires_at=invitation.expires_at,
        is_expired=invitation.is_expired(),
        created_at=invitation.created_at,
    )


# ============================================
# Tenant CRUD
# ============================================

@router.post("", response_model=TenantCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: CreateTenantRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new tenant.

    Creates the tenant and adds creator as owner.
    """
    try:
        use_case = get_create_tenant_use_case()
        result = await use_case.execute(CreateTenantInput(
            name=request.name,
            owner_user_id=user_id,
            slug=request.slug,
            billing_email=request.billing_email,
        ))

        return TenantCreateResponse(
            data={
                "tenant": _tenant_to_response(result.tenant).model_dump(),
                "membership": _membership_to_response(result.owner_membership).model_dump(),
            },
            message="Tenant created successfully",
        )
    except TenantSlugExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "SLUG_EXISTS", "message": str(e)}
        )


@router.get("", response_model=ListTenantsResponse)
async def list_tenants(
    include_inactive: bool = Query(False, description="Include suspended tenants"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List tenants for current user."""
    use_case = get_list_tenants_use_case()
    result = await use_case.execute(ListTenantsInput(
        user_id=user_id,
        include_inactive=include_inactive,
    ))

    tenants = [
        TenantWithMembershipResponse(
            tenant=_tenant_to_response(t.tenant),
            role=t.membership.role.value,
            member_count=t.member_count,
        )
        for t in result.tenants
    ]

    return ListTenantsResponse(
        data=tenants,
        meta={"total": result.total},
    )


@router.get("/{tenant_id}", response_model=TenantDetailResponse)
async def get_tenant(
    tenant_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get tenant details."""
    try:
        use_case = get_get_tenant_use_case()
        result = await use_case.execute(GetTenantInput(
            tenant_id=tenant_id,
            actor_user_id=user_id,
        ))

        return TenantDetailResponse(
            data=TenantWithMembershipResponse(
                tenant=_tenant_to_response(result.tenant),
                role=result.membership.role.value if result.membership else "none",
                member_count=result.member_count,
            ),
        )
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TENANT_NOT_FOUND", "message": "Tenant not found"}
        )
    except NotMemberError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_MEMBER", "message": "You are not a member of this tenant"}
        )


@router.patch("/{tenant_id}", response_model=TenantUpdateResponse)
async def update_tenant(
    tenant_id: UUID,
    request: UpdateTenantRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update tenant details."""
    try:
        use_case = get_update_tenant_use_case()
        result = await use_case.execute(UpdateTenantInput(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            name=request.name,
            billing_email=request.billing_email,
            settings=request.settings,
        ))

        return TenantUpdateResponse(
            data=_tenant_to_response(result.tenant),
        )
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TENANT_NOT_FOUND", "message": "Tenant not found"}
        )
    except InsufficientPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INSUFFICIENT_PERMISSION", "message": str(e)}
        )


@router.delete("/{tenant_id}", response_model=TenantDeleteResponse)
async def delete_tenant(
    tenant_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete tenant (soft delete)."""
    try:
        use_case = get_delete_tenant_use_case()
        await use_case.execute(DeleteTenantInput(
            tenant_id=tenant_id,
            actor_user_id=user_id,
        ))

        return TenantDeleteResponse()
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TENANT_NOT_FOUND", "message": "Tenant not found"}
        )
    except InsufficientPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "OWNER_REQUIRED", "message": "Only owner can delete tenant"}
        )


# ============================================
# Members
# ============================================

@router.get("/{tenant_id}/members", response_model=ListMembersResponse)
async def list_members(
    tenant_id: UUID,
    include_invitations: bool = Query(True, description="Include pending invitations"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List tenant members."""
    try:
        use_case = get_list_members_use_case()
        result = await use_case.execute(ListMembersInput(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            include_invitations=include_invitations,
        ))

        members = [
            MemberResponse(
                membership=_membership_to_response(m.membership),
                user_email=m.user_email,
                user_name=m.user_name,
            ).model_dump()
            for m in result.members
        ]

        pending = [
            _invitation_to_response(i).model_dump()
            for i in result.pending_invitations
        ]

        return ListMembersResponse(
            data={
                "members": members,
                "pending_invitations": pending,
            },
            meta={
                "total_members": result.total_members,
                "total_pending": result.total_pending,
            },
        )
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TENANT_NOT_FOUND", "message": "Tenant not found"}
        )
    except NotMemberError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_MEMBER", "message": "You are not a member of this tenant"}
        )


@router.patch("/{tenant_id}/members/{member_user_id}/role", response_model=MemberRoleUpdateResponse)
async def update_member_role(
    tenant_id: UUID,
    member_user_id: UUID,
    request: UpdateMemberRoleRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update member role."""
    try:
        # Validate role
        try:
            new_role = MemberRole(request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_ROLE", "message": f"Invalid role: {request.role}"}
            )

        use_case = get_update_member_role_use_case()
        result = await use_case.execute(UpdateMemberRoleInput(
            tenant_id=tenant_id,
            target_user_id=member_user_id,
            actor_user_id=user_id,
            new_role=new_role,
        ))

        return MemberRoleUpdateResponse(
            data={
                "old_role": result.old_role.value,
                "new_role": result.new_role.value,
            },
        )
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TENANT_NOT_FOUND", "message": "Tenant not found"}
        )
    except NotMemberError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MEMBER_NOT_FOUND", "message": "Member not found"}
        )
    except InsufficientPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INSUFFICIENT_PERMISSION", "message": str(e)}
        )
    except CannotDemoteOwnerError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANNOT_DEMOTE_OWNER", "message": "Cannot demote the only owner"}
        )


@router.delete("/{tenant_id}/members/{member_user_id}", response_model=MemberRemoveResponse)
async def remove_member(
    tenant_id: UUID,
    member_user_id: UUID,
    reason: Optional[str] = Query(None, max_length=500),
    user_id: UUID = Depends(get_current_user_id),
):
    """Remove member from tenant."""
    try:
        use_case = get_remove_member_use_case()
        await use_case.execute(RemoveMemberInput(
            tenant_id=tenant_id,
            target_user_id=member_user_id,
            actor_user_id=user_id,
            reason=reason,
        ))

        return MemberRemoveResponse()
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TENANT_NOT_FOUND", "message": "Tenant not found"}
        )
    except NotMemberError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MEMBER_NOT_FOUND", "message": "Member not found"}
        )
    except InsufficientPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INSUFFICIENT_PERMISSION", "message": str(e)}
        )
    except CannotRemoveOwnerError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANNOT_REMOVE_OWNER", "message": "Cannot remove the only owner"}
        )


# ============================================
# Invitations
# ============================================

@router.post("/{tenant_id}/invitations", response_model=InvitationCreateResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    tenant_id: UUID,
    request: InviteMemberRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Invite a user to join the tenant."""
    try:
        # Validate role
        try:
            role = MemberRole(request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_ROLE", "message": f"Invalid role: {request.role}"}
            )

        use_case = get_invite_member_use_case()
        result = await use_case.execute(InviteMemberInput(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            email=request.email,
            role=role,
            message=request.message,
        ))

        return InvitationCreateResponse(
            data=_invitation_to_response(result.invitation),
        )
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TENANT_NOT_FOUND", "message": "Tenant not found"}
        )
    except InsufficientPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INSUFFICIENT_PERMISSION", "message": str(e)}
        )
    except AlreadyMemberError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_MEMBER", "message": "User is already a member"}
        )
    except InvitationAlreadyPendingError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "INVITATION_PENDING", "message": "Invitation already pending for this email"}
        )
    except MaxMembersExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PLAN_LIMIT", "message": str(e)}
        )


@router.get("/{tenant_id}/invitations", response_model=ListInvitationsResponse)
async def list_invitations(
    tenant_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
):
    """List tenant invitations (admin only)."""
    # First check if user is admin
    from .dependencies import get_membership_repo
    membership_repo = get_membership_repo()
    membership = await membership_repo.get_by_user_and_tenant(user_id, tenant_id)

    if not membership or not membership.is_admin_or_higher():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_REQUIRED", "message": "Admin access required"}
        )

    invitation_repo = get_invitation_repo()
    invitations = await invitation_repo.list_by_tenant(
        tenant_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return ListInvitationsResponse(
        data=[_invitation_to_response(i) for i in invitations],
        meta={"limit": limit, "offset": offset},
    )


@router.post("/invitations/accept", response_model=InvitationAcceptResponse)
async def accept_invitation(
    request: AcceptInvitationRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Accept a tenant invitation."""
    try:
        use_case = get_accept_invitation_use_case()
        result = await use_case.execute(AcceptInvitationInput(
            token=request.token,
            user_id=user_id,
        ))

        return InvitationAcceptResponse(
            data={
                "membership": _membership_to_response(result.membership).model_dump(),
                "tenant_id": str(result.tenant_id),
            },
        )
    except InvitationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "INVITATION_NOT_FOUND", "message": "Invalid invitation token"}
        )
    except InvitationExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"code": "INVITATION_EXPIRED", "message": "Invitation has expired"}
        )
    except InvitationAlreadyUsedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "INVITATION_USED", "message": "Invitation has already been used"}
        )
    except AlreadyMemberError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_MEMBER", "message": "You are already a member of this tenant"}
        )


@router.delete("/{tenant_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    tenant_id: UUID,
    invitation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Cancel a pending invitation (admin only)."""
    # Check if user is admin
    from .dependencies import get_membership_repo
    membership_repo = get_membership_repo()
    membership = await membership_repo.get_by_user_and_tenant(user_id, tenant_id)

    if not membership or not membership.is_admin_or_higher():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_REQUIRED", "message": "Admin access required"}
        )

    # Get and cancel invitation
    invitation_repo = get_invitation_repo()
    invitation = await invitation_repo.get_by_id(invitation_id)

    if not invitation or invitation.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "INVITATION_NOT_FOUND", "message": "Invitation not found"}
        )

    if not invitation.is_pending():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANNOT_CANCEL", "message": "Can only cancel pending invitations"}
        )

    invitation.cancel()
    await invitation_repo.update(invitation)

    return None


# ============================================
# Leave Tenant
# ============================================

@router.post("/{tenant_id}/leave", response_model=MemberRemoveResponse)
async def leave_tenant(
    tenant_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Leave a tenant."""
    try:
        use_case = get_remove_member_use_case()
        await use_case.execute(RemoveMemberInput(
            tenant_id=tenant_id,
            target_user_id=user_id,  # Self-leave
            actor_user_id=user_id,
            reason="User left voluntarily",
        ))

        return MemberRemoveResponse(message="Left tenant successfully")
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TENANT_NOT_FOUND", "message": "Tenant not found"}
        )
    except NotMemberError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_MEMBER", "message": "You are not a member of this tenant"}
        )
    except CannotRemoveOwnerError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "OWNER_CANNOT_LEAVE", "message": "Owner cannot leave. Transfer ownership first."}
        )
