# CHAT-LAW-006: Append-Only History

**Status**: IMMUTABLE
**Created**: 2026-01-25
**Category**: Data Integrity

---

## Statement

> Chat history adalah audit trail dan TIDAK BOLEH dimodifikasi atau dihapus.
> Hanya operasi INSERT yang diperbolehkan pada chat messages.

---

## Rationale

1. **Audit Trail** - Chat history adalah bukti interaksi
2. **Compliance** - Beberapa industri memerlukan record retention
3. **Debug** - Untuk trace masalah, history harus utuh
4. **Trust** - User harus yakin historynya tidak dimanipulasi
5. **AI Learning** - History digunakan untuk context, tidak boleh corrupt

---

## Allowed Operations

### Messages Table

| Operation | Allowed? | Notes |
|-----------|----------|-------|
| INSERT | YES | Normal operation |
| SELECT | YES | Read anytime |
| UPDATE | NO | Never modify content |
| DELETE | NO | Never delete |

### Exceptions (dengan approval)

| Operation | Condition | Who Can Approve |
|-----------|-----------|-----------------|
| Soft Delete | Legal/compliance request | Legal team |
| Anonymize | GDPR right-to-be-forgotten | Data Protection Officer |
| Purge | Account deletion | User + System |

---

## Implementation

### Database Constraints

```sql
-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id),
    tenant_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(200) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- No updated_at column! Messages are immutable

    -- Soft delete for compliance only
    is_redacted BOOLEAN DEFAULT FALSE,
    redacted_at TIMESTAMPTZ,
    redacted_by VARCHAR(200),
    redaction_reason VARCHAR(500)
);

-- Prevent UPDATE on content
CREATE OR REPLACE FUNCTION prevent_message_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.content IS DISTINCT FROM NEW.content THEN
        RAISE EXCEPTION 'Cannot update message content. Messages are immutable.';
    END IF;
    IF OLD.role IS DISTINCT FROM NEW.role THEN
        RAISE EXCEPTION 'Cannot update message role. Messages are immutable.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_message_immutability
    BEFORE UPDATE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION prevent_message_update();

-- Prevent DELETE entirely
CREATE OR REPLACE FUNCTION prevent_message_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Cannot delete messages. Use redaction for compliance.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_no_delete
    BEFORE DELETE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION prevent_message_delete();
```

### Redaction (Soft Delete)

```python
class MessageRepository:
    async def redact_message(
        self,
        message_id: str,
        redacted_by: str,
        reason: str,
        approval_ticket: str  # WAJIB ada ticket/approval
    ):
        """
        Redact message content for compliance.
        Original content is replaced with [REDACTED].
        """
        await self.db.execute(
            """
            UPDATE chat_messages
            SET
                is_redacted = TRUE,
                redacted_at = NOW(),
                redacted_by = $2,
                redaction_reason = $3,
                content = '[REDACTED: ' || $3 || ']'
            WHERE id = $1
            """,
            message_id, redacted_by, reason
        )

        # Log the redaction
        await self.audit_log.log(
            action="MESSAGE_REDACTED",
            message_id=message_id,
            by=redacted_by,
            reason=reason,
            approval_ticket=approval_ticket
        )
```

---

## Constraints

### REQUIREMENT
- Messages table HARUS punya trigger untuk prevent UPDATE
- Messages table HARUS punya trigger untuk prevent DELETE
- Redaction HARUS di-log ke audit trail
- Redaction HARUS memerlukan approval ticket

### PROHIBITION
- DILARANG UPDATE content field
- DILARANG DELETE rows
- DILARANG bypass trigger dengan TRUNCATE atau ALTER
- DILARANG raw SQL yang modify messages

### LIMITATION
- Redaction hanya untuk compliance (GDPR, legal)
- Redaction memerlukan approval dari authorized role
- Maximum retention: indefinite (atau sesuai tenant policy)

---

## User-Facing Features

### What users CAN do:
- View their chat history
- Search their chat history
- Export their chat history
- Request redaction (via support ticket)

### What users CANNOT do:
- Edit past messages
- Delete individual messages
- Clear history (tanpa formal request)

### Session Deletion

```python
async def delete_session(
    self,
    session_id: str,
    user_id: str,
    confirmation: str  # User must type "DELETE"
):
    """
    Soft-delete a session. Messages remain for audit.
    """
    if confirmation != "DELETE":
        raise ValueError("Must confirm with 'DELETE'")

    await self.db.execute(
        """
        UPDATE chat_sessions
        SET
            is_deleted = TRUE,
            deleted_at = NOW(),
            deleted_by = $2
        WHERE id = $1 AND user_id = $2
        """,
        session_id, user_id
    )

    # Messages are NOT deleted, just hidden from user view
    # Admin/compliance can still access
```

---

## Invariants

1. Message content yang sudah INSERT tidak pernah berubah
2. Setiap redaction tercatat di audit log
3. Deleted sessions tidak menghapus messages
4. Database triggers aktif dan tidak bisa di-bypass
