-- Migration 023: PMS Integration Tables
-- Phase 5: Firebird PMS Integration

-- Guest Data from PMS (synced from Firebird)
CREATE TABLE IF NOT EXISTS pms_guests (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Guest Information
    guest_name VARCHAR(255) NOT NULL,
    room_number VARCHAR(50) NOT NULL,
    checkin_date TIMESTAMP NOT NULL,
    checkout_date TIMESTAMP NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    country VARCHAR(100),
    reservation_no VARCHAR(100),

    -- Sync Metadata
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Room Status from PMS
CREATE TABLE IF NOT EXISTS pms_rooms (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Room Information
    room_number VARCHAR(50) NOT NULL,
    room_type VARCHAR(100),
    status VARCHAR(50) NOT NULL,  -- available, occupied, cleaning, maintenance
    floor VARCHAR(20),
    bed_type VARCHAR(50),
    max_occupancy INTEGER,

    -- Sync Metadata
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint: one record per room per organization
    UNIQUE(organization_id, room_number)
);

-- PMS Configuration (Firebird connection settings per organization)
CREATE TABLE IF NOT EXISTS pms_configurations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE UNIQUE,

    -- API Key for Bridge Agent authentication
    api_key VARCHAR(255) NOT NULL UNIQUE,

    -- Configuration
    is_active BOOLEAN DEFAULT true,
    last_sync TIMESTAMP,
    sync_interval_minutes INTEGER DEFAULT 5,

    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_pms_guests_org ON pms_guests(organization_id);
CREATE INDEX IF NOT EXISTS idx_pms_guests_checkin ON pms_guests(checkin_date);
CREATE INDEX IF NOT EXISTS idx_pms_guests_room ON pms_guests(room_number);

CREATE INDEX IF NOT EXISTS idx_pms_rooms_org ON pms_rooms(organization_id);
CREATE INDEX IF NOT EXISTS idx_pms_rooms_status ON pms_rooms(status);
CREATE INDEX IF NOT EXISTS idx_pms_rooms_number ON pms_rooms(room_number);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_pms_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pms_guests_updated_at
    BEFORE UPDATE ON pms_guests
    FOR EACH ROW
    EXECUTE FUNCTION update_pms_updated_at();

CREATE TRIGGER pms_rooms_updated_at
    BEFORE UPDATE ON pms_rooms
    FOR EACH ROW
    EXECUTE FUNCTION update_pms_updated_at();

CREATE TRIGGER pms_configurations_updated_at
    BEFORE UPDATE ON pms_configurations
    FOR EACH ROW
    EXECUTE FUNCTION update_pms_updated_at();
