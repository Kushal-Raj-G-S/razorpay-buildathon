"""
Where the database actually lives. SQLite file on disk for the
hackathon build -- genuinely persistent, zero setup, and the exact same
SQLModel code would work against real Postgres later by changing one
line (DATABASE_URL), since SQLModel sits on top of SQLAlchemy.
"""
import os
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./warrant.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
