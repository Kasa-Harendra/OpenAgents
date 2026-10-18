import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

OPENAGENTS_DIR = os.path.expanduser(os.environ.get("OPENAGENTS_DIR", "~/.openagents"))
os.makedirs(OPENAGENTS_DIR, exist_ok=True)

DATABASE_PATH = os.environ.get("OPENAGENTS_DB_PATH", os.path.join(OPENAGENTS_DIR, "openagents.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
