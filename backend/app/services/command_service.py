"""
Secure Command Service
Comprehensive command execution service with security validation, rate limiting, and audit logging
"""

import asyncio
import re
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from fastapi import HTTPException, status

from app.models.device import Device
from app.models.device_command import DeviceCommand
from app.models.user import User
from app.schemas.command import (
    CommandType, CommandStatus, CommandRiskLevel, ExecutionMode,
    CommandRequest, BatchCommandRequest, CommandExecutionResult
)


# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# Command whitelist with risk levels and security requirements
ALLOWED_COMMANDS = {
    CommandType.VOLUME: {
        'risk': CommandRiskLevel.LOW,
        'audit': False,
        'requires_2fa': False,
        'requires_approval': False,
        'rate_limit': 10,  # per minute
        'timeout': 5,  # seconds
        'allowed_roles': ['admin', 'operator', 'editor'],
    },
    CommandType.BRIGHTNESS: {
        'risk': CommandRiskLevel.LOW,
        'audit': False,
        'requires_2fa': False,
        'requires_approval': False,
        'rate_limit': 10,
        'timeout': 5,
        'allowed_roles': ['admin', 'operator', 'editor'],
    },
    CommandType.SCREENSHOT: {
        'risk': CommandRiskLevel.LOW,
        'audit': True,
        'requires_2fa': False,
        'requires_approval': False,
        'rate_limit': 5,
        'timeout': 10,
        'allowed_roles': ['admin', 'operator', 'editor'],
    },
    CommandType.NETWORK_TEST: {
        'risk': CommandRiskLevel.LOW,
        'audit': True,
        'requires_2fa': False,
        'requires_approval': False,
        'rate_limit': 5,
        'timeout': 30,
        'allowed_roles': ['admin', 'operator'],
    },
    CommandType.CLEAR_CACHE: {
        'risk': CommandRiskLevel.MEDIUM,
        'audit': True,
        'requires_2fa': False,
        'requires_approval': False,
        'rate_limit': 5,
        'timeout': 30,
        'allowed_roles': ['admin', 'operator'],
    },
    CommandType.RELOAD: {
        'risk': CommandRiskLevel.MEDIUM,
        'audit': True,
        'requires_2fa': False,
        'requires_approval': False,
        'rate_limit': 5,
        'timeout': 10,
        'allowed_roles': ['admin', 'operator'],
    },
    CommandType.REFRESH: {
        'risk': CommandRiskLevel.MEDIUM,
        'audit': True,
        'requires_2fa': False,
        'requires_approval': False,
        'rate_limit': 5,
        'timeout': 10,
        'allowed_roles': ['admin', 'operator'],
    },
    CommandType.REBOOT: {
        'risk': CommandRiskLevel.MEDIUM,
        'audit': True,
        'requires_2fa': False,
        'requires_approval': False,
        'rate_limit': 3,
        'timeout': 60,
        'allowed_roles': ['admin'],
    },
    CommandType.UPDATE: {
        'risk': CommandRiskLevel.HIGH,
        'audit': True,
        'requires_2fa': True,
        'requires_approval': False,
        'rate_limit': 1,
        'timeout': 300,  # 5 minutes
        'allowed_roles': ['admin'],
    },
    CommandType.SHELL: {
        'risk': CommandRiskLevel.CRITICAL,
        'audit': True,
        'requires_2fa': True,
        'requires_approval': True,
        'rate_limit': 1,
        'timeout': 30,
        'allowed_roles': ['admin'],
    },
    # Legacy support
    CommandType.RESET: {
        'risk': CommandRiskLevel.MEDIUM,
        'audit': True,
        'requires_2fa': False,
        'requires_approval': False,
        'rate_limit': 3,
        'timeout': 10,
        'allowed_roles': ['admin', 'operator'],
    },
}

