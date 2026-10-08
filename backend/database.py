import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(Path(__file__).with_name(".env"))

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("NEON_DATABASE_URL")
    or os.getenv("SUPABASE_DB_URL")
    or ""
).strip()

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
elif DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

if not DATABASE_URL:
    db_host = os.getenv("DB_HOST", "").strip()
    if db_host:
        db_user = os.getenv("DB_USER", "").strip()
        db_name = os.getenv("DB_NAME", "").strip()
        if not db_user or not db_name:
            raise RuntimeError("DB_USER and DB_NAME are required when DB_HOST is configured.")
        DATABASE_URL = URL.create(
            "mysql+pymysql",
            username=db_user,
            password=os.getenv("DB_PASSWORD", ""),
            host=db_host,
            port=int(os.getenv("DB_PORT", "3306")),
            database=db_name,
        )
    else:
        if os.getenv("ENVIRONMENT", "development").strip().lower() in {"prod", "production"}:
            raise RuntimeError("DATABASE_URL or DB_HOST must be configured in production.")
        DATABASE_URL = "sqlite:///./surakshapath.db"
        print("[DB] No database URL or DB_HOST provided. Falling back to local SQLite database.")
elif "?" not in DATABASE_URL and DATABASE_URL.startswith("postgres"):
    DATABASE_URL = f"{DATABASE_URL}?sslmode=require"

engine_kwargs = {"pool_pre_ping": True, "pool_recycle": 300}
database_url_string = str(DATABASE_URL)
if database_url_string.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
elif database_url_string.startswith("mysql") and os.getenv("DB_SSL", "false").strip().lower() in {"1", "true", "yes"}:
    engine_kwargs["connect_args"] = {"ssl": {}}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
