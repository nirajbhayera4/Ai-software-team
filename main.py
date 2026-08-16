import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def describe_generation_error(error):
    error_name = error.__class__.__name__
    error_text = str(error)

    if error_name == "RateLimitError" or "insufficient_quota" in error_text:
        return (
            "OpenAI quota was exceeded for the configured API key. "
            "Add billing/quota to that account or set a different OPENAI_API_KEY."
        )

    if error_name == "AuthenticationError" or "invalid_api_key" in error_text:
        return (
            "The configured API key is invalid. Replace LLM_API_KEY or "
            "OPENAI_API_KEY in your .env file with a valid provider key."
        )

    if error_name.endswith("OpenAIError") or "OpenAI" in error_name:
        return f"OpenAI API error: {error_text}"

    if error_name == "ModuleNotFoundError":
        if "No module named 'graph'" in error_text:
            return (
                "Project module `graph` could not be found. Run this command "
                "from the project root."
            )

        return (
            f"Missing Python package: {error_text}. "
            "Install the project dependencies with `pip install -r requirements.txt`."
        )

    return f"Something went wrong while generating the project: {error_text}"


def main():
    print("=" * 60)
    print("AI Software Development Team")
    print("=" * 60)

    try:
        requirement = input("\nEnter your project requirement:\n> ")
    except EOFError:
        print("No project requirement was provided.")
        return

    if not requirement.strip():
        print("Please enter a project requirement.")
        return

    initial_state = {
        "requirement": requirement,
        "tasks": {},
        "implementation": {},
        "review": {},
        "test_plan": {},
        "documentation": "",
    }

    print("\nGenerating...\n")

    try:
        from graph.workflow import graph

        result = graph.invoke(initial_state)
    except Exception as error:
        print(describe_generation_error(error))
        return

    print("=" * 60)
    print("PROJECT TASKS")
    print("=" * 60)
    print(result["tasks"])

    print("\n")

    print("=" * 60)
    print("DEVELOPER OUTPUT")
    print("=" * 60)
    print(result["implementation"])

    print("\n")

    print("=" * 60)
    print("CODE REVIEW")
    print("=" * 60)
    print(result["review"])

    print("\n")

    print("=" * 60)
    print("TEST CASES")
    print("=" * 60)
    print(result["test_plan"])

    print("\n")

    print("=" * 60)
    print("DOCUMENTATION")
    print("=" * 60)
    print(result.get("documentation", ""))


if __name__ == "__main__":
    main()
