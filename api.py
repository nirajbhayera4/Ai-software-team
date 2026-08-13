import sys
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db import (
    create_project,
    create_user,
    get_project,
    get_run_with_outputs,
    get_user_by_id,
    get_user_by_username,
    initialize_database,
    list_project_runs,
    list_projects,
)
from orchestrator import run_project_workflow
from security import (
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class LoginRequest(BaseModel):
    username: str
    password: str


class ProjectRequest(BaseModel):
    name: str
    requirement: str


class GenerateRequest(BaseModel):
    requirement: str


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
            "developer_agent",
            "reviewer_agent",
            "tester_agent",
            "execution_sandbox",
            "database",
        ],
    }


@app.post("/auth/login")
def login(request: LoginRequest):
    user = get_user_by_username(request.username.strip())
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

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
    if not requirement:
        raise HTTPException(status_code=400, detail="Requirement must not be empty.")

    project_id = create_project(user["id"], name, requirement)
    project = get_project(project_id, user["id"])
    return {"project": project}


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
    run = get_run_with_outputs(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")

    project = get_project(run["project_id"], user["id"])
    if not project:
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
