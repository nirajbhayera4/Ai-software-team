import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from logging_config import get_logger


CODE_BLOCK_PATTERN = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
FILE_MARKER_PATTERN = re.compile(r"^=+\s*\n(.+?\.py)\s*\n=+\s*$", re.MULTILINE)
logger = get_logger(__name__)


def extract_python_code(generated_code):
    text = (generated_code or "").strip()
    matches = CODE_BLOCK_PATTERN.findall(text)
    if matches:
        return "\n\n".join(match.strip() for match in matches)
    return text


def _as_list(value):
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.splitlines() if item.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _as_code(value):
    if not value:
        return ""
    if isinstance(value, str):
        return extract_python_code(value)
    return ""


def _write_generated_files(workspace, code):
    parts = FILE_MARKER_PATTERN.split(code)
    if len(parts) < 3:
        (workspace / "generated_code.py").write_text(code, encoding="utf-8")
        return ["generated_code.py"]

    written = []
    prefix = parts[0].strip()
    if prefix:
        (workspace / "generated_code.py").write_text(prefix, encoding="utf-8")
        written.append("generated_code.py")

    for index in range(1, len(parts), 2):
        relative_name = parts[index].strip()
        file_code = parts[index + 1].strip()
        target = (workspace / relative_name).resolve()
        if workspace.resolve() not in target.parents and target != workspace.resolve():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file_code, encoding="utf-8")
        written.append(relative_name)

    if not written:
        (workspace / "generated_code.py").write_text(code, encoding="utf-8")
        return ["generated_code.py"]
    return written


def _docker_available():
    if not shutil.which("docker"):
        return False
    try:
        completed = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def _docker_command(workspace, files, has_requirements, has_tests):
    image = os.getenv("SANDBOX_DOCKER_IMAGE", "python:3.12-slim")
    timeout_seconds = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "30"))
    memory = os.getenv("SANDBOX_MEMORY", "256m")
    cpus = os.getenv("SANDBOX_CPUS", "1")
    pids_limit = os.getenv("SANDBOX_PIDS_LIMIT", "128")
    allow_network = os.getenv("SANDBOX_ALLOW_NETWORK", "false").strip().lower() == "true"
    network = "bridge" if allow_network else "none"

    compile_commands = " && ".join(f"python -m py_compile {shlex.quote(name)}" for name in files)
    install_command = ""
    if has_requirements:
        install_command = (
            "python -m pip install --disable-pip-version-check --no-cache-dir "
            "--target /tmp/deps -r requirements.txt && "
        )
    test_command = " && python test_generated.py" if has_tests else ""
    script = (
        "set -eu; "
        f"{install_command}"
        "export PYTHONPATH=/tmp/deps; "
        f"{compile_commands}"
        f"{test_command}"
    )

    return [
        "docker",
        "run",
        "--rm",
        "--network",
        network,
        "--cpus",
        cpus,
        "--memory",
        memory,
        "--pids-limit",
        pids_limit,
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--tmpfs",
        "/tmp:rw,exec,nosuid,size=128m",
        "--user",
        "65534:65534",
        "-v",
        f"{workspace}:/workspace:ro",
        "-w",
        "/workspace",
        image,
        "sh",
        "-c",
        script,
    ], timeout_seconds


def run_execution_sandbox(generated_code, test_plan, dependencies=None, test_code=None):
    started = time.perf_counter()
    enabled = os.getenv("SANDBOX_ENABLED", "false").strip().lower() == "true"
    if not enabled:
        logger.info(
            "sandbox skipped",
            extra={
                "event": "sandbox_skipped",
                "agent": "execution_sandbox",
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "status": "skipped",
            },
        )
        return {
            "status": "skipped",
            "summary": "Execution sandbox is disabled in configuration.",
            "logs": "",
            "enabled": False,
            "docker_available": _docker_available(),
            "next_step": "Install/start Docker, then set SANDBOX_ENABLED=true to run generated code in a container.",
        }

    code = extract_python_code(generated_code)
    if not code:
        logger.info(
            "sandbox skipped no code",
            extra={
                "event": "sandbox_skipped_no_code",
                "agent": "execution_sandbox",
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "status": "skipped",
            },
        )
        return {
            "status": "skipped",
            "summary": "No generated Python code was available to check.",
            "logs": "",
        }

    if not _docker_available():
        logger.error(
            "sandbox docker unavailable",
            extra={
                "event": "sandbox_docker_unavailable",
                "agent": "execution_sandbox",
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "status": "failed",
                "error": "Docker is unavailable.",
            },
        )
        return {
            "status": "failed",
            "summary": "Docker is unavailable, so generated code was not executed on the application server.",
            "logs": "Install/start Docker or set SANDBOX_ENABLED=false to skip execution checks.",
            "enabled": True,
            "docker_available": False,
            "test_plan_received": bool(test_plan),
            "isolation": "host execution refused",
        }

    with tempfile.TemporaryDirectory(prefix="ai-software-team-sandbox-") as temp_dir:
        workspace = Path(temp_dir).resolve()
        generated_files = _write_generated_files(workspace, code)

        dependency_lines = _as_list(dependencies)
        if dependency_lines:
            (workspace / "requirements.txt").write_text("\n".join(dependency_lines) + "\n", encoding="utf-8")

        executable_tests = _as_code(test_code)
        if executable_tests:
            (workspace / "test_generated.py").write_text(executable_tests, encoding="utf-8")

        command, timeout_seconds = _docker_command(
            workspace,
            generated_files,
            bool(dependency_lines),
            bool(executable_tests),
        )
        try:
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            logs = "\n".join(part for part in [error.stdout, error.stderr] if part)
            logger.error(
                "sandbox timed out",
                extra={
                    "event": "sandbox_timeout",
                    "agent": "execution_sandbox",
                    "duration_ms": int((time.perf_counter() - started) * 1000),
                    "status": "failed",
                    "error": f"Timed out after {timeout_seconds} seconds.",
                },
            )
            return {
                "status": "failed",
                "summary": f"Sandbox timed out after {timeout_seconds} seconds and was destroyed.",
                "logs": logs,
                "test_plan_received": bool(test_plan),
                "files_checked": generated_files,
                "isolation": "docker",
            }

    status = "passed" if completed.returncode == 0 else "failed"
    logs = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    if status == "passed" and executable_tests:
        summary = "Generated Python code compiled and tests passed inside an isolated Docker sandbox."
    elif status == "passed":
        summary = "Generated Python code compiled successfully inside an isolated Docker sandbox."
    else:
        summary = "Generated Python code failed inside the isolated Docker sandbox."

    logger.info(
        "sandbox execution completed",
        extra={
            "event": "sandbox_execution_completed",
            "agent": "execution_sandbox",
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "status": status,
        },
    )
    return {
        "status": status,
        "summary": summary,
        "logs": logs,
        "enabled": True,
        "docker_available": True,
        "test_plan_received": bool(test_plan),
        "dependencies_installed": bool(dependency_lines),
        "tests_executed": bool(executable_tests),
        "files_checked": generated_files,
        "isolation": "docker",
    }
