# ui/app.py

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.llm import describe_llm_error


def describe_generation_error(error):
    error_name = error.__class__.__name__
    error_text = str(error)

    if (
        error_name in {"LLMConfigurationError", "AuthenticationError", "RateLimitError"}
        or "invalid_api_key" in error_text
        or "insufficient_quota" in error_text
        or "Please pass a valid API key" in error_text
        or error_name.endswith("OpenAIError")
        or "OpenAI" in error_name
    ):
        return describe_llm_error(error)

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
    page_icon="🤖",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #07111f 0%, #0f172a 45%, #111827 100%);
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .hero-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 24px;
        padding: 2rem;
        box-shadow: 0 18px 45px rgba(2, 6, 23, 0.35);
        backdrop-filter: blur(12px);
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        font-size: 1.06rem;
        color: #cbd5e1;
        line-height: 1.7;
    }
    .pill {
        display: inline-block;
        margin: 0.2rem 0.3rem 0.2rem 0;
        padding: 0.35rem 0.7rem;
        background: rgba(99, 102, 241, 0.16);
        color: #c7d2fe;
        border-radius: 999px;
        font-size: 0.85rem;
        border: 1px solid rgba(129, 140, 248, 0.25);
    }
    .info-card {
        background: rgba(15, 23, 42, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.9rem;
    }
    .info-card h4 {
        color: #f8fafc;
        margin-bottom: 0.3rem;
    }
    .info-card p {
        color: #cbd5e1;
        margin-bottom: 0;
    }
    .section-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 20px;
        padding: 1.2rem 1.3rem;
        margin-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">Build software with an AI team</div>
        <div class="hero-subtitle">
            Describe your idea, and let a manager, developer, reviewer, and tester collaborate to turn it into a structured plan with code and test guidance.
        </div>
        <div style="margin-top: 1rem;">
            <span class="pill">✨ Fast planning</span>
            <span class="pill">🧠 AI collaboration</span>
            <span class="pill">🧪 Review-ready output</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1.35, 0.95], gap="large")

with col1:
    st.markdown(
        """
        <div class="section-card">
            <h3 style="color:#f8fafc; margin-top:0;">What this experience offers</h3>
            <p style="color:#cbd5e1;">Turn a short requirement into tasks, implementation ideas, reviewed output, and testing suggestions in one flow.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="section-card">
            <h3 style="color:#f8fafc; margin-top:0;">Suggested prompts</h3>
            <p style="color:#cbd5e1;">• A task tracker dashboard<br>• A blog platform with auth<br>• A Python CLI for invoice automation</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="section-card">
        <h3 style="color:#f8fafc; margin-top:0;">Describe your project</h3>
    </div>
    """,
    unsafe_allow_html=True,
)

requirement = st.text_area(
    "Project requirement",
    height=180,
    key="requirement",
    placeholder=(
        "Example:\n"
        "Build an online food delivery app with login, payment gateway, and an admin dashboard."
    ),
)

if "last_requirement" not in st.session_state:
    st.session_state["last_requirement"] = ""

if "result" not in st.session_state:
    st.session_state["result"] = None

button_col, status_col = st.columns([0.4, 1.0])
with button_col:
    if st.button("Generate Project", type="primary"):
        if requirement.strip() == "":
            st.warning("Please enter a project requirement.")
            st.stop()

        if st.session_state["last_requirement"] != requirement:
            with st.spinner("Your AI team is preparing the project..."):
                try:
                    st.session_state["result"] = generate_project(requirement)
                    st.session_state["last_requirement"] = requirement
                except Exception as error:
                    st.error(describe_generation_error(error))
                    st.stop()
        else:
            st.success("Using the cached output for this requirement.")

with status_col:
    if st.session_state["result"] and st.session_state["last_requirement"] == requirement:
        st.success("Project generated successfully.")

if st.session_state["result"] and st.session_state["last_requirement"] == requirement:
    result = st.session_state["result"]

    tab1, tab2, tab3, tab4 = st.tabs(["Tasks", "Code", "Review", "Tests"])

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
