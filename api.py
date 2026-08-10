import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from graph.workflow import graph


class GenerateRequest(BaseModel):
    requirement: str


app = FastAPI(
    title="AI Software Team API",
    description="Backend API for the React frontend to generate AI-driven project outputs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Software Team API is running."}


@app.post("/generate")
def generate_project(request: GenerateRequest):
    requirement = request.requirement.strip()
    if not requirement:
        raise HTTPException(status_code=400, detail="Requirement must not be empty.")

    initial_state = {
        "requirement": requirement,
        "tasks": "",
        "code": "",
        "review": "",
        "tests": "",
    }

    try:
        result = graph.invoke(initial_state)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    return result
