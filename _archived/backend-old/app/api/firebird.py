"""
Firebird Database Integration API Endpoints
Manages Firebird database configurations and executes read-only queries

Security Features:
- JWT authentication required for all endpoints
- Read-only queries only (SELECT statements)
- Encrypted credential storage
- SQL injection prevention through query validation
- Connection pooling with resource limits
"""

from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.middleware.request_id import get_request_id
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException, InternalServerException
from app.schemas.common import success_response
from app.models.user import User
from app.models.firebird import FirebirdConfig
from app.schemas.firebird import (
    FirebirdConfigCreate,
    FirebirdConfigUpdate,
    FirebirdConfigResponse,
    FirebirdConfigListResponse,
    FirebirdTestRequest,
    FirebirdTestResult,
    FirebirdQueryRequest,
    FirebirdQueryResult,
    FirebirdHealthResult
)
from app.services.firebird_service import firebird_service

logger = StructuredLogger(__name__)
router = APIRouter()


# =============================================================================
# CONFIGURATION MANAGEMENT ENDPOINTS
# =============================================================================

@router.post(
    "/api/firebird/configs",
    status_code=status.HTTP_201_CREATED,
    summary="Create Firebird configuration",
    description="Create a new Firebird database configuration with encrypted credentials"
)
async def create_firebird_config(
    request: Request,
    config_data: FirebirdConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new Firebird database configuration

    The API key (username:password) will be encrypted before storage.
    Connection pool will be created on first use.

    Args:
        request: FastAPI Request object
        config_data: Configuration details
        db: Database session
        current_user: Authenticated user

    Returns:
        Created configuration (without decrypted API key)

    Raises:
        BadRequestException: If config_key already exists
        InternalServerException: If encryption or database operation fails
    """
    request_id = get_request_id(request)

    logger.info(
        "Creating Firebird configuration",
        request_id=request_id,
        config_key=config_data.config_key,
        user_id=current_user.id,
        username=current_user.username
    )

    try:
        # Check if config_key already exists
        existing = db.query(FirebirdConfig).filter(
            FirebirdConfig.config_key == config_data.config_key
        ).first()

        if existing:
            raise BadRequestException(
                message=f"Configuration with key '{config_data.config_key}' already exists",
                details={"config_key": config_data.config_key}
            )

        # Encrypt API key before storing
        encrypted_api_key = firebird_service.encrypt_api_key(config_data.api_key)

        # Create new configuration
        new_config = FirebirdConfig(
            config_key=config_data.config_key,
            api_endpoint=config_data.api_endpoint,
            api_key=encrypted_api_key,  # Store encrypted
            refresh_interval=config_data.refresh_interval,
            is_active=config_data.is_active,
            notes=config_data.notes
        )

        db.add(new_config)
        db.commit()
        db.refresh(new_config)

        logger.info(
            "Firebird configuration created successfully",
            request_id=request_id,
            config_id=new_config.id,
            config_key=new_config.config_key,
            user_id=current_user.id
        )

        # Convert to response model
        config_response = FirebirdConfigResponse.model_validate(new_config)

        return success_response(
            data=config_response.model_dump(),
            request_id=request_id
        )

    except BadRequestException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create Firebird configuration",
            request_id=request_id,
            config_key=config_data.config_key,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message=f"Failed to create configuration: {str(e)}",
            details={"config_key": config_data.config_key}
        )


@router.get(
    "/api/firebird/configs",
    summary="List Firebird configurations",
    description="Get list of all Firebird database configurations"
)
async def list_firebird_configs(
    request: Request,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all Firebird database configurations

    Args:
        request: FastAPI Request object
        is_active: Optional filter by active status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Authenticated user

    Returns:
        List of configurations (without decrypted API keys)
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing Firebird configurations",
        request_id=request_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
        user_id=current_user.id
    )

    try:
        query = db.query(FirebirdConfig)

        # Apply filters
        if is_active is not None:
            query = query.filter(FirebirdConfig.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply pagination
        configs = query.order_by(FirebirdConfig.id).offset(skip).limit(limit).all()

        # Convert to response models
        config_list = [FirebirdConfigResponse.model_validate(config) for config in configs]

        logger.info(
            "Firebird configurations retrieved successfully",
            request_id=request_id,
            total=total,
            returned=len(configs)
        )

        return success_response(
            data={
                "total": total,
                "configs": [config.model_dump() for config in config_list]
            },
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Failed to list Firebird configurations",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message=f"Failed to retrieve configurations: {str(e)}"
        )


@router.get(
    "/api/firebird/configs/{config_id}",
    summary="Get Firebird configuration",
    description="Get details of a specific Firebird database configuration"
)
async def get_firebird_config(
    request: Request,
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific Firebird database configuration

    Args:
        request: FastAPI Request object
        config_id: Configuration ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Configuration details (without decrypted API key)

    Raises:
        NotFoundException: If configuration not found
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting Firebird configuration",
        request_id=request_id,
        config_id=config_id,
        user_id=current_user.id
    )

    config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

    if not config:
        raise NotFoundException(
            message=f"Configuration with ID {config_id} not found",
            resource_type="FirebirdConfig",
            resource_id=config_id
        )

    # Convert to response model
    config_response = FirebirdConfigResponse.model_validate(config)

    logger.info(
        "Firebird configuration retrieved successfully",
        request_id=request_id,
        config_id=config_id,
        config_key=config.config_key
    )

    return success_response(
        data=config_response.model_dump(),
        request_id=request_id
    )


@router.put(
    "/api/firebird/configs/{config_id}",
    summary="Update Firebird configuration",
    description="Update an existing Firebird database configuration"
)
async def update_firebird_config(
    request: Request,
    config_id: int,
    config_data: FirebirdConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a Firebird database configuration

    If API key is updated, it will be re-encrypted.
    Connection pool will be recreated on next use if endpoint or credentials change.

    Args:
        request: FastAPI Request object
        config_id: Configuration ID
        config_data: Updated configuration data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated configuration

    Raises:
        NotFoundException: If configuration not found
        BadRequestException: If config_key conflict
        InternalServerException: If update fails
    """
    request_id = get_request_id(request)

    logger.info(
        "Updating Firebird configuration",
        request_id=request_id,
        config_id=config_id,
        user_id=current_user.id
    )

    try:
        # Get existing config
        config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

        if not config:
            raise NotFoundException(
                message=f"Configuration with ID {config_id} not found",
                resource_type="FirebirdConfig",
                resource_id=config_id
            )

        # Check config_key uniqueness if being updated
        if config_data.config_key and config_data.config_key != config.config_key:
            existing = db.query(FirebirdConfig).filter(
                FirebirdConfig.config_key == config_data.config_key,
                FirebirdConfig.id != config_id
            ).first()

            if existing:
                raise BadRequestException(
                    message=f"Configuration with key '{config_data.config_key}' already exists",
                    details={"config_key": config_data.config_key}
                )

        # Track if connection pool needs to be recreated
        pool_needs_reset = False

        # Update fields
        if config_data.config_key is not None:
            config.config_key = config_data.config_key

        if config_data.api_endpoint is not None:
            config.api_endpoint = config_data.api_endpoint
            pool_needs_reset = True

        if config_data.api_key is not None:
            # Re-encrypt new API key
            config.api_key = firebird_service.encrypt_api_key(config_data.api_key)
            pool_needs_reset = True

        if config_data.refresh_interval is not None:
            config.refresh_interval = config_data.refresh_interval

        if config_data.is_active is not None:
            config.is_active = config_data.is_active

        if config_data.notes is not None:
            config.notes = config_data.notes

        # Remove old connection pool if credentials or endpoint changed
        if pool_needs_reset:
            firebird_service.remove_pool(config_id)
            logger.info(
                "Connection pool reset",
                request_id=request_id,
                config_id=config_id
            )

        db.commit()
        db.refresh(config)

        logger.info(
            "Firebird configuration updated successfully",
            request_id=request_id,
            config_id=config_id,
            config_key=config.config_key,
            pool_reset=pool_needs_reset
        )

        # Convert to response model
        config_response = FirebirdConfigResponse.model_validate(config)

        return success_response(
            data=config_response.model_dump(),
            request_id=request_id
        )

    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to update Firebird configuration",
            request_id=request_id,
            config_id=config_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message=f"Failed to update configuration: {str(e)}",
            details={"config_id": config_id}
        )


