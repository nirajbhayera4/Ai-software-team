import time

from agents.developer import developer
from agents.manager import manager
from agents.reviewer import reviewer
from agents.tester import tester
from db import (
    create_agent_run,
    create_run,
    create_task,
    save_file_changes,
    save_agent_output,
    save_message,
    save_review,
    save_test_run,
    update_agent_run,
    update_project_status,
    update_run,
    update_task_status,
)
from logging_config import get_logger
from sandbox import run_execution_sandbox


logger = get_logger(__name__)


def agent_fallback(agent_name, error):
    error_text = str(error)
    base = {
        "_fallback": True,
        "_error_type": "agent_failure",
        "_error": error_text,
    }
    if agent_name == "manager":
        return {
            **base,
            "summary": "Manager failed after retry handling. Using a minimal recovery task.",
            "tasks": [
                {
                    "id": "TASK-RECOVERY",
                    "title": "Recover from manager failure",
                    "area": "planning",
                    "description": "Review the original requirement manually because planning failed.",
                    "depends_on": [],
                    "acceptance_criteria": ["A human-readable recovery task is available."],
                }
            ],
        }
    if agent_name == "developer":
        return {
            **base,
            "task": "Developer failed after retry handling.",
            "files_changed": [],
            "changes": "No implementation was generated.",
            "code": "",
            "dependencies": [],
            "test_code": "",
            "tests_required": ["Retry the developer step after the upstream issue is fixed."],
            "assumptions": [],
        }
    if agent_name == "reviewer":
        return {
            **base,
            "overall_rating": 0,
            "approved": False,
            "strengths": [],
            "issues": [
                {
                    "severity": "high",
                    "file": "",
                    "description": "Reviewer failed after retry handling.",
                    "suggestion": "Treat the work as rejected until review can be rerun.",
                }
            ],
            "missing_functionality": [],
            "security_concerns": ["Review did not complete."],
            "suggestions": [],
        }
    if agent_name == "tester":
        return {
            **base,
            "functional": [],
            "unit": [],
            "integration": [],
            "edge_cases": [],
            "negative": ["Tester failed after retry handling."],
            "performance": [],
            "security": ["Testing did not complete."],
        }
    return base


