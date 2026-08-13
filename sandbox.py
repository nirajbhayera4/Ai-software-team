import os
import re
import subprocess
import tempfile
from pathlib import Path


CODE_BLOCK_PATTERN = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_python_code(generated_code):
    matches = CODE_BLOCK_PATTERN.findall(generated_code or "")
    if matches:
        return "\n\n".join(match.strip() for match in matches)
    return generated_code.strip()


def run_execution_sandbox(generated_code, test_plan):
    enabled = os.getenv("SANDBOX_ENABLED", "false").strip().lower() == "true"
    if not enabled:
        return {
            "status": "skipped",
            "summary": "Execution sandbox is disabled. Set SANDBOX_ENABLED=true to run generated code checks.",
            "logs": "",
        }

    code = extract_python_code(generated_code)
    if not code:
        return {
            "status": "skipped",
            "summary": "No generated Python code was available to check.",
            "logs": "",
        }

    with tempfile.TemporaryDirectory(prefix="ai-software-team-") as temp_dir:
        source_path = Path(temp_dir) / "generated_code.py"
        source_path.write_text(code, encoding="utf-8")

        command = ["python", "-m", "py_compile", str(source_path)]
        completed = subprocess.run(
            command,
            cwd=temp_dir,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )

    status = "passed" if completed.returncode == 0 else "failed"
    logs = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    summary = "Generated Python code compiled successfully." if status == "passed" else "Generated Python code failed compilation."
    return {
        "status": status,
        "summary": summary,
        "logs": logs,
        "test_plan_received": bool(test_plan),
    }
