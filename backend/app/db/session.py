"""
Where the database actually lives. SQLite file on disk for the
hackathon build -- genuinely persistent, zero setup, and the exact same
SQLModel code would work against real Postgres later by changing one
line (DATABASE_URL), since SQLModel sits on top of SQLAlchemy.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlmodel import SQLModel, Session, create_engine

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./warrant.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def init_db():
    SQLModel.metadata.create_all(engine)
    _migrate_add_missing_columns()


# create_all() only creates missing TABLES -- it never alters a table
# that already exists on disk, even if the model gained a new column
# since that table was first created. allow_categories was added to
# Policy/PolicyRow after real merchants (shop_123 included) already had
# rows in a `policies` table without it; without this, every read of an
# existing policy would fail with "no such column" the moment the model
# expects it. Each statement is its own try/except, not one transaction,
# so one already-applied column doesn't block another that genuinely is
# missing -- and it's safe to call on every startup, not just once.
_COLUMN_MIGRATIONS = [
    ("policies", "allow_categories", "JSON DEFAULT '[]'"),
]


def _migrate_add_missing_columns():
    with engine.connect() as conn:
        for table, column, coltype in _COLUMN_MIGRATIONS:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"))
                conn.commit()
            except (OperationalError, ProgrammingError):
                conn.rollback()  # column already exists -- fine, not an error


def get_session():
    with Session(engine) as session:
        yield session
