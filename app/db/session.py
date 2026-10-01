"""DB engine / session factory. URL + pool come from Settings (M4 tuning)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True,
                           connect_args={"check_same_thread": False})
else:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True,
                           pool_size=settings.DB_POOL_SIZE,
                           max_overflow=settings.DB_MAX_OVERFLOW,
                           pool_timeout=settings.DB_POOL_TIMEOUT)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