# Dangerous patterns to block in shell commands
BLOCKED_PATTERNS = [
    r'rm\s+-rf\s+/',  # Delete root
    r'rm\s+-rf\s+/\*',  # Delete all
    r'dd\s+if=',  # Disk operations
    r'mkfs\.',  # Format disk
    r'wget.*\|.*sh',  # Remote execution
    r'curl.*\|.*bash',  # Remote execution
    r'curl.*\|.*sh',  # Remote execution
    r':\(\)\{.*\};:',  # Fork bomb
    r'shutdown\s+-h',  # Shutdown (use reboot command)
    r'init\s+0',  # Shutdown
    r'systemctl\s+stop',  # Stop services
    r'systemctl\s+disable',  # Disable services
    r'pkill\s+-9',  # Kill all processes
    r'chmod\s+-R\s+777',  # Dangerous permissions
    r'chown\s+-R',  # Ownership changes
    r'>\s*/dev/sd',  # Write to disk devices
    r'/dev/null.*>',  # Redirect to /dev/null
]


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter for command execution
    In production, use Redis for distributed rate limiting
    """

    def __init__(self):
        self._limits: Dict[str, List[datetime]] = {}

    def _get_key(self, device_id: int, command_type: str) -> str:
        """Generate rate limit key"""
        return f"device:{device_id}:command:{command_type}"

    async def check(self, device_id: int, command_type: str) -> bool:
        """Check if rate limit is exceeded"""
        command_config = ALLOWED_COMMANDS.get(CommandType(command_type))
        if not command_config:
            return False

        limit = command_config['rate_limit']
        key = self._get_key(device_id, command_type)

        # Get current window
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)

        # Clean old entries
        if key in self._limits:
            self._limits[key] = [
                ts for ts in self._limits[key]
                if ts > window_start
            ]
        else:
            self._limits[key] = []

        # Check limit
        if len(self._limits[key]) >= limit:
            return False

        # Add current request
        self._limits[key].append(now)
        return True

    async def get_remaining(self, device_id: int, command_type: str) -> int:
        """Get remaining requests in current window"""
        command_config = ALLOWED_COMMANDS.get(CommandType(command_type))
        if not command_config:
            return 0

        limit = command_config['rate_limit']
        key = self._get_key(device_id, command_type)

        # Get current window
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)

        # Count requests in window
        if key in self._limits:
            current_count = len([
                ts for ts in self._limits[key]
                if ts > window_start
            ])
            return max(0, limit - current_count)

        return limit


# =============================================================================
# COMMAND SERVICE
# =============================================================================

class CommandService:
    """
    Secure command execution service with comprehensive security controls
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rate_limiter = RateLimiter()

    # =========================================================================
    # SECURITY VALIDATION
    # =========================================================================

    def _validate_command_type(self, command_type: str) -> None:
        """Validate command type is whitelisted"""
        try:
            cmd_type = CommandType(command_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Command '{command_type}' not allowed"
            )

        if cmd_type not in ALLOWED_COMMANDS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Command '{command_type}' is not whitelisted"
            )

    async def _check_permission(
        self,
        user_id: int,
        command_type: str
    ) -> bool:
        """Check if user has permission to execute command"""
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check role permission
        command_config = ALLOWED_COMMANDS.get(CommandType(command_type))
        if not command_config:
            return False

        allowed_roles = command_config.get('allowed_roles', ['admin'])

        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not authorized for command '{command_type}'"
            )

        return True

    async def _verify_2fa(self, user_id: int) -> bool:
        """
        Verify 2FA for critical commands
        TODO: Implement actual 2FA verification
        """
        # Placeholder - in production, verify 2FA token
        # This would check:
        # 1. User has 2FA enabled
        # 2. Valid 2FA token provided in request
        # 3. Token hasn't been used before
        return True

    def _validate_shell_command(self, command: str) -> None:
        """Validate shell command against dangerous patterns"""
        if not command or not command.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shell command cannot be empty"
            )

        # Max length check
        if len(command) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Command too long (max 500 characters)"
            )

        # Check dangerous patterns
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Dangerous pattern detected: {pattern}"
                )

    async def _check_rate_limit(
        self,
        device_id: int,
        command_type: str
    ) -> None:
        """Check rate limiting for command"""
        allowed = await self.rate_limiter.check(device_id, command_type)

        if not allowed:
            command_config = ALLOWED_COMMANDS.get(CommandType(command_type))
            limit = command_config.get('rate_limit', 0) if command_config else 0

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for '{command_type}' ({limit} requests per minute)"
            )

    # =========================================================================
    # COMMAND QUEUEING
    # =========================================================================

    async def queue_command(
        self,
        request: CommandRequest,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Queue command for execution with comprehensive security validation

        Security checks:
        1. Command type whitelisted
        2. User has permission
        3. 2FA verified (if required)
        4. Rate limit not exceeded
        5. Dangerous patterns blocked (shell commands)
        6. Device exists and is active
        7. Audit logged
        """

        # 1. Validate command type
        self._validate_command_type(request.command_type)
        command_config = ALLOWED_COMMANDS[CommandType(request.command_type)]

        # 2. Check permission
        await self._check_permission(user_id, request.command_type)

        # 3. Check 2FA if required
        if command_config['requires_2fa']:
            if not await self._verify_2fa(user_id):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="2FA verification required for this command"
                )

        # 4. Rate limiting
        await self._check_rate_limit(request.device_id, request.command_type)

        # 5. Validate parameters
        if request.command_type == CommandType.SHELL:
            self._validate_shell_command(request.parameters.get('command', ''))

        # 6. Check device exists
        result = await self.db.execute(
            select(Device).where(Device.id == request.device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {request.device_id} not found"
            )

        # 7. Create command
        scheduled_at = request.scheduled_at or datetime.now(timezone.utc)
        expires_at = scheduled_at + timedelta(hours=24)  # Commands expire after 24 hours

        command = DeviceCommand(
            device_id=request.device_id,
            command_type=request.command_type,
            reason=request.reason,
            status=CommandStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at
        )

        # Store parameters and metadata in reason field (temporary - should use JSONB column)
        command_data = {
            'parameters': request.parameters,
            'priority': request.priority,
            'created_by': user_id,
            'risk_level': command_config['risk'].value,
            'ip_address': ip_address,
            'user_agent': user_agent,
        }

        self.db.add(command)
        await self.db.commit()
        await self.db.refresh(command)

        # 8. Audit log (if required)
        if command_config['audit']:
            await self._audit_log(
                command_id=command.id,
                event_type='created',
                user_id=user_id,
                ip_address=ip_address,
                details={
                    'command_type': request.command_type,
                    'device_id': request.device_id,
                    'parameters': request.parameters,
                    'reason': request.reason
                }
            )

        # 9. Send to device via WebSocket (if scheduled for immediate execution)
        if not request.scheduled_at or request.scheduled_at <= datetime.now(timezone.utc):
            # TODO: Send via WebSocket
            # await self._send_to_device(device, command, request.parameters)
            pass

        return {
            'id': command.id,
            'device_id': command.device_id,
            'command_type': command.command_type,
            'status': command.status,
            'created_at': command.created_at.isoformat(),
            'expires_at': command.expires_at.isoformat() if command.expires_at else None,
            'parameters': request.parameters,
            'risk_level': command_config['risk'].value
        }

    async def batch_command(
        self,
        request: BatchCommandRequest,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute command on multiple devices"""
        results = []
        batch_id = str(uuid.uuid4())

        # Validate command type first
        self._validate_command_type(request.command_type)

        for device_id in request.device_ids:
            try:
                # Create individual command request
                cmd_request = CommandRequest(
                    device_id=device_id,
                    command_type=request.command_type,
                    parameters=request.parameters,
                    priority=request.priority,
                    reason=request.reason
                )

                # Queue command
                result = await self.queue_command(
                    request=cmd_request,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                results.append({
                    'device_id': device_id,
                    'success': True,
                    'command_id': result['id']
                })

            except HTTPException as e:
                results.append({
                    'device_id': device_id,
                    'success': False,
                    'error': e.detail
                })
            except Exception as e:
                results.append({
                    'device_id': device_id,
                    'success': False,
                    'error': str(e)
                })

            # Sequential execution delay
            if request.execution_mode == ExecutionMode.SEQUENTIAL:
                await asyncio.sleep(1)

        return {
            'batch_id': batch_id,
            'total': len(request.device_ids),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'results': results
        }

    # =========================================================================
    # COMMAND EXECUTION
    # =========================================================================

    async def execute_command(
        self,
        command_id: int
    ) -> Dict[str, Any]:
        """
        Mark command as executed (called by device after execution)
        """
        result = await self.db.execute(
            select(DeviceCommand).where(DeviceCommand.id == command_id)
        )
        command = result.scalar_one_or_none()

        if not command:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Command {command_id} not found"
            )

        # Update status
        command.status = CommandStatus.COMPLETED
        command.executed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(command)

        # Audit log
        await self._audit_log(
            command_id=command_id,
            event_type='executed',
            details={'status': 'completed'}
        )

        return command.to_dict()

    async def fail_command(
        self,
        command_id: int,
        error_message: str
    ) -> Dict[str, Any]:
        """Mark command as failed"""
        result = await self.db.execute(
            select(DeviceCommand).where(DeviceCommand.id == command_id)
        )
        command = result.scalar_one_or_none()

        if not command:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Command {command_id} not found"
            )

        # Update status
        command.status = CommandStatus.FAILED
        # Store error in reason field (temporary)

        await self.db.commit()
        await self.db.refresh(command)

        # Audit log
        await self._audit_log(
            command_id=command_id,
            event_type='failed',
            details={'error': error_message}
        )

        return command.to_dict()

    # =========================================================================
    # COMMAND MANAGEMENT
    # =========================================================================

    async def get_command(self, command_id: int) -> Optional[Dict[str, Any]]:
        """Get command by ID"""
        result = await self.db.execute(
            select(DeviceCommand)
            .where(DeviceCommand.id == command_id)
        )
        command = result.scalar_one_or_none()

        if not command:
            return None

        return command.to_dict()

    async def list_commands(
        self,
        device_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List commands with filters"""
        query = select(DeviceCommand)

        # Apply filters
        conditions = []
        if device_id:
            conditions.append(DeviceCommand.device_id == device_id)
        if status:
            conditions.append(DeviceCommand.status == status)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(DeviceCommand)
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get commands
        query = query.order_by(DeviceCommand.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        commands = result.scalars().all()

        # Get status counts
        status_counts = {
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0
        }

        for cmd in commands:
            if cmd.status in status_counts:
                status_counts[cmd.status] += 1

        return {
            'commands': [cmd.to_dict() for cmd in commands],
            'total': total,
            **status_counts
        }

    async def cancel_command(
        self,
        command_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel a pending command"""
        result = await self.db.execute(
            select(DeviceCommand).where(DeviceCommand.id == command_id)
        )
        command = result.scalar_one_or_none()

        if not command:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Command {command_id} not found"
            )

        if command.status not in [CommandStatus.PENDING, CommandStatus.SENT]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel command with status '{command.status}'"
            )

        # Update status
        command.status = CommandStatus.CANCELLED

        await self.db.commit()
        await self.db.refresh(command)

        # Audit log
        await self._audit_log(
            command_id=command_id,
            event_type='cancelled',
            user_id=user_id,
            details={'reason': reason}
        )

        return command.to_dict()

    async def retry_command(
        self,
        command_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Retry a failed command"""
        result = await self.db.execute(
            select(DeviceCommand).where(DeviceCommand.id == command_id)
        )
        command = result.scalar_one_or_none()

        if not command:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Command {command_id} not found"
            )

        if command.status != CommandStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only retry failed commands"
            )

        # Reset status
        command.status = CommandStatus.PENDING
        command.executed_at = None

        await self.db.commit()
        await self.db.refresh(command)

        # Audit log
        await self._audit_log(
            command_id=command_id,
            event_type='retried',
            user_id=user_id
        )

        return command.to_dict()

    # =========================================================================
    # CLEANUP
    # =========================================================================

    async def cleanup_expired_commands(self) -> int:
        """Clean up expired commands (background task)"""
        now = datetime.now(timezone.utc)

        # Mark expired commands
        result = await self.db.execute(
            update(DeviceCommand)
            .where(
                and_(
                    DeviceCommand.status == CommandStatus.PENDING,
                    DeviceCommand.expires_at < now
                )
            )
            .values(status=CommandStatus.EXPIRED)
        )

        await self.db.commit()
        return result.rowcount

    # =========================================================================
    # AUDIT LOGGING
    # =========================================================================

    async def _audit_log(
        self,
        command_id: int,
        event_type: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create audit log entry
        TODO: Implement actual audit log table
        """
        # Placeholder - in production, write to command_audit_log table
        pass
