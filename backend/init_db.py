#!/usr/bin/env python3
"""Initialize database tables."""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.database import engine, Base
from app.models.user import User
from app.models.datasource import DataSource
from app.models.audit import AuditLog


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
