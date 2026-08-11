ALTER TABLE assets ADD COLUMN source_provider TEXT NOT NULL DEFAULT '';
ALTER TABLE assets ADD COLUMN source_resource_id TEXT NOT NULL DEFAULT '';
ALTER TABLE assets ADD COLUMN source_url TEXT NOT NULL DEFAULT '';

ALTER TABLE document_assets ADD COLUMN linked_asset_id INTEGER REFERENCES assets(id) ON DELETE RESTRICT;
ALTER TABLE document_assets ADD COLUMN owns_object INTEGER NOT NULL DEFAULT 1;
ALTER TABLE document_assets ADD COLUMN alt_text TEXT NOT NULL DEFAULT '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_assets_external_source
ON assets(source_provider, source_resource_id)
WHERE source_provider != '' AND source_resource_id != '';

CREATE INDEX IF NOT EXISTS idx_document_assets_linked_asset_id
ON document_assets(linked_asset_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_document_assets_document_link
ON document_assets(document_id, linked_asset_id)
WHERE document_id IS NOT NULL AND linked_asset_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_document_assets_draft_link
ON document_assets(draft_key, linked_asset_id)
WHERE draft_key IS NOT NULL AND linked_asset_id IS NOT NULL;
