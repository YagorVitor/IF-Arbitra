from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings().database_url,
    pool_size=settings().pool_size,
    max_overflow=settings().pool_overflow,
    pool_timeout=15,
    pool_pre_ping=True,
    connect_args={"options": "-c timezone=UTC -c lock_timeout=10000 -c statement_timeout=30000"},
)
SessionFactory = sessionmaker(engine, expire_on_commit=False)


def database_now(db: Session):
    # transaction_timestamp() predates any lock wait; the decision must use the actual clock.
    return db.scalar(text("SELECT clock_timestamp()"))
