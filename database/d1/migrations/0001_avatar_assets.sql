CREATE TABLE IF NOT EXISTS avatar_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_type TEXT NOT NULL,
    gender TEXT NOT NULL,
    name TEXT NOT NULL,
    source_index INTEGER NOT NULL DEFAULT 0,
    availability TEXT NOT NULL DEFAULT '',
    match_status TEXT NOT NULL DEFAULT '',
    series TEXT NOT NULL DEFAULT '',
    confidence TEXT NOT NULL DEFAULT '',
    master_resource_id TEXT NOT NULL,
    group_id TEXT NOT NULL DEFAULT '',
    group_size INTEGER NOT NULL DEFAULT 1,
    master_color_hex TEXT NOT NULL DEFAULT '',
    master_is_group_canonical INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset_type, gender, master_resource_id)
);

CREATE TABLE IF NOT EXISTS avatar_asset_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    avatar_asset_id INTEGER NOT NULL REFERENCES avatar_assets(id) ON DELETE CASCADE,
    resource_id TEXT NOT NULL,
    thumbnail_url TEXT NOT NULL DEFAULT '',
    hex_code TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL DEFAULT '',
    dname TEXT NOT NULL DEFAULT '',
    UNIQUE(avatar_asset_id, resource_id)
);

CREATE INDEX IF NOT EXISTS idx_avatar_assets_type_gender ON avatar_assets(asset_type, gender);
CREATE INDEX IF NOT EXISTS idx_avatar_assets_name ON avatar_assets(name);
CREATE INDEX IF NOT EXISTS idx_avatar_asset_variants_asset_id ON avatar_asset_variants(avatar_asset_id);
CREATE INDEX IF NOT EXISTS idx_avatar_asset_variants_resource_id ON avatar_asset_variants(resource_id);
