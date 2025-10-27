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

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.deps import get_current_active_user
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

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# CONFIGURATION MANAGEMENT ENDPOINTS
# =============================================================================

@router.post(
    "/api/firebird/configs",
    response_model=FirebirdConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Firebird configuration",
    description="Create a new Firebird database configuration with encrypted credentials"
)
async def create_firebird_config(
    config_data: FirebirdConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new Firebird database configuration

    The API key (username:password) will be encrypted before storage.
    Connection pool will be created on first use.

    Args:
        config_data: Configuration details
        db: Database session
        current_user: Authenticated user

    Returns:
        Created configuration (without decrypted API key)

    Raises:
        HTTPException 400: If config_key already exists
        HTTPException 500: If encryption or database operation fails
    """
    try:
        # Check if config_key already exists
        existing = db.query(FirebirdConfig).filter(
            FirebirdConfig.config_key == config_data.config_key
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Configuration with key '{config_data.config_key}' already exists"
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
            f"Created Firebird config: id={new_config.id}, "
            f"key={new_config.config_key} by user={current_user.username}"
        )

        return new_config

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create Firebird config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}"
        )


@router.get(
    "/api/firebird/configs",
    response_model=FirebirdConfigListResponse,
    summary="List Firebird configurations",
    description="Get list of all Firebird database configurations"
)
async def list_firebird_configs(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all Firebird database configurations

    Args:
        is_active: Optional filter by active status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Authenticated user

    Returns:
        List of configurations (without decrypted API keys)
    """
    try:
        query = db.query(FirebirdConfig)

        # Apply filters
        if is_active is not None:
            query = query.filter(FirebirdConfig.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply pagination
        configs = query.order_by(FirebirdConfig.id).offset(skip).limit(limit).all()

        return FirebirdConfigListResponse(
            total=total,
            configs=configs
        )

    except Exception as e:
        logger.error(f"Failed to list Firebird configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configurations: {str(e)}"
        )


@router.get(
    "/api/firebird/configs/{config_id}",
    response_model=FirebirdConfigResponse,
    summary="Get Firebird configuration",
    description="Get details of a specific Firebird database configuration"
)
async def get_firebird_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific Firebird database configuration

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Configuration details (without decrypted API key)

    Raises:
        HTTPException 404: If configuration not found
    """
    config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration with ID {config_id} not found"
        )

    return config


@router.put(
    "/api/firebird/configs/{config_id}",
    response_model=FirebirdConfigResponse,
    summary="Update Firebird configuration",
    description="Update an existing Firebird database configuration"
)
async def update_firebird_config(
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
        config_id: Configuration ID
        config_data: Updated configuration data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated configuration

    Raises:
        HTTPException 404: If configuration not found
        HTTPException 400: If config_key conflict
        HTTPException 500: If update fails
    """
    try:
        # Get existing config
        config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration with ID {config_id} not found"
            )

        # Check config_key uniqueness if being updated
        if config_data.config_key and config_data.config_key != config.config_key:
            existing = db.query(FirebirdConfig).filter(
                FirebirdConfig.config_key == config_data.config_key,
                FirebirdConfig.id != config_id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Configuration with key '{config_data.config_key}' already exists"
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
            logger.info(f"Connection pool reset for config_id={config_id}")

        db.commit()
        db.refresh(config)

        logger.info(
            f"Updated Firebird config: id={config_id}, "
            f"key={config.config_key} by user={current_user.username}"
        )

        return config

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update Firebird config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.delete(
    "/api/firebird/configs/{config_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Firebird configuration",
    description="Delete a Firebird database configuration and close its connection pool"
)
async def delete_firebird_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a Firebird database configuration

    This will also close and remove the associated connection pool.

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Success message

    Raises:
        HTTPException 404: If configuration not found
        HTTPException 500: If deletion fails
    """
    try:
        config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration with ID {config_id} not found"
            )

        config_key = config.config_key

        # Remove connection pool
        firebird_service.remove_pool(config_id)

        # Delete from database
        db.delete(config)
        db.commit()

        logger.info(
            f"Deleted Firebird config: id={config_id}, "
            f"key={config_key} by user={current_user.username}"
        )

        return {
            "message": f"Configuration '{config_key}' deleted successfully",
            "config_id": config_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete Firebird config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}"
        )


# =============================================================================
# CONNECTION & QUERY ENDPOINTS
# =============================================================================

@router.post(
    "/api/firebird/configs/{config_id}/test",
    response_model=FirebirdTestResult,
    summary="Test Firebird connection",
    description="Test connection to Firebird database and optionally execute a test query"
)
async def test_firebird_connection(
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
        config_id: Configuration ID
        test_request: Optional test query to execute
        db: Database session
        current_user: Authenticated user

    Returns:
        Test result with connection time and status

    Raises:
        HTTPException 404: If configuration not found
    """
    # Get configuration
    config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration with ID {config_id} not found"
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
        f"Connection test for config_id={config_id}: "
        f"success={result['success']} by user={current_user.username}"
    )

    return FirebirdTestResult(**result)


@router.post(
    "/api/firebird/configs/{config_id}/query",
    response_model=FirebirdQueryResult,
    summary="Execute Firebird query",
    description="Execute a read-only SELECT query against the Firebird database"
)
async def execute_firebird_query(
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
        config_id: Configuration ID
        query_request: Query details (SQL and max_rows)
        db: Database session
        current_user: Authenticated user

    Returns:
        Query results with columns and rows

    Raises:
        HTTPException 404: If configuration not found
        HTTPException 400: If configuration is inactive
    """
    # Get configuration
    config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration with ID {config_id} not found"
        )

    # Check if configuration is active
    if not config.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration '{config.config_key}' is not active"
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
        f"Query execution for config_id={config_id}: "
        f"success={result['success']}, rows={result['row_count']} "
        f"by user={current_user.username}"
    )

    return FirebirdQueryResult(**result)


@router.get(
    "/api/firebird/configs/{config_id}/health",
    response_model=FirebirdHealthResult,
    summary="Check Firebird connection health",
    description="Check connection health and pool status for a Firebird configuration"
)
async def check_firebird_health(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Check connection health and pool status

    Returns current connection pool status and tests if database is accessible.

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Health status with connection and pool information

    Raises:
        HTTPException 404: If configuration not found
    """
    # Get configuration
    config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration with ID {config_id} not found"
        )

    # Check health
    result = await firebird_service.health_check(config)

    logger.info(
        f"Health check for config_id={config_id}: "
        f"healthy={result['is_healthy']} by user={current_user.username}"
    )

    return FirebirdHealthResult(**result)
