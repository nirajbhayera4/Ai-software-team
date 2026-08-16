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
from sandbox import run_execution_sandbox


def run_task_workflow(project, task):
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
    }

    try:
        for agent_name, agent_function, output_key in [
            ("manager", manager, "tasks"),
            ("developer", developer, "implementation"),
            ("reviewer", reviewer, "review"),
            ("tester", tester, "test_plan"),
        ]:
            agent_run_id = create_agent_run(task["id"], agent_name, state)
            update = agent_function(state)
            state.update(update)
            update_agent_run(agent_run_id, "completed", state[output_key])
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
        sandbox_result = run_execution_sandbox(
            state["implementation"].get("code", ""),
            state["test_plan"],
            dependencies=state["implementation"].get("dependencies", []),
            test_code=state["implementation"].get("test_code", ""),
        )
        state["sandbox"] = sandbox_result
        update_agent_run(sandbox_run_id, sandbox_result["status"], sandbox_result)
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
        }
        final_status = "completed" if sandbox_result["status"] != "failed" else "failed"
        update_task_status(task["id"], final_status)
        update_project_status(project["id"], final_status)

        return {
            "task_id": task["id"],
            "status": final_status,
            **final_output,
        }
    except Exception as error:
        update_task_status(task["id"], "failed")
        update_project_status(project["id"], "failed")
        raise


def run_project_workflow(project):
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

    return {"run_id": run_id, **result}
