import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


DATABASE_PATH = Path("data/ai_software_team.db")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database():
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                requirement TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                requirement TEXT NOT NULL,
                final_output TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS agent_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                output TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );
            """
        )


def create_user(username, password_hash):
    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (username, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (username, password_hash, now),
        )
        return cursor.lastrowid


def get_user_by_username(username):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def create_project(owner_id, name, requirement):
    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO projects (owner_id, name, requirement, status, created_at, updated_at)
            VALUES (?, ?, ?, 'draft', ?, ?)
            """,
            (owner_id, name, requirement, now, now),
        )
        return cursor.lastrowid


def list_projects(owner_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT p.*,
                   (
                       SELECT status
                       FROM runs
                       WHERE project_id = p.id
                       ORDER BY id DESC
                       LIMIT 1
                   ) AS latest_run_status
            FROM projects p
            WHERE p.owner_id = ?
            ORDER BY p.updated_at DESC
            """,
            (owner_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_project(project_id, owner_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM projects WHERE id = ? AND owner_id = ?",
            (project_id, owner_id),
        ).fetchone()
        return dict(row) if row else None


def update_project_status(project_id, status):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE projects
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, utc_now(), project_id),
        )


def create_run(project_id, requirement):
    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO runs (project_id, status, requirement, created_at, updated_at)
            VALUES (?, 'running', ?, ?, ?)
            """,
            (project_id, requirement, now, now),
        )
        return cursor.lastrowid


def update_run(run_id, status, final_output=None, error=None):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE runs
            SET status = ?, final_output = ?, error = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                json.dumps(final_output) if isinstance(final_output, dict) else final_output,
                error,
                utc_now(),
                run_id,
            ),
        )


def save_agent_output(run_id, agent_name, output):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO agent_outputs (run_id, agent_name, output, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, agent_name, output, utc_now()),
        )


def list_project_runs(project_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM runs
            WHERE project_id = ?
            ORDER BY id DESC
            """,
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_run_with_outputs(run_id):
    with get_connection() as connection:
        run = connection.execute(
            "SELECT * FROM runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        if not run:
            return None

        outputs = connection.execute(
            """
            SELECT agent_name, output, created_at
            FROM agent_outputs
            WHERE run_id = ?
            ORDER BY id ASC
            """,
            (run_id,),
        ).fetchall()

        run_data = dict(run)
        if run_data.get("final_output"):
            run_data["final_output"] = json.loads(run_data["final_output"])
        run_data["agent_outputs"] = [dict(row) for row in outputs]
        return run_data
