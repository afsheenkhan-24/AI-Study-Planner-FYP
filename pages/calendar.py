import streamlit as st
from datetime import date, datetime
from utils.supabase_client import supabase


st.title("Calendar")

def format_date(date_str: str) -> str:
    try:
        d = datetime.fromisoformat(date_str).date()
        return d.strftime("%d %b %Y")
    except Exception:
        return date_str


def parse_deadline(d):
    try:
        return datetime.fromisoformat(d).date()
    except Exception:
        return None


# ---- Data layer ----

def get_tasks(student_id: int):
    response = (
        supabase
        .table("Task")
        .select(
            "task_id, title, description, deadline, priority, status, "
            "estimated_time, assignment_id"
        )
        .eq("student_id", student_id)
        .execute()
    )
    return response.data or []


# ---- Main layout ----

student_id = st.session_state.get("student_id", 1)
tasks = get_tasks(student_id)

if not tasks:
    st.info("No tasks yet. Generate tasks from your assignments first.")
    st.stop()

today = date.today()

# Date picker
selected_date = st.date_input(
    "Select a date",
    value=today,
)

# Tasks on selected date
tasks_on_selected = []
for t in tasks:
    d = parse_deadline(t.get("deadline"))
    if not d:
        continue
    if d == selected_date:
        tasks_on_selected.append(t)

st.markdown(f"### Tasks on {selected_date.strftime('%d %b %Y')}")

if not tasks_on_selected:
    st.caption("No tasks scheduled for this date.")
else:
    for t in tasks_on_selected:
        with st.container(border=True):
            st.markdown(f"**{t['title']}**")
            st.caption(t.get("description") or "No description")
            st.caption(
                f"Deadline: {format_date(t['deadline'])}  •  "
                f"Priority: {t['priority']}  •  Status: {t['status']}  •  "
                f"Est: {t.get('estimated_time','N/A')}h"
            )