def run_task_workflow(project, task):
    workflow_started = time.perf_counter()
    logger.info(
        "task workflow started",
        extra={
            "event": "task_workflow_started",
            "project_id": project["id"],
            "task_id": task["id"],
            "status": "running",
        },
    )
    update_project_status(project["id"], "running")
    update_task_status(task["id"], "running")
    save_message(task["id"], "user", task["requirement"])
    state = {
        "project": {
            "id": project["id"],
            "name": project["name"],
            "requirement": project["requirement"],
        },
        "task": {
            "id": task["id"],
            "title": task["title"],
            "requirement": task["requirement"],
        },
        "requirement": task["requirement"],
        "tasks": {},
        "implementation": {},
        "review": {},
        "test_plan": {},
        "sandbox": {},
        "workflow_errors": [],
    }

    try:
        for agent_name, agent_function, output_key in [
            ("manager", manager, "tasks"),
            ("developer", developer, "implementation"),
            ("reviewer", reviewer, "review"),
            ("tester", tester, "test_plan"),
        ]:
            agent_started = time.perf_counter()
            agent_run_id = create_agent_run(task["id"], agent_name, state)
            state["current_agent_run_id"] = agent_run_id
            logger.info(
                "agent started",
                extra={
                    "event": "agent_started",
                    "project_id": project["id"],
                    "task_id": task["id"],
                    "agent": agent_name,
                    "status": "running",
                },
            )
            try:
                update = agent_function(state)
                state.update(update)
            except Exception as error:
                duration_ms = int((time.perf_counter() - agent_started) * 1000)
                fallback = agent_fallback(agent_name, error)
                state[output_key] = fallback
                state["workflow_errors"].append(
                    {"agent": agent_name, "error_type": "agent_failure", "error": str(error)}
                )
                update_agent_run(agent_run_id, "failed", fallback, error=str(error))
                logger.exception(
                    "agent failed",
                    extra={
                        "event": "agent_failed",
                        "project_id": project["id"],
                        "task_id": task["id"],
                        "agent": agent_name,
                        "duration_ms": duration_ms,
                        "status": "failed",
                        "error": str(error),
                    },
                )
            else:
                output = state[output_key]
                if isinstance(output, dict) and output.get("_fallback"):
                    state["workflow_errors"].append(
                        {
                            "agent": agent_name,
                            "error_type": output.get("_error_type", "fallback"),
                            "error": output.get("_error", "Fallback output was used."),
                        }
                    )
                update_agent_run(agent_run_id, "completed", output)
                logger.info(
                    "agent completed",
                    extra={
                        "event": "agent_completed",
                        "project_id": project["id"],
                        "task_id": task["id"],
                        "agent": agent_name,
                        "duration_ms": int((time.perf_counter() - agent_started) * 1000),
                        "status": "completed",
                    },
                )
            save_message(task["id"], agent_name, state[output_key], agent_run_id)

            if agent_name == "developer":
                save_file_changes(
                    task["id"],
                    agent_run_id,
                    state["implementation"].get("files_changed", []),
                )
            elif agent_name == "reviewer":
                save_review(task["id"], agent_run_id, state["review"])
            elif agent_name == "tester":
                save_test_run(task["id"], agent_run_id, "planned", state["test_plan"])

        sandbox_run_id = create_agent_run(task["id"], "execution_sandbox", state)
        state["current_agent_run_id"] = sandbox_run_id
        sandbox_started = time.perf_counter()
        logger.info(
            "sandbox started",
            extra={
                "event": "sandbox_started",
                "project_id": project["id"],
                "task_id": task["id"],
                "agent": "execution_sandbox",
                "status": "running",
            },
        )
        try:
            sandbox_result = run_execution_sandbox(
                state["implementation"].get("code", ""),
                state["test_plan"],
                dependencies=state["implementation"].get("dependencies", []),
                test_code=state["implementation"].get("test_code", ""),
            )
        except Exception as error:
            sandbox_result = {
                "status": "failed",
                "summary": "Execution sandbox failed unexpectedly.",
                "logs": str(error),
                "isolation": "docker",
            }
            state["workflow_errors"].append(
                {"agent": "execution_sandbox", "error_type": "sandbox_failure", "error": str(error)}
            )
            logger.exception(
                "sandbox failed",
                extra={
                    "event": "sandbox_failed",
                    "project_id": project["id"],
                    "task_id": task["id"],
                    "agent": "execution_sandbox",
                    "duration_ms": int((time.perf_counter() - sandbox_started) * 1000),
                    "status": "failed",
                    "error": str(error),
                },
            )
        state["sandbox"] = sandbox_result
        update_agent_run(sandbox_run_id, sandbox_result["status"], sandbox_result)
        logger.info(
            "sandbox completed",
            extra={
                "event": "sandbox_completed",
                "project_id": project["id"],
                "task_id": task["id"],
                "agent": "execution_sandbox",
                "duration_ms": int((time.perf_counter() - sandbox_started) * 1000),
                "status": sandbox_result["status"],
            },
        )
        save_message(task["id"], "execution_sandbox", sandbox_result, sandbox_run_id)
        save_test_run(
            task["id"],
            sandbox_run_id,
            sandbox_result["status"],
            state["test_plan"],
            sandbox_result.get("logs", ""),
        )

        final_output = {
            "tasks": state["tasks"],
            "implementation": state["implementation"],
            "review": state["review"],
            "test_plan": state["test_plan"],
            "sandbox": sandbox_result,
            "workflow_errors": state["workflow_errors"],
        }
        reviewer_rejected = isinstance(state["review"], dict) and state["review"].get("approved") is False
        if reviewer_rejected:
            state["workflow_errors"].append(
                {
                    "agent": "reviewer",
                    "error_type": "reviewer_rejection",
                    "error": "Reviewer did not approve the implementation.",
                }
            )
            final_output["workflow_errors"] = state["workflow_errors"]
            logger.warning(
                "reviewer rejected implementation",
                extra={
                    "event": "reviewer_rejection",
                    "project_id": project["id"],
                    "task_id": task["id"],
                    "agent": "reviewer",
                    "status": "failed",
                },
            )

        final_status = "completed"
        if sandbox_result["status"] == "failed" or reviewer_rejected or state["workflow_errors"]:
            final_status = "failed"
        update_task_status(task["id"], final_status)
        update_project_status(project["id"], final_status)
        logger.info(
            "task workflow completed",
            extra={
                "event": "task_workflow_completed",
                "project_id": project["id"],
                "task_id": task["id"],
                "duration_ms": int((time.perf_counter() - workflow_started) * 1000),
                "status": final_status,
            },
        )

        return {
            "task_id": task["id"],
            "status": final_status,
            **final_output,
        }
    except Exception as error:
        update_task_status(task["id"], "failed")
        update_project_status(project["id"], "failed")
        logger.exception(
            "task workflow crashed",
            extra={
                "event": "task_workflow_crashed",
                "project_id": project["id"],
                "task_id": task["id"],
                "duration_ms": int((time.perf_counter() - workflow_started) * 1000),
                "status": "failed",
                "error": str(error),
            },
        )
        raise


def run_project_workflow(project):
    project_started = time.perf_counter()
    logger.info(
        "project workflow started",
        extra={
            "event": "project_workflow_started",
            "project_id": project["id"],
            "status": "running",
        },
    )
    task_id = create_task(
        project["id"],
        "Initial requirement",
        project["requirement"],
    )
    task = {
        "id": task_id,
        "project_id": project["id"],
        "title": "Initial requirement",
        "requirement": project["requirement"],
    }
    result = run_task_workflow(project, task)

    run_id = create_run(project["id"], project["requirement"])
    update_run(run_id, result["status"], final_output=result)
    for agent_name in ["manager", "developer", "reviewer", "tester", "execution_sandbox"]:
        key = {
            "manager": "tasks",
            "developer": "implementation",
            "reviewer": "review",
            "tester": "test_plan",
            "execution_sandbox": "sandbox",
        }[agent_name]
        save_agent_output(run_id, agent_name, result.get(key, {}))

    logger.info(
        "project workflow completed",
        extra={
            "event": "project_workflow_completed",
            "project_id": project["id"],
            "task_id": task_id,
            "run_id": run_id,
            "duration_ms": int((time.perf_counter() - project_started) * 1000),
            "status": result["status"],
        },
    )
    return {"run_id": run_id, **result}
