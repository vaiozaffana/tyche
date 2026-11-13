from sqlalchemy import Engine
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def create_engine(url: str) -> Engine:
    options = {"check_same_thread": False} if url.startswith("sqlite") else {}
    if url in {"sqlite://", "sqlite:///:memory:"}:
        return sqlalchemy_create_engine(
            url,
            pool_pre_ping=True,
            connect_args=options,
            poolclass=StaticPool,
        )
    return sqlalchemy_create_engine(
        normalize_database_url(url),
        pool_pre_ping=True,
        connect_args=options,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
