from graph.workflow import graph
from openai import OpenAIError, RateLimitError


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
        "tasks": "",
        "code": "",
        "review": "",
        "tests": "",
        "documentation": "",
    }

    print("\nGenerating...\n")

    try:
        result = graph.invoke(initial_state)
    except RateLimitError:
        print(
            "OpenAI quota was exceeded for the configured API key. "
            "Add billing/quota to that account or set a different OPENAI_API_KEY."
        )
        return
    except OpenAIError as error:
        print(f"OpenAI API error: {error}")
        return
    except Exception as error:
        print(f"Something went wrong while generating the project: {error}")
        return

    print("=" * 60)
    print("PROJECT TASKS")
    print("=" * 60)
    print(result["tasks"])

    print("\n")

    print("=" * 60)
    print("GENERATED CODE")
    print("=" * 60)
    print(result["code"])

    print("\n")

    print("=" * 60)
    print("CODE REVIEW")
    print("=" * 60)
    print(result["review"])

    print("\n")

    print("=" * 60)
    print("TEST CASES")
    print("=" * 60)
    print(result["tests"])

    print("\n")

    print("=" * 60)
    print("DOCUMENTATION")
    print("=" * 60)
    print(result.get("documentation", ""))


if __name__ == "__main__":
    main()
