"""
Imports all SQLModel models so they are registered with SQLModel.metadata.

This is used by Alembic and test fixtures that need access to the complete database schema.
"""

from app.users.models import User
