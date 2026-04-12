import streamlit as st
from datetime import date, timedelta, datetime
from utils.supabase_client import supabase


st.title("Assignments")

def format_date(date_str: str) -> str:
    try:
        d = datetime.fromisoformat(date_str).date()
        return d.strftime("%d %b %Y")
    except Exception:
        return date_str


# ---- Data layer ----


def get_assignments(student_id: int):
    response = (
        supabase
        .table("Assignment")
        .select("assignment_id, title, description, module, deadline, created_at")
        .eq("student_id", student_id)
        .order("deadline", desc=False)
        .execute()
    )
    return response.data or []


def add_assignment(student_id: int, title: str, module: str, description: str, deadline: date):
    supabase.table("Assignment").insert({
        "student_id": student_id,
        "title": title,
        "description": description,
        "module": module,
        "deadline": deadline.isoformat(),
    }).execute()
    st.success("Assignment added successfully!")


def delete_assignment(student_id: int, assignment_id: int):
    supabase.table("Assignment") \
        .delete() \
        .eq("student_id", student_id) \
        .eq("assignment_id", assignment_id) \
        .execute()
    st.success("Assignment deleted.")


def create_tasks_from_assignment(assignment, student_id: int, sessions: int = 5):
    title = assignment["title"]
    description = assignment.get("description") or ""
    deadline_str = assignment["deadline"]
    deadline = date.fromisoformat(deadline_str)
    today = date.today()

    if deadline <= today:
        st.warning("Deadline is today or in the past; cannot schedule tasks in the future.")
        return

    total_days = (deadline - today).days
    if total_days < sessions:
        sessions = total_days
        if sessions <= 0:
            st.warning("Not enough days between today and the deadline to create sessions.")
            return

    step = max(1, total_days // sessions)
    scheduled_dates = []
    current = today
    while current < deadline and len(scheduled_dates) < sessions:
        scheduled_dates.append(current)
        current = current + timedelta(days=step)
    if deadline not in scheduled_dates:
        scheduled_dates.append(deadline)

    scheduled_dates = sorted(set(scheduled_dates))

    tasks_payload = []
    for i, d in enumerate(scheduled_dates, start=1):
        tasks_payload.append({
            "student_id": student_id,
            "assignment_id": assignment["assignment_id"],
            "title": f"{title} - Session {i}",
            "description": description,
            "deadline": d.isoformat(),
            "priority": "Medium",
            "status": "To Do",
            "estimated_time": "1",
        })

    if not tasks_payload:
        st.warning("No tasks generated from this assignment.")
        return

    supabase.table("Task").insert(tasks_payload).execute()
    st.success(f"Created {len(tasks_payload)} tasks for this assignment.")


# ---- Add assignment dialog ----

@st.dialog("Add new assignment")
def add_assignment_dialog(student_id: int):
    with st.form("add_assignment_form"):
        title = st.text_input("Title")
        module = st.text_input("Module (optional)")
        description = st.text_area("Description (optional)")
        deadline = st.date_input("Deadline", value=date.today())

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("Add", type="primary", use_container_width=True)
        with c2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            add_assignment(student_id, title, module, description, deadline)
            st.rerun()
        if cancel:
            st.rerun()


# ---- Main layout ----

student_id = st.session_state.get("student_id", 1)
assignments = get_assignments(student_id)

st.button("Add assignment", on_click=add_assignment_dialog, args=(student_id,), type="primary")

if not assignments:
    st.info("No assignments yet. Use the button above to add your first assignment.")
else:
    for a in assignments:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{a['title']}** ({a.get('module') or 'No module'})")
                st.caption(a.get("description") or "No description")
                st.caption(f"Deadline: {format_date(a['deadline'])}")
            with c2:
                if st.button("Auto-create tasks", key=f"gen_tasks_{a['assignment_id']}", use_container_width=True):
                    create_tasks_from_assignment(a, student_id, sessions=5)
                if st.button("Delete", key=f"delete_assignment_{a['assignment_id']}", use_container_width=True):
                    delete_assignment(student_id, a["assignment_id"])
                    st.rerun()