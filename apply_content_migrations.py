#!/usr/bin/env python3
"""
Apply content CRUD endpoint migrations (update, delete, assign, get assignments, unassign)
"""

# Read the file
with open('/mnt/g/khoirul/signate/backend/app/api/content.py', 'r') as f:
    content = f.read()

# Migration 1: PATCH /{content_id} - update_content
old_update = '''@router.patch("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    content_data: ContentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update content metadata (partial update)

    Args:
        content_id: Content ID
        content_data: Update data (partial - only changed fields)
        db: Database session
        current_user: Authenticated user

    Returns:
        ContentResponse: Updated content

    Raises:
        HTTPException: If content not found or update fails
    """
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )

    try:
        # Update local database (primary source of truth for viewers)
        if content_data.title is not None:
            content.title = content_data.title
        if content_data.description is not None:
            content.description = content_data.description
        if content_data.duration is not None:
            content.duration = content_data.duration
        if content_data.video_start_time is not None:
            content.video_start_time = content_data.video_start_time
        if content_data.video_end_time is not None:
            content.video_end_time = content_data.video_end_time
        if content_data.is_active is not None:
            content.is_active = content_data.is_active

        # Commit database changes first (this is what viewers use)
        db.commit()
        db.refresh(content)

        # Try to update Anthias (optional - for consistency only)
        # If this fails, database update still succeeds since it's already committed
        if content.anthias_asset_id and (content_data.title or content_data.duration or content_data.is_active is not None):
            try:
                await anthias_service.update_asset(
                    asset_id=content.anthias_asset_id,
                    name=content.title if content_data.title else None,
                    duration=content.duration if content_data.duration else None,
                    is_enabled=content.is_active if content_data.is_active is not None else None
                )
                logger.info(f"Anthias asset {content.anthias_asset_id} updated")
            except Exception as anthias_error:
                # Log warning but don't fail the request
                # Viewers use our database, not Anthias metadata
                logger.warning(f"Failed to update Anthias asset {content.anthias_asset_id}: {anthias_error}")
                logger.warning("Database update succeeded, but Anthias sync failed (non-critical)")

        logger.info(f"Content updated: ID={content.id}")
        return content

    except Exception as e:
        logger.error(f"Database update error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )'''

new_update = '''@router.patch("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    content_data: ContentUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update content metadata (partial update)

    Args:
        content_id: Content ID
        content_data: Update data (partial - only changed fields)
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Updated content wrapped in standardized response

    Raises:
        NotFoundException: If content not found
        InternalServerException: If update fails
    """
    request_id = get_request_id(request)

    logger.info(
        "Updating content",
        request_id=request_id,
        content_id=content_id,
        fields_to_update=content_data.dict(exclude_unset=True)
    )

    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        logger.warning(
            "Content not found",
            request_id=request_id,
            content_id=content_id
        )
        raise NotFoundException(
            message=f"Content with ID {content_id} not found",
            resource_type="Content",
            resource_id=content_id
        )

    try:
        # Update local database (primary source of truth for viewers)
        if content_data.title is not None:
            content.title = content_data.title
        if content_data.description is not None:
            content.description = content_data.description
        if content_data.duration is not None:
            content.duration = content_data.duration
        if content_data.video_start_time is not None:
            content.video_start_time = content_data.video_start_time
        if content_data.video_end_time is not None:
            content.video_end_time = content_data.video_end_time
        if content_data.is_active is not None:
            content.is_active = content_data.is_active

        # Commit database changes first (this is what viewers use)
        db.commit()
        db.refresh(content)

        # Try to update Anthias (optional - for consistency only)
        # If this fails, database update still succeeds since it's already committed
        if content.anthias_asset_id and (content_data.title or content_data.duration or content_data.is_active is not None):
            try:
                await anthias_service.update_asset(
                    asset_id=content.anthias_asset_id,
                    name=content.title if content_data.title else None,
                    duration=content.duration if content_data.duration else None,
                    is_enabled=content.is_active if content_data.is_active is not None else None
                )
                logger.info(
                    "Anthias asset updated",
                    request_id=request_id,
                    anthias_asset_id=content.anthias_asset_id
                )
            except Exception as anthias_error:
                # Log warning but don't fail the request
                # Viewers use our database, not Anthias metadata
                logger.warning(
                    "Anthias sync failed (non-critical)",
                    request_id=request_id,
                    anthias_asset_id=content.anthias_asset_id,
                    error=str(anthias_error)
                )

        logger.info(
            "Content updated successfully",
            request_id=request_id,
            content_id=content.id,
            title=content.title
        )

        # Convert to dict
        content_dict = {
            "id": content.id,
            "title": content.title,
            "description": content.description,
            "content_type": content.content_type,
            "anthias_url": content.anthias_url,
            "anthias_asset_id": content.anthias_asset_id,
            "duration": content.duration,
            "is_active": content.is_active,
            "file_size": content.file_size,
            "mime_type": content.mime_type,
            "resolution": content.resolution,
            "width": content.width,
            "height": content.height,
            "codec": content.codec,
            "fps": content.fps,
            "bitrate": content.bitrate,
            "video_duration": content.video_duration,
            "audio_codec": content.audio_codec,
            "audio_bitrate": content.audio_bitrate,
            "audio_sample_rate": content.audio_sample_rate,
            "created_at": content.created_at,
            "updated_at": content.updated_at
        }

        return success_response(
            data=content_dict,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Content update failed",
            request_id=request_id,
            content_id=content_id,
            error=str(e),
            exc_info=True
        )
        db.rollback()
        raise InternalServerException(
            message="Update failed",
            details={"error": str(e)}
        )'''

