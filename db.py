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

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                requirement TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'todo',
                priority TEXT NOT NULL DEFAULT 'normal',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                input TEXT NOT NULL,
                output TEXT,
                error TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                agent_run_id INTEGER,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (agent_run_id) REFERENCES agent_runs(id)
            );

            CREATE TABLE IF NOT EXISTS file_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                agent_run_id INTEGER,
                path TEXT NOT NULL,
                purpose TEXT,
                change_summary TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (agent_run_id) REFERENCES agent_runs(id)
            );

            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                agent_run_id INTEGER,
                status TEXT NOT NULL,
                plan TEXT NOT NULL,
                logs TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (agent_run_id) REFERENCES agent_runs(id)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                agent_run_id INTEGER,
                rating INTEGER,
                approved INTEGER NOT NULL DEFAULT 0,
                findings TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (agent_run_id) REFERENCES agent_runs(id)
            );
            """
        )
        seed_agents(connection)


def seed_agents(connection):
    now = utc_now()
    agents = [
        ("manager", "Planning", "Breaks project requirements into actionable tasks."),
        ("developer", "Implementation", "Produces structured implementation output and file changes."),
        ("reviewer", "Review", "Reviews implementation quality, security, and completeness."),
        ("tester", "QA", "Creates categorized test plans and validation coverage."),
        ("execution_sandbox", "Execution", "Runs local validation checks for generated output."),
    ]
    connection.executemany(
        """
        INSERT OR IGNORE INTO agents (name, role, description, created_at)
        VALUES (?, ?, ?, ?)
        """,
        [(name, role, description, now) for name, role, description in agents],
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


def create_task(project_id, title, requirement, priority="normal"):
    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO tasks (project_id, title, requirement, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, 'todo', ?, ?, ?)
            """,
            (project_id, title, requirement, priority, now, now),
        )
        connection.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now, project_id),
        )
        return cursor.lastrowid


