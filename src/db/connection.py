"""
Database Connection Management
==============================

Provides async SQLite connection with SQLAlchemy 2.0.
Supports both sync and async operations for flexibility.

Usage:
    # Async context manager
    async with get_db_session() as session:
        result = await session.execute(select(GrowSession))

    # Or via DatabaseManager
    db = DatabaseManager("sqlite+aiosqlite:///data/grokmon.db")
    await db.initialize()
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base


# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "grokmon.db"


class DatabaseManager:
    """
    Manages database connections and sessions.

    Supports:
    - SQLite (default, file-based)
    - Async operations via aiosqlite
    - Connection pooling
    - Automatic table creation
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        echo: bool = False,
    ):
        """
        Initialize database manager.

        Args:
            database_url: SQLAlchemy connection URL.
                         Default: sqlite+aiosqlite:///data/grokmon.db
            echo: If True, log all SQL statements
        """
        if database_url is None:
            # Ensure data directory exists
            DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            database_url = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"

        self.database_url = database_url
        self.echo = echo

        # Async engine and session factory
        self._async_engine: Optional[AsyncEngine] = None
        self._async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None

        # Sync engine for migrations and simple operations
        self._sync_engine = None
        self._sync_session_factory = None

    @property
    def async_engine(self) -> AsyncEngine:
        """Get or create async engine"""
        if self._async_engine is None:
            # For SQLite, use StaticPool to share connection in async context
            connect_args = {}
            poolclass = None

            if "sqlite" in self.database_url:
                connect_args = {"check_same_thread": False}
                poolclass = StaticPool

            self._async_engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                connect_args=connect_args,
                poolclass=poolclass,
            )

        return self._async_engine

    @property
    def async_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create async session factory"""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._async_session_factory

    @property
    def sync_engine(self):
        """Get or create sync engine (for migrations)"""
        if self._sync_engine is None:
            # Convert async URL to sync for migrations
            sync_url = self.database_url.replace("+aiosqlite", "")
            connect_args = {}

            if "sqlite" in sync_url:
                connect_args = {"check_same_thread": False}

            self._sync_engine = create_engine(
                sync_url,
                echo=self.echo,
                connect_args=connect_args,
            )

            # Enable foreign keys for SQLite
            if "sqlite" in sync_url:
                @event.listens_for(self._sync_engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA busy_timeout=5000")
                    cursor.close()

        return self._sync_engine

    @property
    def sync_session_factory(self) -> sessionmaker[Session]:
        """Get or create sync session factory"""
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                bind=self.sync_engine,
                expire_on_commit=False,
            )
        return self._sync_session_factory

    async def initialize(self) -> None:
        """
        Initialize database - create tables if they don't exist.

        Call this on application startup.
        """
        async with self.async_engine.begin() as conn:
            # Enable foreign keys and WAL mode for SQLite
            if "sqlite" in self.database_url:
                await conn.execute(text("PRAGMA foreign_keys=ON"))
                await conn.execute(text("PRAGMA journal_mode=WAL"))
                await conn.execute(text("PRAGMA busy_timeout=5000"))

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

    def initialize_sync(self) -> None:
        """Synchronous initialization for migrations/scripts"""
        Base.metadata.create_all(bind=self.sync_engine)

    async def close(self) -> None:
        """Close database connections"""
        if self._async_engine:
            await self._async_engine.dispose()
            self._async_engine = None

        if self._sync_engine:
            self._sync_engine.dispose()
            self._sync_engine = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions.

        Usage:
            async with db.session() as session:
                session.add(my_object)
                await session.commit()
        """
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def session_sync(self) -> Session:
        """Get a sync session (caller must manage lifecycle)"""
        return self.sync_session_factory()


# =============================================================================
# Global database instance and helpers
# =============================================================================

# Global database manager (initialized on first use)
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager, creating it if needed"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def set_db_manager(manager: DatabaseManager) -> None:
    """Set a custom database manager (for testing)"""
    global _db_manager
    _db_manager = manager


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Convenience function to get a database session.

    Usage:
        async with get_db_session() as session:
            result = await session.execute(select(GrowSession))
    """
    db = get_db_manager()
    async with db.session() as session:
        yield session


async def init_database(database_url: Optional[str] = None) -> DatabaseManager:
    """
    Initialize the database on application startup.

    Args:
        database_url: Optional custom database URL

    Returns:
        DatabaseManager instance
    """
    global _db_manager

    if database_url:
        _db_manager = DatabaseManager(database_url)
    else:
        _db_manager = get_db_manager()

    await _db_manager.initialize()
    return _db_manager


async def close_database() -> None:
    """Close database connections on shutdown"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