@router.delete(
    "/api/firebird/configs/{config_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Firebird configuration",
    description="Delete a Firebird database configuration and close its connection pool"
)
async def delete_firebird_config(
    request: Request,
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a Firebird database configuration

    This will also close and remove the associated connection pool.

    Args:
        request: FastAPI Request object
        config_id: Configuration ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Success message

    Raises:
        NotFoundException: If configuration not found
        InternalServerException: If deletion fails
    """
    request_id = get_request_id(request)

    logger.info(
        "Deleting Firebird configuration",
        request_id=request_id,
        config_id=config_id,
        user_id=current_user.id
    )

    try:
        config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

        if not config:
            raise NotFoundException(
                message=f"Configuration with ID {config_id} not found",
                resource_type="FirebirdConfig",
                resource_id=config_id
            )

        config_key = config.config_key

        # Remove connection pool
        firebird_service.remove_pool(config_id)

        # Delete from database
        db.delete(config)
        db.commit()

        logger.info(
            "Firebird configuration deleted successfully",
            request_id=request_id,
            config_id=config_id,
            config_key=config_key,
            user_id=current_user.id
        )

        return success_response(
            data={
                "message": f"Configuration '{config_key}' deleted successfully",
                "config_id": config_id
            },
            request_id=request_id
        )

    except NotFoundException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to delete Firebird configuration",
            request_id=request_id,
            config_id=config_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message=f"Failed to delete configuration: {str(e)}",
            details={"config_id": config_id}
        )


# =============================================================================
# CONNECTION & QUERY ENDPOINTS
# =============================================================================

@router.post(
    "/api/firebird/configs/{config_id}/test",
    summary="Test Firebird connection",
    description="Test connection to Firebird database and optionally execute a test query"
)
async def test_firebird_connection(
    request: Request,
    config_id: int,
    test_request: Optional[FirebirdTestRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Test Firebird database connection

    This will create a connection pool if it doesn't exist and test the connection.
    Optionally executes a custom test query.

    Args:
        request: FastAPI Request object
        config_id: Configuration ID
        test_request: Optional test query to execute
        db: Database session
        current_user: Authenticated user

    Returns:
        Test result with connection time and status

    Raises:
        NotFoundException: If configuration not found
    """
    request_id = get_request_id(request)

    logger.info(
        "Testing Firebird connection",
        request_id=request_id,
        config_id=config_id,
        user_id=current_user.id
    )

    # Get configuration
    config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

    if not config:
        raise NotFoundException(
            message=f"Configuration with ID {config_id} not found",
            resource_type="FirebirdConfig",
            resource_id=config_id
        )

    # Get test query if provided
    test_query = None
    if test_request and test_request.test_query:
        test_query = test_request.test_query
    else:
        # Default test query
        test_query = "SELECT 1 FROM RDB$DATABASE"

    # Test connection
    result = await firebird_service.test_connection(config, test_query)

    # Update last_sync if successful
    if result["success"]:
        config.last_sync = datetime.utcnow()
        db.commit()

    logger.info(
        "Firebird connection test completed",
        request_id=request_id,
        config_id=config_id,
        success=result["success"],
        connection_time=result.get("connection_time")
    )

    # Convert to response model
    test_result = FirebirdTestResult(**result)

    return success_response(
        data=test_result.model_dump(),
        request_id=request_id
    )


@router.post(
    "/api/firebird/configs/{config_id}/query",
    summary="Execute Firebird query",
    description="Execute a read-only SELECT query against the Firebird database"
)
async def execute_firebird_query(
    request: Request,
    config_id: int,
    query_request: FirebirdQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute a read-only SELECT query

    Only SELECT queries are allowed. INSERT, UPDATE, DELETE, and DDL operations are blocked.
    Query results are limited by max_rows parameter (1-1000).

    Args:
        request: FastAPI Request object
        config_id: Configuration ID
        query_request: Query details (SQL and max_rows)
        db: Database session
        current_user: Authenticated user

    Returns:
        Query results with columns and rows

    Raises:
        NotFoundException: If configuration not found
        BadRequestException: If configuration is inactive
    """
    request_id = get_request_id(request)

    logger.info(
        "Executing Firebird query",
        request_id=request_id,
        config_id=config_id,
        max_rows=query_request.max_rows,
        user_id=current_user.id
    )

    # Get configuration
    config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

    if not config:
        raise NotFoundException(
            message=f"Configuration with ID {config_id} not found",
            resource_type="FirebirdConfig",
            resource_id=config_id
        )

    # Check if configuration is active
    if not config.is_active:
        raise BadRequestException(
            message=f"Configuration '{config.config_key}' is not active",
            details={"config_key": config.config_key, "is_active": False}
        )

    # Execute query
    result = await firebird_service.execute_query(
        config,
        query_request.query,
        query_request.max_rows
    )

    # Update last_sync if successful
    if result["success"]:
        config.last_sync = datetime.utcnow()
        db.commit()

    logger.info(
        "Firebird query executed",
        request_id=request_id,
        config_id=config_id,
        success=result["success"],
        row_count=result.get("row_count"),
        execution_time=result.get("execution_time")
    )

    # Convert to response model
    query_result = FirebirdQueryResult(**result)

    return success_response(
        data=query_result.model_dump(),
        request_id=request_id
    )


@router.get(
    "/api/firebird/configs/{config_id}/health",
    summary="Check Firebird connection health",
    description="Check connection health and pool status for a Firebird configuration"
)
async def check_firebird_health(
    request: Request,
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Check connection health and pool status

    Returns current connection pool status and tests if database is accessible.

    Args:
        request: FastAPI Request object
        config_id: Configuration ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Health status with connection and pool information

    Raises:
        NotFoundException: If configuration not found
    """
    request_id = get_request_id(request)

    logger.info(
        "Checking Firebird connection health",
        request_id=request_id,
        config_id=config_id,
        user_id=current_user.id
    )

    # Get configuration
    config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

    if not config:
        raise NotFoundException(
            message=f"Configuration with ID {config_id} not found",
            resource_type="FirebirdConfig",
            resource_id=config_id
        )

    # Check health
    result = await firebird_service.health_check(config)

    logger.info(
        "Firebird health check completed",
        request_id=request_id,
        config_id=config_id,
        is_healthy=result.get("is_healthy"),
        pool_size=result.get("pool_size")
    )

    # Convert to response model
    health_result = FirebirdHealthResult(**result)

    return success_response(
        data=health_result.model_dump(),
        request_id=request_id
    )
