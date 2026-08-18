import sys
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db import (
    create_project,
    create_task,
    create_user,
    get_benchmark_run,
    get_project,
    get_task,
    get_run_with_outputs_for_owner,
    get_task_for_owner,
    get_task_workspace,
    get_user_by_id,
    get_user_by_username,
    initialize_database,
    list_benchmark_runs,
    list_project_runs,
    list_project_tasks,
    list_projects,
)
from evaluation import BENCHMARK_TASKS, benchmark_summary, run_benchmark
from logging_config import get_logger, reset_request_id, set_request_id
from orchestrator import run_project_workflow, run_task_workflow
from security import (
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


logger = get_logger(__name__)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class ProjectRequest(BaseModel):
    name: str
    requirement: str = ""


class TaskRequest(BaseModel):
    title: str
    requirement: str
    priority: str = "normal"


class GenerateRequest(BaseModel):
    requirement: str


class BenchmarkRunRequest(BaseModel):
    limit: int | None = None


app = FastAPI(
    title="AI Software Team API",
    description="Project API, agent orchestration, sandbox execution, and run persistence.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    token = set_request_id(request_id)
    started = time.perf_counter()
    logger.info(
        "request started",
        extra={
            "request_id": request_id,
            "event": "request_started",
            "method": request.method,
            "path": request.url.path,
        },
    )

    try:
        response = await call_next(request)
    except Exception as error:
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.exception(
            "request failed",
            extra={
                "request_id": request_id,
                "event": "request_failed",
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "status": "failed",
                "error": str(error),
            },
        )
        reset_request_id(token)
        raise

    duration_ms = int((time.perf_counter() - started) * 1000)
    response.headers["x-request-id"] = request_id
    logger.info(
        "request completed",
        extra={
            "request_id": request_id,
            "event": "request_completed",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "status": "completed" if response.status_code < 500 else "failed",
        },
    )
    reset_request_id(token)
    return response


@app.on_event("startup")
def startup():
    initialize_database()
    if not get_user_by_username(DEFAULT_ADMIN_USERNAME):
        create_user(DEFAULT_ADMIN_USERNAME, hash_password(DEFAULT_ADMIN_PASSWORD))


def current_user(authorization: str = Header(default="")):
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Missing authentication token.")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token.")

    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists.")
    return user


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "AI Software Team API is running.",
        "architecture": [
            "web_ui",
            "api_server",
            "agent_orchestrator",
            "tasks",
            "agent_runs",
            "agent_messages",
            "file_changes",
            "reviews",
            "test_runs",
            "developer_agent",
            "llm_calls",
            "reviewer_agent",
            "tester_agent",
            "execution_sandbox",
            "benchmark_evaluation",
            "database",
        ],
    }


@app.post("/auth/login")
def login(request: LoginRequest):
    user = get_user_by_username(request.username.strip())
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    return auth_response(user)


@app.post("/auth/register", status_code=201)
def register(request: RegisterRequest):
    username = request.username.strip()
    password = request.password
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if get_user_by_username(username):
        raise HTTPException(status_code=409, detail="Username is already taken.")

    user_id = create_user(username, hash_password(password))
    user = get_user_by_id(user_id)
    return auth_response(user)


@app.get("/auth/session")
def session(user=Depends(current_user)):
    return {"user": {"id": user["id"], "username": user["username"]}}


def auth_response(user):
    return {
        "access_token": create_access_token(user["id"], user["username"]),
        "token_type": "bearer",
        "user": {"id": user["id"], "username": user["username"]},
    }


@app.get("/projects")
def projects(user=Depends(current_user)):
    return {"projects": list_projects(user["id"])}


@app.post("/projects")
def create_new_project(request: ProjectRequest, user=Depends(current_user)):
    name = request.name.strip()
    requirement = request.requirement.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name must not be empty.")

    project_id = create_project(user["id"], name, requirement)
    if requirement:
        create_task(project_id, "Initial requirement", requirement)

    project = get_project(project_id, user["id"])
    return {"project": project}


@app.get("/projects/{project_id}/tasks")
def project_tasks(project_id: int, user=Depends(current_user)):
    project = get_project(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"tasks": list_project_tasks(project_id)}


@app.post("/projects/{project_id}/tasks")
def create_project_task(project_id: int, request: TaskRequest, user=Depends(current_user)):
    project = get_project(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    title = request.title.strip()
    requirement = request.requirement.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Task title must not be empty.")
    if not requirement:
        raise HTTPException(status_code=400, detail="Task requirement must not be empty.")

    task_id = create_task(project_id, title, requirement, request.priority.strip() or "normal")
    return {"task": get_task(task_id)}


@app.get("/tasks/{task_id}")
def task_detail(task_id: int, user=Depends(current_user)):
    task = get_task_for_owner(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    return {"task": get_task_workspace(task_id)}


@app.post("/tasks/{task_id}/runs")
def run_task(task_id: int, user=Depends(current_user)):
    task = get_task_for_owner(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    project = get_project(task["project_id"], user["id"])

    try:
        result = run_task_workflow(project, task)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    return result


@app.post("/projects/{project_id}/runs")
def run_project(project_id: int, user=Depends(current_user)):
    project = get_project(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    try:
        result = run_project_workflow(project)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    return result


@app.get("/projects/{project_id}/runs")
def project_runs(project_id: int, user=Depends(current_user)):
    project = get_project(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"runs": list_project_runs(project_id)}


@app.get("/runs/{run_id}")
def run_detail(run_id: int, user=Depends(current_user)):
    run = get_run_with_outputs_for_owner(run_id, user["id"])
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    return {"run": run}


@app.post("/generate")
def generate_project(request: GenerateRequest, user=Depends(current_user)):
    requirement = request.requirement.strip()
    if not requirement:
        raise HTTPException(status_code=400, detail="Requirement must not be empty.")

    project_id = create_project(user["id"], "Untitled project", requirement)
    project = get_project(project_id, user["id"])
    return run_project_workflow(project)


@app.get("/benchmarks/tasks")
def benchmark_tasks(user=Depends(current_user)):
    return {"tasks": BENCHMARK_TASKS}


@app.get("/benchmarks")
def benchmarks(user=Depends(current_user)):
    return {"benchmarks": list_benchmark_runs(user["id"])}


@app.post("/benchmarks/runs")
def create_benchmark(request: BenchmarkRunRequest, user=Depends(current_user)):
    limit = request.limit
    if limit is not None and limit < 1:
        raise HTTPException(status_code=400, detail="Benchmark limit must be at least 1.")
    if limit is not None and limit > len(BENCHMARK_TASKS):
        raise HTTPException(status_code=400, detail=f"Benchmark limit must be {len(BENCHMARK_TASKS)} or fewer.")

    benchmark_run = run_benchmark(user["id"], limit=limit)
    return {
        "benchmark": benchmark_run,
        "summary": benchmark_summary(benchmark_run),
    }


@app.get("/benchmarks/runs/{benchmark_run_id}")
def benchmark_detail(benchmark_run_id: int, user=Depends(current_user)):
    benchmark_run = get_benchmark_run(benchmark_run_id, user["id"])
    if not benchmark_run:
        raise HTTPException(status_code=404, detail="Benchmark run not found.")
    return {
        "benchmark": benchmark_run,
        "summary": benchmark_summary(benchmark_run),
    }
