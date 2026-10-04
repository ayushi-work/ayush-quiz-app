from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "adaptiveai.db")
if os.environ.get("VERCEL"):
    # Vercel serverless filesystem is read-only except /tmp (ephemeral per
    # instance — fine for a school demo; use Postgres via DATABASE_URL for persistence).
    DB_PATH = "/tmp/adaptiveai.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
# sqlite needs check_same_thread=False; postgres URL works without connect_args
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
