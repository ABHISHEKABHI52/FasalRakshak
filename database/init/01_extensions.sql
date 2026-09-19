-- FasalRakshak database extensions (docs/07 §9, docs/15 §3).
-- Executed on first container start by the postgres entrypoint.

-- Geospatial support (PostGIS): geography/geometry columns, GIST indexes,
-- spatial aggregation for GIS Intelligence (docs/09).
CREATE EXTENSION IF NOT EXISTS postgis;

-- Vector support (pgvector): knowledge_chunks.embedding for the RAG layer
-- (docs/11 §2). Extension name is `vector`.
CREATE EXTENSION IF NOT EXISTS vector;