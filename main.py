from graph.workflow import graph


def main():
    print("=" * 60)
    print("AI Software Development Team")
    print("=" * 60)

    requirement = input("\nEnter your project requirement:\n> ")

    initial_state = {
        "requirement": requirement,
        "tasks": "",
        "code": "",
        "review": "",
        "tests": "",
        "documentation": "",
    }

    print("\nGenerating...\n")

    result = graph.invoke(initial_state)

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