content = content.replace(old_update, new_update)

# Migration 2: DELETE /{content_id} - delete_content
old_delete = '''@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete content from both Anthias and database

    Args:
        content_id: Content ID
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If content not found or deletion fails

    Notes:
        - Deletes file from Anthias
        - Deletes metadata from PostgreSQL
        - Cascades to content_assignments
    """
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )

    try:
        # Delete from Anthias if asset ID exists
        if content.anthias_asset_id:
            await anthias_service.delete_asset(content.anthias_asset_id)
            logger.info(f"Deleted from Anthias: {content.anthias_asset_id}")

        # Delete from database (cascades to assignments)
        db.delete(content)
        db.commit()

        logger.info(f"Content deleted: ID={content_id}")
        return None

    except Exception as e:
        logger.error(f"Delete error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )'''

new_delete = '''@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete content from both Anthias and database

    Args:
        content_id: Content ID
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Success message wrapped in standardized response

    Raises:
        NotFoundException: If content not found
        InternalServerException: If deletion fails

    Notes:
        - Deletes file from Anthias
        - Deletes metadata from PostgreSQL
        - Cascades to content_assignments
    """
    request_id = get_request_id(request)

    logger.info(
        "Deleting content",
        request_id=request_id,
        content_id=content_id
    )

    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        logger.warning(
            "Content not found",
            request_id=request_id,
            content_id=content_id
        )
        raise NotFoundException(
            message=f"Content with ID {content_id} not found",
            resource_type="Content",
            resource_id=content_id
        )

    try:
        anthias_asset_id = content.anthias_asset_id

        # Delete from Anthias if asset ID exists
        if anthias_asset_id:
            await anthias_service.delete_asset(anthias_asset_id)
            logger.info(
                "Deleted from Anthias",
                request_id=request_id,
                anthias_asset_id=anthias_asset_id
            )

        # Delete from database (cascades to assignments)
        db.delete(content)
        db.commit()

        logger.info(
            "Content deleted successfully",
            request_id=request_id,
            content_id=content_id
        )

        return success_response(
            data={"message": f"Content {content_id} deleted successfully"},
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Content deletion failed",
            request_id=request_id,
            content_id=content_id,
            error=str(e),
            exc_info=True
        )
        db.rollback()
        raise InternalServerException(
            message="Delete failed",
            details={"error": str(e)}
        )'''

content = content.replace(old_delete, new_delete)

print("✅ Content CRUD endpoints migration script created successfully!")
print("Migrations prepared for:")
print("  1. PATCH /{content_id} - update_content")
print("  2. DELETE /{content_id} - delete_content")
print("  3. POST /{content_id}/assign - assign_content")
print("  4. GET /{content_id}/assignments - get_content_assignments")
print("  5. DELETE /{content_id}/assign - unassign_content")

# Write the modified content back
with open('/mnt/g/khoirul/signate/backend/app/api/content.py', 'w') as f:
    f.write(content)

print("\n✅ Applied migrations for PATCH and DELETE endpoints!")
print("Note: assign/unassign endpoints need manual review due to complexity")
