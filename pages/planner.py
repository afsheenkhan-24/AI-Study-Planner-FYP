import streamlit as st
from datetime import datetime, date
from utils.supabase_client import supabase
from utils.llm_client import generate_study_plan
from utils.auth import run_auth


run_auth()
if "student_id" not in st.session_state or st.session_state.student_id is None:
    st.stop()

student_id: int = st.session_state.student_id

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


def get_study_days(student_id: int):
    try:
        resp = (
            supabase.table("Student")
            .select("study_days")
            .eq("student_id", student_id)
            .single()
            .execute()
        )
        data = resp.data or {}
        return data.get("study_days") or []
    except Exception:
        return []


def parse_deadline(task):
    d_str = task.get("deadline")
    try:
        return datetime.fromisoformat(d_str).date() if d_str else None
    except Exception:
        return None


# ---- Main layout ----

all_tasks = get_tasks(student_id)
today = date.today()

# Only plan for tasks that are not completed AND whose deadline is today or later
incomplete_future_tasks = []
overdue_tasks = []
for t in all_tasks:
    d = parse_deadline(t)
    if d is None:
        continue
    if t.get("status") == "Completed":
        continue
    if d < today:
        overdue_tasks.append(t)
    else:
        incomplete_future_tasks.append(t)

if overdue_tasks:
    st.warning(
        f"You have {len(overdue_tasks)} overdue task(s). "
        "They are not included in the new plan - please review them on the Dashboard."
    )

if not incomplete_future_tasks:
    st.info("All upcoming tasks are completed or past their deadlines. There is nothing to plan right now.")
    st.stop()

study_days = get_study_days(student_id)

st.subheader("AI Study Plan")

days_ahead = st.slider(
    "Plan for how many study days?",
    min_value=3,
    max_value=14,
    value=7,
    help="The AI will spread your tasks over this many upcoming study days.",
)

if study_days:
    pretty_days = ", ".join(study_days)
    st.caption(f"Using your preferred study days: {pretty_days}")
else:
    st.caption("No study day preferences set. The plan will use consecutive days from today.")

if st.button("Generate Study Plan", type="primary", use_container_width=True):
    with st.spinner("Generating study plan with AI..."):
        plan_text = generate_study_plan(
            incomplete_future_tasks,
            days_ahead=days_ahead,
            study_days=study_days,
        )
    st.markdown("### Suggested Plan")
    st.markdown(plan_text)
else:
    st.caption("Click the button to generate a plan using your current tasks and study preferences.")