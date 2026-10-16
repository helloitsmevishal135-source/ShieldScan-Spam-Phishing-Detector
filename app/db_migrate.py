"""
db_migrate.py — SQLite migration module (no longer needed with MongoDB).
MongoDB/MongoEngine creates collections and indexes automatically.
This stub is kept to avoid import errors from any residual references.
"""


def ensure_schema():
    """No-op: MongoDB schema is schema-less; MongoEngine handles indexes automatically."""
    pass
