import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


DEFAULT_SQLITE_PATH = Path("data/ai_software_team.db")


def normalize_database_url(url):
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"))


def utc_now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    projects: Mapped[list["Project"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    owner: Mapped["User"] = relationship(back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    runs: Mapped[list["Run"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="todo")
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="normal")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    agent_messages: Mapped[list["AgentMessage"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    file_changes: Mapped[list["FileChange"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    test_runs: Mapped[list["TestRun"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    runs: Mapped[list["AgentRun"]] = relationship(back_populates="agent")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    input: Mapped[dict] = mapped_column("input", JSON, nullable=False)
    output: Mapped[dict | list | str | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    task: Mapped["Task"] = relationship(back_populates="agent_runs")
    agent: Mapped["Agent"] = relationship(back_populates="runs")
    messages: Mapped[list["AgentMessage"]] = relationship(back_populates="agent_run")
    file_changes: Mapped[list["FileChange"]] = relationship(back_populates="agent_run")
    test_runs: Mapped[list["TestRun"]] = relationship(back_populates="agent_run")
    reviews: Mapped[list["Review"]] = relationship(back_populates="agent_run")
    llm_calls: Mapped[list["LlmCall"]] = relationship(back_populates="agent_run", cascade="all, delete-orphan")


class LlmCall(Base):
    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), index=True)
    agent_run_id: Mapped[int | None] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(150), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    agent_run: Mapped["AgentRun"] = relationship(back_populates="llm_calls")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    agent_run_id: Mapped[int | None] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    sender: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[dict | list | str] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="agent_messages")
    agent_run: Mapped["AgentRun"] = relationship(back_populates="messages")


class FileChange(Base):
    __tablename__ = "file_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    agent_run_id: Mapped[int | None] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text)
    change_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="file_changes")
    agent_run: Mapped["AgentRun"] = relationship(back_populates="file_changes")


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    agent_run_id: Mapped[int | None] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    plan: Mapped[dict | list | str] = mapped_column(JSON, nullable=False)
    logs: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="test_runs")
    agent_run: Mapped["AgentRun"] = relationship(back_populates="test_runs")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    agent_run_id: Mapped[int | None] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    rating: Mapped[int | None] = mapped_column(Integer)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    findings: Mapped[dict | list | str] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="reviews")
    agent_run: Mapped["AgentRun"] = relationship(back_populates="reviews")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    final_output: Mapped[dict | list | str | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="runs")
    agent_outputs: Mapped[list["AgentOutput"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class AgentOutput(Base):
    __tablename__ = "agent_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    output: Mapped[dict | list | str] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    run: Mapped["Run"] = relationship(back_populates="agent_outputs")


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")
    total_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tests_passing_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reviewer_approval_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_iterations: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_correctness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    results: Mapped[list["BenchmarkResult"]] = relationship(back_populates="benchmark_run", cascade="all, delete-orphan")


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benchmark_run_id: Mapped[int] = mapped_column(ForeignKey("benchmark_runs.id"), nullable=False, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    correctness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tests_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reviewer_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    iterations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    benchmark_run: Mapped["BenchmarkRun"] = relationship(back_populates="results")


def _engine_kwargs():
    if DATABASE_URL.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


if DATABASE_URL.startswith("sqlite:///"):
    Path(DATABASE_URL.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, future=True, **_engine_kwargs())
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _as_dict(model):
    if not model:
        return None
    data = {}
    for column in model.__table__.columns:
        value = getattr(model, column.key)
        if isinstance(value, datetime):
            value = value.isoformat()
        data[column.key] = value
    return data


def _duration_ms(started_at, completed_at):
    if not started_at or not completed_at:
        return None
    return int((completed_at - started_at).total_seconds() * 1000)


def _decode_json(value):
    if not value:
        return value
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


def initialize_database():
    Base.metadata.create_all(bind=engine)
    with get_session() as session:
        seed_agents(session)


def seed_agents(session):
    now = utc_now()
    agents = [
        ("manager", "Planning", "Breaks project requirements into actionable tasks."),
        ("developer", "Implementation", "Produces structured implementation output and file changes."),
        ("reviewer", "Review", "Reviews implementation quality, security, and completeness."),
        ("tester", "QA", "Creates categorized test plans and validation coverage."),
        ("execution_sandbox", "Execution", "Runs local validation checks for generated output."),
    ]
    existing = set(session.scalars(select(Agent.name)).all())
    for name, role, description in agents:
        if name not in existing:
            session.add(Agent(name=name, role=role, description=description, created_at=now))


def create_user(username, password_hash):
    with get_session() as session:
        user = User(username=username, password_hash=password_hash)
        session.add(user)
        session.flush()
        return user.id


def get_user_by_username(username):
    with get_session() as session:
        return _as_dict(session.scalar(select(User).where(User.username == username)))


def get_user_by_id(user_id):
    with get_session() as session:
        return _as_dict(session.get(User, user_id))


def create_project(owner_id, name, requirement):
    with get_session() as session:
        project = Project(owner_id=owner_id, name=name, requirement=requirement)
        session.add(project)
        session.flush()
        return project.id


def create_task(project_id, title, requirement, priority="normal"):
    now = utc_now()
    with get_session() as session:
        task = Task(project_id=project_id, title=title, requirement=requirement, priority=priority, created_at=now, updated_at=now)
        session.add(task)
        project = session.get(Project, project_id)
        if project:
            project.updated_at = now
        session.flush()
        return task.id


def list_projects(owner_id):
    latest_task_status = (
        select(Task.status)
        .where(Task.project_id == Project.id)
        .order_by(Task.id.desc())
        .limit(1)
        .scalar_subquery()
    )
    task_count = (
        select(func.count(Task.id))
        .where(Task.project_id == Project.id)
        .scalar_subquery()
    )
    with get_session() as session:
        rows = session.execute(
            select(Project, latest_task_status.label("latest_task_status"), task_count.label("task_count"))
            .where(Project.owner_id == owner_id)
            .order_by(Project.updated_at.desc())
        ).all()
        projects = []
        for project, latest_status, count in rows:
            item = _as_dict(project)
            item["latest_task_status"] = latest_status
            item["task_count"] = count
            projects.append(item)
        return projects


def get_project(project_id, owner_id):
    with get_session() as session:
        project = session.scalar(select(Project).where(Project.id == project_id, Project.owner_id == owner_id))
        return _as_dict(project)


def list_project_tasks(project_id):
    latest_agent_run_status = (
        select(AgentRun.status)
        .where(AgentRun.task_id == Task.id)
        .order_by(AgentRun.id.desc())
        .limit(1)
        .scalar_subquery()
    )
    with get_session() as session:
        rows = session.execute(
            select(Task, latest_agent_run_status.label("latest_agent_run_status"))
            .where(Task.project_id == project_id)
            .order_by(Task.updated_at.desc())
        ).all()
        tasks = []
        for task, latest_status in rows:
            item = _as_dict(task)
            item["latest_agent_run_status"] = latest_status
            tasks.append(item)
        return tasks


def get_task(task_id):
    with get_session() as session:
        return _as_dict(session.get(Task, task_id))


def get_task_for_owner(task_id, owner_id):
    with get_session() as session:
        task = session.scalar(
            select(Task)
            .join(Project, Project.id == Task.project_id)
            .where(Task.id == task_id, Project.owner_id == owner_id)
        )
        return _as_dict(task)


def update_task_status(task_id, status):
    with get_session() as session:
        task = session.get(Task, task_id)
        if task:
            task.status = status
            task.updated_at = utc_now()


def get_agent_by_name(name):
    with get_session() as session:
        return _as_dict(session.scalar(select(Agent).where(Agent.name == name)))


def create_agent_run(task_id, agent_name, input_payload):
    now = utc_now()
    with get_session() as session:
        agent = session.scalar(select(Agent).where(Agent.name == agent_name))
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent_run = AgentRun(
            task_id=task_id,
            agent_id=agent.id,
            status="running",
            input=input_payload,
            started_at=now,
        )
        session.add(agent_run)
        session.flush()
        return agent_run.id


def update_agent_run(agent_run_id, status, output=None, error=None):
    with get_session() as session:
        agent_run = session.get(AgentRun, agent_run_id)
        if agent_run:
            agent_run.status = status
            agent_run.output = output
            agent_run.error = error
            agent_run.completed_at = utc_now()


def save_llm_call(
    agent_name,
    model,
    input_tokens=0,
    output_tokens=0,
    latency_ms=0,
    cost_usd=0.0,
    status="completed",
    error=None,
    task_id=None,
    agent_run_id=None,
):
    with get_session() as session:
        session.add(
            LlmCall(
                task_id=task_id,
                agent_run_id=agent_run_id,
                agent_name=agent_name,
                model=model,
                input_tokens=input_tokens or 0,
                output_tokens=output_tokens or 0,
                latency_ms=latency_ms or 0,
                cost_usd=cost_usd or 0.0,
                status=status,
                error=error,
            )
        )


def save_message(task_id, sender, content, agent_run_id=None):
    with get_session() as session:
        session.add(
            AgentMessage(
                task_id=task_id,
                agent_run_id=agent_run_id,
                sender=sender,
                content=content,
            )
        )


def save_file_changes(task_id, agent_run_id, file_changes):
    rows = []
    for change in file_changes or []:
        if isinstance(change, str):
            rows.append(FileChange(task_id=task_id, agent_run_id=agent_run_id, path=change, purpose="", change_summary=""))
            continue

        rows.append(
            FileChange(
                task_id=task_id,
                agent_run_id=agent_run_id,
                path=change.get("path", ""),
                purpose=change.get("purpose", ""),
                change_summary=change.get("change_summary") or change.get("summary", ""),
            )
        )

    if not rows:
        return

    with get_session() as session:
        session.add_all(rows)


def save_review(task_id, agent_run_id, review):
    with get_session() as session:
        session.add(
            Review(
                task_id=task_id,
                agent_run_id=agent_run_id,
                rating=review.get("overall_rating"),
                approved=bool(review.get("approved")),
                findings=review,
            )
        )


def save_test_run(task_id, agent_run_id, status, plan, logs=""):
    with get_session() as session:
        session.add(
            TestRun(
                task_id=task_id,
                agent_run_id=agent_run_id,
                status=status,
                plan=plan,
                logs=logs,
            )
        )


def update_project_status(project_id, status):
    with get_session() as session:
        project = session.get(Project, project_id)
        if project:
            project.status = status
            project.updated_at = utc_now()


def create_run(project_id, requirement):
    now = utc_now()
    with get_session() as session:
        run = Run(project_id=project_id, status="running", requirement=requirement, created_at=now, updated_at=now)
        session.add(run)
        session.flush()
        return run.id


def update_run(run_id, status, final_output=None, error=None):
    with get_session() as session:
        run = session.get(Run, run_id)
        if run:
            run.status = status
            run.final_output = final_output
            run.error = error
            run.updated_at = utc_now()


def save_agent_output(run_id, agent_name, output):
    with get_session() as session:
        session.add(AgentOutput(run_id=run_id, agent_name=agent_name, output=output))


def create_benchmark_run(owner_id, total_tasks):
    with get_session() as session:
        benchmark_run = BenchmarkRun(owner_id=owner_id, total_tasks=total_tasks, status="running")
        session.add(benchmark_run)
        session.flush()
        return benchmark_run.id


def save_benchmark_result(
    benchmark_run_id,
    name,
    requirement,
    status,
    correctness_score=0.0,
    tests_passed=False,
    reviewer_approved=False,
    iterations=0,
    latency_ms=0,
    cost_usd=0.0,
    error=None,
    metrics=None,
    project_id=None,
    task_id=None,
):
    with get_session() as session:
        session.add(
            BenchmarkResult(
                benchmark_run_id=benchmark_run_id,
                project_id=project_id,
                task_id=task_id,
                name=name,
                requirement=requirement,
                status=status,
                correctness_score=correctness_score or 0.0,
                tests_passed=bool(tests_passed),
                reviewer_approved=bool(reviewer_approved),
                iterations=iterations or 0,
                latency_ms=latency_ms or 0,
                cost_usd=cost_usd or 0.0,
                error=error,
                metrics=metrics or {},
            )
        )


def complete_benchmark_run(benchmark_run_id, status="completed"):
    with get_session() as session:
        benchmark_run = session.get(BenchmarkRun, benchmark_run_id)
        if not benchmark_run:
            return None

        results = session.scalars(
            select(BenchmarkResult).where(BenchmarkResult.benchmark_run_id == benchmark_run_id)
        ).all()
        total = len(results)
        completed = [result for result in results if result.status == "completed"]

        benchmark_run.status = status
        benchmark_run.completed_tasks = len(completed)
        benchmark_run.completed_at = utc_now()
        if total:
            benchmark_run.tests_passing_rate = sum(1 for result in results if result.tests_passed) / total
            benchmark_run.reviewer_approval_rate = sum(1 for result in results if result.reviewer_approved) / total
            benchmark_run.average_iterations = sum(result.iterations for result in results) / total
            benchmark_run.average_latency_ms = sum(result.latency_ms for result in results) / total
            benchmark_run.average_cost_usd = sum(result.cost_usd for result in results) / total
            benchmark_run.average_correctness_score = sum(result.correctness_score for result in results) / total

        session.flush()
        return _as_dict(benchmark_run)


def _benchmark_with_results(benchmark_run, results):
    data = _as_dict(benchmark_run)
    data["results"] = [_as_dict(result) for result in results]
    return data


def list_benchmark_runs(owner_id):
    with get_session() as session:
        benchmark_runs = session.scalars(
            select(BenchmarkRun)
            .where(BenchmarkRun.owner_id == owner_id)
            .order_by(BenchmarkRun.id.desc())
        ).all()
        return [_as_dict(benchmark_run) for benchmark_run in benchmark_runs]


def get_benchmark_run(benchmark_run_id, owner_id):
    with get_session() as session:
        benchmark_run = session.scalar(
            select(BenchmarkRun).where(
                BenchmarkRun.id == benchmark_run_id,
                BenchmarkRun.owner_id == owner_id,
            )
        )
        if not benchmark_run:
            return None
        results = session.scalars(
            select(BenchmarkResult)
            .where(BenchmarkResult.benchmark_run_id == benchmark_run_id)
            .order_by(BenchmarkResult.id.asc())
        ).all()
        return _benchmark_with_results(benchmark_run, results)


def list_project_runs(project_id):
    with get_session() as session:
        runs = session.scalars(select(Run).where(Run.project_id == project_id).order_by(Run.id.desc())).all()
        return [_as_dict(run) for run in runs]


def get_task_workspace(task_id):
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return None

        agent_runs = session.execute(
            select(AgentRun, Agent.name.label("agent_name"), Agent.role.label("agent_role"))
            .join(Agent, Agent.id == AgentRun.agent_id)
            .where(AgentRun.task_id == task_id)
            .order_by(AgentRun.id.asc())
        ).all()
        messages = session.scalars(
            select(AgentMessage).where(AgentMessage.task_id == task_id).order_by(AgentMessage.id.asc())
        ).all()
        file_changes = session.scalars(
            select(FileChange).where(FileChange.task_id == task_id).order_by(FileChange.id.asc())
        ).all()
        test_runs = session.scalars(
            select(TestRun).where(TestRun.task_id == task_id).order_by(TestRun.id.asc())
        ).all()
        reviews = session.scalars(
            select(Review).where(Review.task_id == task_id).order_by(Review.id.asc())
        ).all()
        llm_calls = session.scalars(
            select(LlmCall).where(LlmCall.task_id == task_id).order_by(LlmCall.id.asc())
        ).all()

        task_data = _as_dict(task)
        decoded_agent_runs = []
        for agent_run, agent_name, agent_role in agent_runs:
            item = _as_dict(agent_run)
            item["agent_name"] = agent_name
            item["agent_role"] = agent_role
            item["input"] = _decode_json(item.get("input"))
            item["output"] = _decode_json(item.get("output"))
            item["duration_ms"] = _duration_ms(agent_run.started_at, agent_run.completed_at)
            decoded_agent_runs.append(item)

        decoded_messages = []
        for message in messages:
            item = _as_dict(message)
            item["content"] = _decode_json(item.get("content"))
            decoded_messages.append(item)

        decoded_test_runs = []
        for test_run in test_runs:
            item = _as_dict(test_run)
            item["plan"] = _decode_json(item.get("plan"))
            decoded_test_runs.append(item)

        decoded_reviews = []
        for review in reviews:
            item = _as_dict(review)
            item["findings"] = _decode_json(item.get("findings"))
            decoded_reviews.append(item)

        task_data["agent_runs"] = decoded_agent_runs
        task_data["llm_calls"] = [_as_dict(call) for call in llm_calls]
        task_data["total_duration_ms"] = sum(
            item["duration_ms"] or 0 for item in decoded_agent_runs
        )
        task_data["messages"] = decoded_messages
        task_data["file_changes"] = [_as_dict(change) for change in file_changes]
        task_data["test_runs"] = decoded_test_runs
        task_data["reviews"] = decoded_reviews
        return task_data


def get_run_with_outputs(run_id):
    with get_session() as session:
        run = session.get(Run, run_id)
        if not run:
            return None

        outputs = session.scalars(
            select(AgentOutput).where(AgentOutput.run_id == run_id).order_by(AgentOutput.id.asc())
        ).all()
        run_data = _as_dict(run)
        run_data["final_output"] = _decode_json(run_data.get("final_output"))
        run_data["agent_outputs"] = []
        for output in outputs:
            item = _as_dict(output)
            item["output"] = _decode_json(item.get("output"))
            run_data["agent_outputs"].append(item)
        return run_data


def get_run_with_outputs_for_owner(run_id, owner_id):
    with get_session() as session:
        run_id_for_owner = session.scalar(
            select(Run.id)
            .join(Project, Project.id == Run.project_id)
            .where(Run.id == run_id, Project.owner_id == owner_id)
        )
    if not run_id_for_owner:
        return None
    return get_run_with_outputs(run_id)
