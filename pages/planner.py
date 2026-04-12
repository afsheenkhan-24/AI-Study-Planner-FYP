import streamlit as st
from datetime import datetime
from utils.supabase_client import supabase
from utils.ollama_client import generate_study_plan


st.title("Planner")


def format_date(date_str: str) -> str:
    try:
        d = datetime.fromisoformat(date_str).date()
        return d.strftime("%d %b %Y")
    except Exception:
        return date_str


# ---- Data layer ----

def get_tasks(student_id: int):
    response = (
        supabase
        .table("Task")
        .select("task_id, title, description, deadline, priority, status, estimated_time")
        .eq("student_id", student_id)
        .execute()
    )
    return response.data or []


# ---- Main layout ----

student_id = st.session_state.get("student_id", 1)
tasks = get_tasks(student_id)

if not tasks:
    st.info("You have no tasks yet. Generate tasks from assignments first.")
    st.stop()


st.subheader("AI Study Plan")

days_ahead = st.slider(
    "Plan for how many days?",
    min_value=3,
    max_value=14,
    value=7,
    help="The AI will spread your tasks over this many upcoming dates.",
)

if st.button("Generate Study Plan", type="primary", use_container_width=True):
    with st.spinner("Generating study plan with AI..."):
        plan_text = generate_study_plan(tasks, days_ahead=days_ahead)
    st.markdown("### Suggested Plan")
    st.markdown(plan_text)
else:
    st.caption("Click the button to generate a plan using your current tasks.")