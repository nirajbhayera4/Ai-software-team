import argparse
import json
import time

from db import (
    complete_benchmark_run,
    create_benchmark_run,
    create_project,
    get_benchmark_run,
    get_project,
    get_task_workspace,
    initialize_database,
    save_benchmark_result,
)
from orchestrator import run_project_workflow


BENCHMARK_TASKS = [
    {
        "name": "Password Validator",
        "requirement": "Build a Python password validator with length, uppercase, lowercase, digit, and symbol checks plus tests.",
    },
    {
        "name": "Todo REST API",
        "requirement": "Build a FastAPI todo API with create, list, update, delete, validation, and tests.",
    },
    {
        "name": "CSV Summarizer",
        "requirement": "Build a Python utility that reads CSV sales rows and returns totals by product with tests.",
    },
    {
        "name": "Rate Limiter",
        "requirement": "Implement an in-memory token bucket rate limiter with tests for refill and rejection behavior.",
    },
    {
        "name": "JWT Auth Helper",
        "requirement": "Implement JWT-style token create/verify helpers with expiry checks and tests.",
    },
    {
        "name": "Markdown Link Extractor",
        "requirement": "Build a parser that extracts Markdown links and images into structured data with tests.",
    },
    {
        "name": "Shopping Cart",
        "requirement": "Implement a shopping cart class with add, remove, subtotal, discounts, tax, and tests.",
    },
    {
        "name": "Task Scheduler",
        "requirement": "Build a simple priority task scheduler that orders by priority then creation time with tests.",
    },
    {
        "name": "Log Analyzer",
        "requirement": "Build a Python log analyzer that counts errors by level and endpoint with tests.",
    },
    {
        "name": "URL Shortener Core",
        "requirement": "Implement URL shortener core functions for slug generation, collision handling, and validation with tests.",
    },
    {
        "name": "Expense Splitter",
        "requirement": "Build an expense splitter that calculates who owes whom and includes rounding tests.",
    },
    {
        "name": "Feature Flag Evaluator",
        "requirement": "Implement feature flag evaluation by user id, percentage rollout, and explicit overrides with tests.",
    },
    {
        "name": "Inventory Tracker",
        "requirement": "Build inventory tracking functions for stock adjustments, low-stock detection, and tests.",
    },
    {
        "name": "Email Normalizer",
        "requirement": "Implement email normalization and validation rules with edge-case tests.",
    },
    {
        "name": "Cache With TTL",
        "requirement": "Build a small TTL cache with get, set, delete, expiry, and tests.",
    },
    {
        "name": "Bank Account",
        "requirement": "Implement a bank account class with deposit, withdraw, transfer, overdraft protection, and tests.",
    },
    {
        "name": "Search Filter",
        "requirement": "Build a product search filter for query text, category, price range, sorting, and tests.",
    },
    {
        "name": "Webhook Verifier",
        "requirement": "Implement HMAC webhook signature verification with timestamp tolerance and tests.",
    },
    {
        "name": "Pagination Helper",
        "requirement": "Build pagination helpers that calculate page metadata and slice results with tests.",
    },
    {
        "name": "Config Loader",
        "requirement": "Build a config loader that merges defaults, environment overrides, validation, and tests.",
    },
]


def _review_approved(result):
    review = result.get("review") if isinstance(result, dict) else {}
    return bool(isinstance(review, dict) and review.get("approved"))


def _sandbox_passed(result):
    sandbox = result.get("sandbox") if isinstance(result, dict) else {}
    return isinstance(sandbox, dict) and sandbox.get("status") == "passed"


def _score_correctness(result, workflow_errors):
    if not isinstance(result, dict):
        return 0.0
    score = 0.0
    if result.get("status") == "completed":
        score += 0.35
    if _sandbox_passed(result):
        score += 0.35
    if _review_approved(result):
        score += 0.20
    if not workflow_errors:
        score += 0.10
    return round(min(score, 1.0), 3)


