import streamlit as st
from datetime import date, timedelta, datetime
from utils.supabase_client import supabase
from utils.llm_client import generate_subtasks_with_llm
from utils.auth import run_auth


run_auth()
if "student_id" not in st.session_state or st.session_state.student_id is None:
    st.stop()

student_id: int = st.session_state.student_id

st.title("Assignments")

st.markdown("---")


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


def update_assignment(
    student_id: int,
    assignment_id: int,
    title: str,
    module: str,
    description: str,
    deadline: date,
):
    supabase.table("Assignment").update({
        "title": title,
        "description": description,
        "module": module,
        "deadline": deadline.isoformat(),
    }).eq("student_id", student_id).eq("assignment_id", assignment_id).execute()
    st.success("Assignment updated successfully!")


def delete_assignment(student_id: int, assignment_id: int):
    # First delete all tasks linked to this assignment 
    supabase.table("Task") \
        .delete() \
        .eq("student_id", student_id) \
        .eq("assignment_id", assignment_id) \
        .execute()

    # Then delete the assignment itself
    supabase.table("Assignment") \
        .delete() \
        .eq("student_id", student_id) \
        .eq("assignment_id", assignment_id) \
        .execute()

    st.success("Assignment and its tasks were deleted.")


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
    sessions = len(scheduled_dates)

    subtasks = generate_subtasks_with_llm(title, description, sessions=sessions)
    if not subtasks or len(subtasks) != sessions:
        subtasks = [f"Session {i}" for i in range(1, sessions + 1)]

    tasks_payload = []
    for i, d in enumerate(scheduled_dates):
        label = subtasks[i]
        tasks_payload.append({
            "student_id": student_id,
            "assignment_id": assignment["assignment_id"],
            "title": f"{title} - {label}",
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


# ---- Dialogs ----

@st.dialog("Add new assignment")
def add_assignment_dialog(student_id: int):
    with st.form("add_assignment_form"):
        title = st.text_input("Title")
        module = st.text_input("Module (optional)")
        description = st.text_area("Description (optional)")
        deadline = st.date_input("Deadline", value=date.today(), format="DD-MM-YYYY")

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("Add", type="primary", use_container_width=True)
        with c2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            if not title:
                st.error("Title is required.")
            else:
                add_assignment(student_id, title, module, description, deadline)
                st.rerun()
        if cancel:
            st.rerun()


@st.dialog("Edit assignment")
def edit_assignment_dialog(student_id: int, assignment: dict):
    with st.form(f"edit_assignment_form_{assignment['assignment_id']}"):
        title = st.text_input("Title", value=assignment.get("title") or "")
        module = st.text_input("Module (optional)", value=assignment.get("module") or "")
        description = st.text_area("Description (optional)", value=assignment.get("description") or "")

        try:
            current_deadline = date.fromisoformat(assignment["deadline"])
        except Exception:
            current_deadline = date.today()
        deadline = st.date_input("Deadline", value=current_deadline, format="DD-MM-YYYY",)

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("Save changes", type="primary", use_container_width=True)
        with c2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            if not title:
                st.error("Title is required.")
            else:
                update_assignment(student_id, assignment["assignment_id"], title, module, description, deadline)
                st.rerun()
        if cancel:
            st.rerun()


# ---- Main layout ----

assignments = get_assignments(student_id)

st.button("Add assignment", on_click=add_assignment_dialog, args=(student_id,), type="primary")

if not assignments:
    st.info("No assignments yet. Use the button above to add your first assignment.")
else:
    for a in assignments:
        with st.container(border=True):
            c_title, c_buttons = st.columns([4, 2])
            with c_title:
                st.markdown(f"**{a['title']}** ({a.get('module') or 'No module'})")
                st.caption(f"Deadline: {format_date(a['deadline'])}")
            with c_buttons:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Edit", key=f"edit_assignment_{a['assignment_id']}", use_container_width=True):
                        edit_assignment_dialog(student_id, a)
                with b2:
                    if st.button("Delete", key=f"delete_assignment_{a['assignment_id']}", use_container_width=True):
                        delete_assignment(student_id, a["assignment_id"])
                        st.rerun()

            c_desc, c_auto = st.columns([4, 2])
            with c_desc:
                st.caption(a.get("description") or "No description")
            with c_auto:
                st.write("") 
                if st.button(
                    "Auto-create tasks",
                    key=f"gen_tasks_{a['assignment_id']}",
                    use_container_width=True,
                ):
                    create_tasks_from_assignment(a, student_id, sessions=5)