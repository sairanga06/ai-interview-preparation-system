from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import psycopg
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
SQLITE_PATH = BASE_DIR / "interview.db"


def qident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def get_sqlite_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [row[0] for row in rows]


def get_postgres_tables(conn: psycopg.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
    ).fetchall()
    return [row[0] for row in rows]


def main() -> int:
    load_dotenv()

    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url.startswith(("postgresql://", "postgres://")):
        print("ERROR: DATABASE_URL is missing or invalid.")
        return 1

    if not SQLITE_PATH.exists():
        print(f"ERROR: {SQLITE_PATH} was not found.")
        return 1

    sqlite_conn = sqlite3.connect(
        f"file:{SQLITE_PATH.resolve().as_posix()}?mode=ro",
        uri=True,
    )

    try:
        pg_conn = psycopg.connect(
            database_url,
            connect_timeout=30,
        )

        try:
            sqlite_tables = get_sqlite_tables(sqlite_conn)
            pg_tables = get_postgres_tables(pg_conn)

            print()
            print("========================================")
            print("CareerCraft AI — Neon Migration Verify")
            print("========================================")
            print(f"SQLite tables : {len(sqlite_tables)}")
            print(f"Neon tables   : {len(pg_tables)}")
            print()

            if set(sqlite_tables) != set(pg_tables):
                print("TABLE CHECK: FAILED")
                print("Missing in Neon:", sorted(set(sqlite_tables) - set(pg_tables)))
                print("Extra in Neon:", sorted(set(pg_tables) - set(sqlite_tables)))
                return 1

            all_ok = True

            for table in sqlite_tables:
                sqlite_count = sqlite_conn.execute(
                    f"SELECT COUNT(*) FROM {qident(table)}"
                ).fetchone()[0]

                pg_count = pg_conn.execute(
                    f"SELECT COUNT(*) FROM {qident(table)}"
                ).fetchone()[0]

                status = "OK" if sqlite_count == pg_count else "MISMATCH"
                if status != "OK":
                    all_ok = False

                print(
                    f"{status:8} {table:38} "
                    f"SQLite={sqlite_count:<6} Neon={pg_count:<6}"
                )

            print()

            if all_ok:
                print("========================================")
                print("VERIFICATION PASSED")
                print("========================================")
                print("All SQLite tables and row counts match Neon.")
                print("No data was modified.")
                return 0

            print("========================================")
            print("VERIFICATION FAILED")
            print("========================================")
            print("At least one table has a different row count.")
            return 1

        finally:
            pg_conn.close()

    finally:
        sqlite_conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
