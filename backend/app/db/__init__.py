# TODO(Phase 1): SQLAlchemy models + session go here.
#
# You'll likely want:
#   - session.py   -> engine + SessionLocal, get_db() dependency
#   - models.py    -> Document, Chunk (with a pgvector Vector column), User, etc.
#
# Settings.database_url (app/core/config.py) already points at the
# docker-compose Postgres instance — pgvector extension is enabled via
# db/init/001_extensions.sql on first container start.
