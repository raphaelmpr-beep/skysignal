import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

_raw_url = os.getenv("DATABASE_URL", "postgresql://skysignal:skysignal@db:5432/skysignal").strip()

# Supabase pooler URLs use port 6543 with pgbouncer in transaction mode,
# which is incompatible with SQLAlchemy's default connection args.
# Direct connections use port 5432 and work fine.
# If the URL contains port 6543 (Supabase pooler), add sslmode and no-prepare.
_connect_args: dict = {}
_engine_kwargs: dict = {"pool_pre_ping": True}

if "6543" in _raw_url:
    # Supabase session pooler — disable prepared statements
    _connect_args = {"sslmode": "require"}
    _engine_kwargs.update({"connect_args": _connect_args})
elif "supabase" in _raw_url and "5432" in _raw_url:
    # Supabase direct — require SSL
    _connect_args = {"sslmode": "require"}
    _engine_kwargs.update({"connect_args": _connect_args})

DATABASE_URL = _raw_url

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
