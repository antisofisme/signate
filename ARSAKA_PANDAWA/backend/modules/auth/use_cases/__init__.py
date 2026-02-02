"""
ARSAKA_PANDAWA Backend - Auth Module Use Cases
Business logic layer (follows Clean Architecture)

Use Cases:
- LoginUseCase (Phase 1)
- RegisterUseCase (Phase 1)
- RefreshTokenUseCase (Phase 1)
- UpdateProfileUseCase (Phase 1)
- ChangePasswordUseCase (Phase 1)

Use Case Pattern Benefits:
- Encapsulates business logic
- Orchestrates repositories
- Handles validations & business rules
- Independent of delivery mechanism (HTTP, CLI, etc.)
"""

# Use case classes will be implemented here per phase
# Phase 1: Authentication & User Management
# - LoginUseCase: Validate credentials, generate JWT tokens
# - RegisterUseCase: Create user, hash password, create tenant (optional)
# - RefreshTokenUseCase: Validate refresh token, generate new access token
# - UpdateProfileUseCase: Update user profile with validation
# - ChangePasswordUseCase: Verify current password, update to new password
