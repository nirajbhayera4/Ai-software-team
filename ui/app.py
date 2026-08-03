# ui/app.py

import streamlit as st
from graph.workflow import graph

st.set_page_config(
    page_title="AI Software Team",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Software Development Team")
st.write(
    "Enter your software idea and let the AI Manager, Developer, Reviewer, and Tester collaborate."
)

requirement = st.text_area(
    "Project Requirement",
    height=200,
    placeholder="Example:\nBuild an Online Food Delivery App with login, payment gateway, and admin dashboard."
)

if st.button("Generate Project"):

    if requirement.strip() == "":
        st.warning("Please enter a project requirement.")
        st.stop()

    initial_state = {
        "requirement": requirement,
        "tasks": "",
        "code": "",
        "review": "",
        "tests": ""
    }

    with st.spinner("AI Team is working..."):

        result = graph.invoke(initial_state)

    st.success("Project Generated Successfully!")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📋 Tasks",
            "💻 Code",
            "🔍 Review",
            "🧪 Tests"
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