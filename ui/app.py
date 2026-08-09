# ui/app.py

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
                "Project module `graph` could not be found. Start Streamlit "
                "from the project root with `python -m streamlit run ui/app.py`."
            )

        return (
            f"Missing Python package: {error_text}. "
            "Install the project dependencies with `pip install -r requirements.txt`."
        )

    return f"Something went wrong while generating the project: {error_text}"


@st.cache_data(ttl=3600)
def generate_project(requirement: str):
    from graph.workflow import graph

    initial_state = {
        "requirement": requirement,
        "tasks": "",
        "code": "",
        "review": "",
        "tests": "",
    }

    return graph.invoke(initial_state)


st.set_page_config(
    page_title="AI Software Team",
    page_icon="AI",
    layout="wide",
)

st.title("AI Software Development Team")
st.write(
    "Enter your software idea and let the AI Manager, Developer, Reviewer, "
    "and Tester collaborate."
)

requirement = st.text_area(
    "Project Requirement",
    height=200,
    key="requirement",
    placeholder=(
        "Example:\n"
        "Build an Online Food Delivery App with login, payment gateway, "
        "and admin dashboard."
    ),
)

if "last_requirement" not in st.session_state:
    st.session_state["last_requirement"] = ""

if "result" not in st.session_state:
    st.session_state["result"] = None

if st.button("Generate Project"):
    if requirement.strip() == "":
        st.warning("Please enter a project requirement.")
        st.stop()

    if st.session_state["last_requirement"] != requirement:
        with st.spinner("AI Team is working..."):
            try:
                st.session_state["result"] = generate_project(requirement)
                st.session_state["last_requirement"] = requirement
            except Exception as error:
                st.error(describe_generation_error(error))
                st.stop()
    else:
        st.success("Using cached output for the same requirement.")

if st.session_state["result"] and st.session_state["last_requirement"] == requirement:
    result = st.session_state["result"]
    st.success("Project Generated Successfully!")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Tasks",
            "Code",
            "Review",
            "Tests",
        ]
    )

    with tab1:
        st.subheader("Project Tasks")
        st.markdown(result["tasks"])

    with tab2:
        st.subheader("Generated Code")
        st.code(result["code"], language="python")

    with tab3:
        st.subheader("Code Review")
        st.markdown(result["review"])

    with tab4:
        st.subheader("Testing Plan")
        st.markdown(result["tests"])
