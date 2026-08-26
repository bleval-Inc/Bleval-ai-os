"""Database Manager — Manages four isolated domain databases with async SQLAlchemy."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional, List, TYPE_CHECKING

from sqlalchemy import MetaData, create_engine, event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from axiom.config import settings

if TYPE_CHECKING:
    from axiom.runtime.logging import RuntimeLogger


class Domain(str, Enum):
    """Database domains."""

    BLEVAL = "bleval"  # Sales, CRM, deals, campaigns
    MARKET = "market"  # Market data, trading, MT5
    RESEARCH = "research"  # Web research, news, knowledge
    COMMS = "comms"  # Communications, Slack, email, calendar


@dataclass
class DatabaseConfig:
    """Database configuration."""

    domain: Domain
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: float = 30.0
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    echo: bool = False
    # Read replica (optional)
    read_replica_url: Optional[str] = None
    read_pool_size: int = 5
    # Migration
    migration_path: Optional[str] = None


class DomainDatabase:
    """Single domain database with async engine and session management."""

    def __init__(
        self,
        config: DatabaseConfig,
        base: "DeclarativeBase",
        logger: Optional["RuntimeLogger"] = None,
    ) -> None:
        self.config = config
        self.base = base
        # Lazy import to avoid circular dependency
        from axiom.runtime.logging import RuntimeLogger
        self.logger = logger or RuntimeLogger()

        # Primary (write) engine
        self.engine: AsyncEngine = create_async_engine(
            config.url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=config.pool_pre_ping,
            echo=config.echo,
            poolclass=NullPool if config.pool_size == 0 else None,
        )

        # Read replica engine (falls back to primary if not configured)
        read_url = config.read_replica_url or config.url
        self.read_engine: AsyncEngine = create_async_engine(
            read_url,
            pool_size=config.read_pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=config.pool_pre_ping,
            echo=config.echo,
            poolclass=NullPool if config.read_pool_size == 0 else None,
        )

        # Session factories
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        self.read_session_factory = async_sessionmaker(
            self.read_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        self._initialized = False

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a write session."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def read_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a read-only session (uses read replica if available)."""
        async with self.read_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def initialize(self) -> None:
        """Create all tables."""
        if self._initialized:
            return

        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.create_all)

        self._initialized = True
        self.logger.info(f"Database {self.config.domain.value} initialized")

    async def drop_all(self) -> None:
        """Drop all tables (dangerous!)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.drop_all)
        self._initialized = False
        self.logger.warning(f"Database {self.config.domain.value} dropped")

    async def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            async with self.session() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "healthy", "domain": self.config.domain.value}
        except Exception as e:
            return {"status": "unhealthy", "domain": self.config.domain.value, "error": str(e)}

    async def close(self) -> None:
        """Close engine connections."""
        await self.engine.dispose()
        await self.read_engine.dispose()
        self.logger.info("database", f"Database {self.config.domain.value} closed")


class DatabaseManager:
    """Manages all four domain databases."""

    def __init__(self, logger: Optional["RuntimeLogger"] = None) -> None:
        from axiom.runtime.logging import RuntimeLogger
        self.logger = logger or RuntimeLogger()
        self._databases: Dict[Domain, DomainDatabase] = {}
        self._bases: Dict[Domain, DeclarativeBase] = {}

    def register_domain(
        self,
        domain: Domain,
        base: DeclarativeBase,
        config: DatabaseConfig,
    ) -> None:
        """Register a domain database."""
        self._bases[domain] = base
        self._databases[domain] = DomainDatabase(config, base, self.logger)

    def get_database(self, domain: Domain) -> Optional[DomainDatabase]:
        """Get a domain database."""
        return self._databases.get(domain)

    def get_session(self, domain: Domain):
        """Get write session for domain."""
        db = self._databases.get(domain)
        if not db:
            raise ValueError(f"Domain {domain.value} not registered")
        return db.session()

    def get_read_session(self, domain: Domain):
        """Get read session for domain."""
        db = self._databases.get(domain)
        if not db:
            raise ValueError(f"Domain {domain.value} not registered")
        return db.read_session()

    async def initialize_all(self) -> None:
        """Initialize all registered databases."""
        for domain, db in self._databases.items():
            await db.initialize()

    async def health_check_all(self) -> Dict[str, Any]:
        """Health check all databases."""
        results = {}
        for domain, db in self._databases.items():
            results[domain.value] = await db.health_check()
        return results

    async def close_all(self) -> None:
        """Close all databases."""
        for db in self._databases.values():
            await db.close()
        self._databases.clear()
        self._bases.clear()

    def get_status(self) -> Dict[str, Any]:
        """Get status of all registered databases."""
        return {
            "databases": {
                domain.value: {
                    "initialized": db._initialized,
                    "domain": domain.value,
                    "config": {
                        "url": db.config.url,
                        "pool_size": db.config.pool_size,
                        "max_overflow": db.config.max_overflow,
                        "echo": db.config.echo,
                    }
                }
                for domain, db in self._databases.items()
            }
        }

    @property
    def registered_domains(self) -> List[Domain]:
        """Get list of registered domains."""
        return list(self._databases.keys())


# Global manager instance
_database_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get global database manager."""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager()
    return _database_manager


async def create_database_configs() -> Dict[Domain, DatabaseConfig]:
    """Create database configurations from settings."""
    data_dir = Path(settings.data_dir) / "databases"
    data_dir.mkdir(parents=True, exist_ok=True)

    configs = {}
    for domain in Domain:
        db_path = data_dir / f"{domain.value}.db"
        url = f"sqlite+aiosqlite:///{db_path}"

        # For production, use PostgreSQL:
        # url = settings.get_database_url(domain.value)

        configs[domain] = DatabaseConfig(
            domain=domain,
            url=url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=settings.debug,
            migration_path=str(Path(settings.registry_dir) / "migrations" / domain.value),
        )

    return configs