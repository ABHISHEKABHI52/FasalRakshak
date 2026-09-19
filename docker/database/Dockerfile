# FasalRakshak database image: PostgreSQL 16 + PostGIS + pgvector (docs/15 §1).
# PostGIS base image provides geospatial support; pgvector (extension name
# `vector`) is installed from the PGDG repository already configured in it.
# Used for the full application schema from Phase 2 onward (fields.geometry,
# knowledge_chunks.embedding); Phase 1 needs the extensions present so that
# migrations and readiness checks behave exactly as in production.

FROM postgis/postgis:16-3.4

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*

# Extensions are created by database/init/01_extensions.sql (mounted at
# /docker-entrypoint-initdb.d by docker-compose.yml).