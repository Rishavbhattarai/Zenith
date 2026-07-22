-- Zenith Phase 3: relational core linking assets, inventory, and access control.

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('field_tech', 'admin')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Lightweight asset identity/metadata. Live telemetry itself stays in
-- Phase 1's Go in-memory store (localhost:8080) -- this table just gives
-- inventory records something stable to reference.
CREATE TABLE IF NOT EXISTS assets (
    asset_id   TEXT PRIMARY KEY,
    name       TEXT,
    location   TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS parts (
    id                SERIAL PRIMARY KEY,
    part_name         TEXT UNIQUE NOT NULL,
    unit_price        NUMERIC(10, 2) NOT NULL DEFAULT 0,
    stock_quantity    INTEGER NOT NULL DEFAULT 0,
    reorder_threshold INTEGER NOT NULL DEFAULT 0,
    reorder_quantity  INTEGER NOT NULL DEFAULT 0
);

-- Audit trail of what was installed where -- the "Real-Time Inventory
-- Sync" record the handoff doc describes.
CREATE TABLE IF NOT EXISTS part_installations (
    id           SERIAL PRIMARY KEY,
    asset_id     TEXT REFERENCES assets (asset_id),
    part_id      INTEGER NOT NULL REFERENCES parts (id),
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    technician   TEXT NOT NULL,
    installed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reorder_requests (
    id         SERIAL PRIMARY KEY,
    part_id    INTEGER NOT NULL REFERENCES parts (id),
    quantity   INTEGER NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ordered', 'received', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- At most one pending reorder per part at a time -- avoids duplicate
-- reorder requests piling up while one is already outstanding.
CREATE UNIQUE INDEX IF NOT EXISTS one_pending_reorder_per_part
    ON reorder_requests (part_id)
    WHERE status = 'pending';