def _metrics_from_workspace(result, workspace, elapsed_ms):
    agent_runs = workspace.get("agent_runs", []) if workspace else []
    llm_calls = workspace.get("llm_calls", []) if workspace else []
    workflow_errors = result.get("workflow_errors", []) if isinstance(result, dict) else []
    latency_ms = workspace.get("total_duration_ms") if workspace else 0
    if not latency_ms:
        latency_ms = elapsed_ms

    return {
        "status": "completed" if result.get("status") == "completed" else "failed",
        "correctness_score": _score_correctness(result, workflow_errors),
        "tests_passed": _sandbox_passed(result),
        "reviewer_approved": _review_approved(result),
        "iterations": sum(1 for run in agent_runs if run.get("agent_name") == "developer") or 1,
        "latency_ms": int(latency_ms or 0),
        "cost_usd": round(sum(call.get("cost_usd") or 0 for call in llm_calls), 8),
        "metrics": {
            "agent_runs": len(agent_runs),
            "llm_calls": len(llm_calls),
            "workflow_errors": workflow_errors,
            "sandbox_status": (result.get("sandbox") or {}).get("status") if isinstance(result, dict) else None,
            "reviewer_approved": _review_approved(result),
        },
    }


def run_benchmark(owner_id, limit=None, tasks=None, workflow_runner=run_project_workflow):
    selected_tasks = list(tasks or BENCHMARK_TASKS)
    if limit:
        selected_tasks = selected_tasks[:limit]

    benchmark_run_id = create_benchmark_run(owner_id, len(selected_tasks))
    for benchmark_task in selected_tasks:
        started = time.perf_counter()
        project_id = None
        task_id = None
        try:
            project_id = create_project(
                owner_id,
                f"Benchmark: {benchmark_task['name']}",
                benchmark_task["requirement"],
            )
            project = get_project(project_id, owner_id)
            result = workflow_runner(project)
            task_id = result.get("task_id")
            workspace = get_task_workspace(task_id) if task_id else None
            metrics = _metrics_from_workspace(
                result,
                workspace,
                int((time.perf_counter() - started) * 1000),
            )
            save_benchmark_result(
                benchmark_run_id,
                name=benchmark_task["name"],
                requirement=benchmark_task["requirement"],
                project_id=project_id,
                task_id=task_id,
                **metrics,
            )
        except Exception as error:
            save_benchmark_result(
                benchmark_run_id,
                name=benchmark_task["name"],
                requirement=benchmark_task["requirement"],
                project_id=project_id,
                task_id=task_id,
                status="failed",
                correctness_score=0.0,
                tests_passed=False,
                reviewer_approved=False,
                iterations=0,
                latency_ms=int((time.perf_counter() - started) * 1000),
                cost_usd=0.0,
                error=str(error),
                metrics={"workflow_errors": [{"error_type": "benchmark_exception", "error": str(error)}]},
            )

    return complete_benchmark_run(benchmark_run_id)


def benchmark_summary(benchmark_run):
    return {
        "benchmark_run_id": benchmark_run["id"],
        "status": benchmark_run["status"],
        "tasks_completed": f"{benchmark_run['completed_tasks']}/{benchmark_run['total_tasks']}",
        "tests_passing": f"{benchmark_run['tests_passing_rate'] * 100:.1f}%",
        "reviewer_approval": f"{benchmark_run['reviewer_approval_rate'] * 100:.1f}%",
        "average_iterations": round(benchmark_run["average_iterations"], 2),
        "average_latency_seconds": round(benchmark_run["average_latency_ms"] / 1000, 2),
        "average_llm_cost_usd": round(benchmark_run["average_cost_usd"], 6),
        "average_correctness_score": round(benchmark_run["average_correctness_score"], 3),
    }


def main():
    parser = argparse.ArgumentParser(description="Run the AI Software Team coding benchmark.")
    parser.add_argument("--owner-id", type=int, required=True, help="User id that owns created benchmark projects.")
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N benchmark tasks.")
    args = parser.parse_args()

    initialize_database()
    benchmark_run = run_benchmark(args.owner_id, limit=args.limit)
    detailed = get_benchmark_run(benchmark_run["id"], args.owner_id)
    print(json.dumps({"summary": benchmark_summary(benchmark_run), "benchmark": detailed}, indent=2))


if __name__ == "__main__":
    main()
