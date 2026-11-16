"""Database Engine and Session Management with RLS Context Support."""
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from backend.app.core.config import settings

# Engine setup
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def set_rls_context(db: Session, user_id: str, role: str, region: str = ""):
    """Set PostgreSQL Row Level Security session variables if running on Postgres."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        try:
            db.execute(text("SET LOCAL app.user_id = :uid"), {"uid": user_id})
            db.execute(text("SET LOCAL app.role = :role"), {"role": role})
            db.execute(text("SET LOCAL app.region = :region"), {"region": region or ""})
        except Exception:
            pass