def list_projects(owner_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT p.*,
                   (
                       SELECT status
                       FROM tasks
                       WHERE project_id = p.id
                       ORDER BY id DESC
                       LIMIT 1
                   ) AS latest_task_status,
                   (
                       SELECT COUNT(*)
                       FROM tasks
                       WHERE project_id = p.id
                   ) AS task_count
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


def list_project_tasks(project_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT t.*,
                   (
                       SELECT status
                       FROM agent_runs
                       WHERE task_id = t.id
                       ORDER BY id DESC
                       LIMIT 1
                   ) AS latest_agent_run_status
            FROM tasks t
            WHERE t.project_id = ?
            ORDER BY t.updated_at DESC
            """,
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_task(task_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        return dict(row) if row else None


def update_task_status(task_id, status):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE tasks
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, utc_now(), task_id),
        )


def get_agent_by_name(name):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM agents WHERE name = ?",
            (name,),
        ).fetchone()
        return dict(row) if row else None


def create_agent_run(task_id, agent_name, input_payload):
    now = utc_now()
    agent = get_agent_by_name(agent_name)
    if not agent:
        raise ValueError(f"Unknown agent: {agent_name}")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO agent_runs (task_id, agent_id, status, input, started_at)
            VALUES (?, ?, 'running', ?, ?)
            """,
            (task_id, agent["id"], json.dumps(input_payload), now),
        )
        return cursor.lastrowid


def update_agent_run(agent_run_id, status, output=None, error=None):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE agent_runs
            SET status = ?, output = ?, error = ?, completed_at = ?
            WHERE id = ?
            """,
            (
                status,
                json.dumps(output) if isinstance(output, (dict, list)) else output,
                error,
                utc_now(),
                agent_run_id,
            ),
        )


def save_message(task_id, sender, content, agent_run_id=None):
    if isinstance(content, (dict, list)):
        content = json.dumps(content)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO messages (task_id, agent_run_id, sender, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, agent_run_id, sender, content, utc_now()),
        )


def save_file_changes(task_id, agent_run_id, file_changes):
    rows = []
    now = utc_now()
    for change in file_changes or []:
        if isinstance(change, str):
            rows.append((task_id, agent_run_id, change, "", "", now))
            continue

        rows.append(
            (
                task_id,
                agent_run_id,
                change.get("path", ""),
                change.get("purpose", ""),
                change.get("change_summary") or change.get("summary", ""),
                now,
            )
        )

    if not rows:
        return

    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO file_changes (task_id, agent_run_id, path, purpose, change_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def save_review(task_id, agent_run_id, review):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reviews (task_id, agent_run_id, rating, approved, findings, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                agent_run_id,
                review.get("overall_rating"),
                1 if review.get("approved") else 0,
                json.dumps(review),
                utc_now(),
            ),
        )


def save_test_run(task_id, agent_run_id, status, plan, logs=""):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO test_runs (task_id, agent_run_id, status, plan, logs, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                agent_run_id,
                status,
                json.dumps(plan) if isinstance(plan, (dict, list)) else plan,
                logs,
                utc_now(),
            ),
        )


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
    if isinstance(output, (dict, list)):
        output = json.dumps(output)

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


def _decode_json(value):
    if not value:
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


def get_task_workspace(task_id):
    with get_connection() as connection:
        task = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if not task:
            return None

        agent_runs = connection.execute(
            """
            SELECT ar.*, a.name AS agent_name, a.role AS agent_role
            FROM agent_runs ar
            JOIN agents a ON a.id = ar.agent_id
            WHERE ar.task_id = ?
            ORDER BY ar.id ASC
            """,
            (task_id,),
        ).fetchall()

        messages = connection.execute(
            """
            SELECT *
            FROM messages
            WHERE task_id = ?
            ORDER BY id ASC
            """,
            (task_id,),
        ).fetchall()

        file_changes = connection.execute(
            """
            SELECT *
            FROM file_changes
            WHERE task_id = ?
            ORDER BY id ASC
            """,
            (task_id,),
        ).fetchall()

        test_runs = connection.execute(
            """
            SELECT *
            FROM test_runs
            WHERE task_id = ?
            ORDER BY id ASC
            """,
            (task_id,),
        ).fetchall()

        reviews = connection.execute(
            """
            SELECT *
            FROM reviews
            WHERE task_id = ?
            ORDER BY id ASC
            """,
            (task_id,),
        ).fetchall()

    task_data = dict(task)

    decoded_agent_runs = []
    for row in agent_runs:
        item = dict(row)
        item["input"] = _decode_json(item.get("input"))
        item["output"] = _decode_json(item.get("output"))
        decoded_agent_runs.append(item)

    decoded_messages = []
    for row in messages:
        item = dict(row)
        item["content"] = _decode_json(item.get("content"))
        decoded_messages.append(item)

    decoded_test_runs = []
    for row in test_runs:
        item = dict(row)
        item["plan"] = _decode_json(item.get("plan"))
        decoded_test_runs.append(item)

    decoded_reviews = []
    for row in reviews:
        item = dict(row)
        item["approved"] = bool(item["approved"])
        item["findings"] = _decode_json(item.get("findings"))
        decoded_reviews.append(item)

    task_data["agent_runs"] = decoded_agent_runs
    task_data["messages"] = decoded_messages
    task_data["file_changes"] = [dict(row) for row in file_changes]
    task_data["test_runs"] = decoded_test_runs
    task_data["reviews"] = decoded_reviews
    return task_data


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
            try:
                run_data["final_output"] = json.loads(run_data["final_output"])
            except json.JSONDecodeError:
                pass
        agent_outputs = []
        for row in outputs:
            output = dict(row)
            try:
                output["output"] = json.loads(output["output"])
            except (TypeError, json.JSONDecodeError):
                pass
            agent_outputs.append(output)

        run_data["agent_outputs"] = agent_outputs
        return run_data
