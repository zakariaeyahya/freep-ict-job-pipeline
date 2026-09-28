"""Verifies the Alembic setup itself (migrations/), not just the ORM
models: that `alembic upgrade head` builds the full schema from scratch on
an empty database, and that the current migration doesn't drift from the
SQLAlchemy models (CLAUDE.md: "Manage schema changes with Alembic
migrations committed to Git. Never hand-edit a production schema.").

Requires a reachable Postgres server (the same one docker-compose/README
already has running for the pipeline) since Alembic's autogenerate compare
and the migration's DDL (sequences, JSON columns) are Postgres-dialect
specific — SQLite would not exercise the same code path production runs
against. Skipped automatically if no server is reachable (e.g. in an
environment without Docker), rather than failing the whole suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from config.settings import DATABASE_URL
from src.freep_pipeline.storage.models import Base
from src.freep_pipeline.storage.scan_models import ScanError, ScanRoute, ScanRun  # noqa: F401

BACKEND_DIR = Path(__file__).resolve().parent.parent
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"

# Derived from the real DATABASE_URL by swapping the database name, so this
# test targets the same server/credentials without touching real data.
_BASE_URL, _, _REAL_DB_NAME = DATABASE_URL.rpartition("/")
SCRATCH_DB_URL = f"{_BASE_URL}/freep_pipeline_test_migrations"
ADMIN_DB_URL = DATABASE_URL  # used only to issue CREATE/DROP DATABASE


def _postgres_reachable() -> bool:
    try:
        create_engine(ADMIN_DB_URL).connect().close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_reachable(),
    reason="Postgres is not reachable — start it (see README.md) to run migration tests.",
)


@pytest.fixture()
def scratch_database():
    """Creates a throwaway Postgres database on the same server, and drops
    it afterwards — never touches the real freep_pipeline database."""
    admin_engine = create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    scratch_db_name = SCRATCH_DB_URL.rsplit("/", 1)[-1]

    with admin_engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{scratch_db_name}"'))
        conn.execute(text(f'CREATE DATABASE "{scratch_db_name}"'))

    try:
        yield SCRATCH_DB_URL
    finally:
        with admin_engine.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{scratch_db_name}"'))


def _alembic_config(database_url: str) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_upgrade_head_creates_every_table_on_a_fresh_database(scratch_database: str) -> None:
    """A clean checkout + fresh Postgres + `alembic upgrade head` must be
    enough to get a working schema — no manual ALTER TABLE, no relying on
    JobRepository.create_schema() in production."""
    from alembic import command

    command.upgrade(_alembic_config(scratch_database), "head")

    engine = create_engine(scratch_database)
    actual_tables = set(inspect(engine).get_table_names())
    expected_tables = set(Base.metadata.tables.keys()) | {"alembic_version"}

    assert expected_tables <= actual_tables, f"missing tables: {expected_tables - actual_tables}"


def test_upgrade_then_downgrade_leaves_no_pipeline_tables(scratch_database: str) -> None:
    """The initial migration's upgrade/downgrade must be symmetric — a
    downgrade actually undoes what upgrade created, not a stub."""
    from alembic import command

    config = _alembic_config(scratch_database)
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_engine(scratch_database)
    remaining_tables = set(inspect(engine).get_table_names()) - {"alembic_version"}

    assert remaining_tables == set(), f"downgrade left tables behind: {remaining_tables}"


def test_current_migration_matches_the_sqlalchemy_models(scratch_database: str) -> None:
    """Guards against the real failure mode this whole setup exists to
    prevent: someone adds/changes a column on JobCurrent/ScanRun without
    generating a migration. If this test fails, run
    `alembic revision --autogenerate` and commit the result."""
    from alembic import command

    command.upgrade(_alembic_config(scratch_database), "head")

    engine = create_engine(scratch_database)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diff = compare_metadata(context, Base.metadata)

    assert diff == [], f"migrations are out of sync with the models: {diff}"


def test_migrations_have_a_single_linear_head() -> None:
    """A second, unmerged migration head would mean two developers branched
    the schema independently — Alembic would then refuse to know which
    history is current. Catches that before it reaches Postgres."""
    config = _alembic_config(DATABASE_URL)
    script_dir = ScriptDirectory.from_config(config)

    heads = script_dir.get_heads()

    assert len(heads) == 1, f"expected exactly one migration head, found {len(heads)}: {heads}"
