"""
ATLAS_SEMAR Backend - Assistant Module Routes
Follows PANDAWA Clean Architecture standards
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.api_routes import routes
from modules.assistant.dtos import VoiceCommandRequest, VoiceCommandResponse

router = APIRouter(prefix=routes.ASSISTANT, tags=["assistant"])


@router.post("/voice", response_model=VoiceCommandResponse)
async def process_voice_command(
    request: VoiceCommandRequest, db: Session = Depends(get_db)
):
    """
    Process voice command

    Args:
        request: Voice command request with audio data
        db: Database session

    Returns:
        Voice command response with transcript and status
    """
    # TODO: Implement voice command processing logic
    # 1. Call STT service to transcribe audio
    # 2. Parse command from transcript
    # 3. Execute command via CommandExecutor
    # 4. Return response

    raise HTTPException(
        status_code=501, detail="Voice command processing not yet implemented"
    )
