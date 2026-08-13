from agents.developer import developer
from agents.manager import manager
from agents.reviewer import reviewer
from agents.tester import tester
from db import (
    create_run,
    save_agent_output,
    update_project_status,
    update_run,
)
from sandbox import run_execution_sandbox


def run_project_workflow(project):
    run_id = create_run(project["id"], project["requirement"])
    update_project_status(project["id"], "running")

    state = {
        "requirement": project["requirement"],
        "tasks": "",
        "code": "",
        "review": "",
        "tests": "",
        "sandbox": "",
    }

    try:
        for agent_name, agent_function, output_key in [
            ("manager", manager, "tasks"),
            ("developer", developer, "code"),
            ("reviewer", reviewer, "review"),
            ("tester", tester, "tests"),
        ]:
            update = agent_function(state)
            state.update(update)
            save_agent_output(run_id, agent_name, state[output_key])

        sandbox_result = run_execution_sandbox(state["code"], state["tests"])
        state["sandbox"] = sandbox_result
        save_agent_output(run_id, "execution_sandbox", sandbox_result["summary"])

        final_output = {
            "tasks": state["tasks"],
            "code": state["code"],
            "review": state["review"],
            "tests": state["tests"],
            "sandbox": sandbox_result,
        }
        final_status = "completed" if sandbox_result["status"] != "failed" else "failed"
        update_run(run_id, final_status, final_output=final_output)
        update_project_status(project["id"], final_status)

        return {
            "run_id": run_id,
            "status": final_status,
            **final_output,
        }
    except Exception as error:
        update_run(run_id, "failed", error=str(error))
        update_project_status(project["id"], "failed")
        raise
