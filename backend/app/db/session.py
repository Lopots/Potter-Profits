from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app import models  # noqa: F401


local_connect_args = {"check_same_thread": False} if settings.local_database_url.startswith("sqlite") else {}
remote_connect_args = {"check_same_thread": False} if settings.remote_database_url.startswith("sqlite") else {}

engine = create_engine(settings.local_database_url, future=True, connect_args=local_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

remote_engine = None
RemoteSessionLocal = None
if settings.remote_database_url:
    remote_engine = create_engine(settings.remote_database_url, future=True, connect_args=remote_connect_args)
    RemoteSessionLocal = sessionmaker(bind=remote_engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_remote_db() -> Generator[Session | None, None, None]:
    if RemoteSessionLocal is None:
        yield None
        return

    db = RemoteSessionLocal()
    try:
        yield db
    finally:
        db.close()
