import logging
from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings
from app.core.debug_store import push_debug_event

logger = logging.getLogger("data")

engine = create_engine(
    settings.database_url,
    echo=settings.sql_echo,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@event.listens_for(engine, "before_cursor_execute")
def log_sql_calls(conn, cursor, statement, parameters, context, executemany):
    if settings.app_debug:
        statement_preview = statement[:1500] if isinstance(statement, str) else str(statement)[:1500]
        parameters_preview = str(parameters)[:1000]
        logger.debug(
            "sql_execute",
            extra={
                "area": "dados",
                "statement": statement_preview,
                "parameters": parameters_preview,
            },
        )
        push_debug_event(
            source="dados",
            level="DEBUG",
            message="sql_execute",
            context={"statement": statement_preview, "parameters": parameters_preview},
        )


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
