import streamlit as st
from datetime import date, datetime
from utils.supabase_client import supabase


st.title("Tasks")


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
        .select(
            "task_id, title, description, deadline, priority, status, "
            "estimated_time"
        )
        .eq("student_id", student_id)
        .execute()
    )
    return response.data or []


def update_task(student_id: int, task_id: int):
    supabase.table("Task").update({
        "status": st.session_state.update_status,
    }).eq("student_id", student_id).eq("task_id", task_id).execute()
    st.success("Task updated successfully!")


def delete_task(student_id: int, task_id: int):
    supabase.table("Task").delete() \
        .eq("student_id", student_id) \
        .eq("task_id", task_id) \
        .execute()
    st.success("Task deleted successfully!")


# ---- Update Task Dialog ----

@st.dialog(title="Update Task status")
def update_task_dialog(task):
    with st.form("update_task_form"):
        st.markdown(f"**{task['title']}**")
        st.caption(task.get("description") or "No description")
        st.date_input(
            "Due Date",
            value=date.fromisoformat(task["deadline"]),
            disabled=True,
        )
        st.selectbox(
            "Status",
            options=["To Do", "In Progress", "Completed"],
            index=["To Do", "In Progress", "Completed"].index(task["status"]),
            key="update_status",
        )

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("Update", type="primary", use_container_width=True)
        with c2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            student_id = st.session_state.student_id
            update_task(student_id, task["task_id"])
            st.rerun()

        if cancel:
            st.rerun()


# ---- Main layout ----

student_id = st.session_state.student_id
tasks = get_tasks(student_id)

st.subheader("All Tasks")
if not tasks:
    st.info("No tasks yet. Generate a study plan on the Planner page.")
else:
    for t in tasks:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1.5, 1], width="stretch")
            with c1:
                st.markdown(f"**{t['title']}**")
                st.caption(t["description"] or "No description")
                st.caption(f"Estimated time: {t['estimated_time'] or 'N/A'} hours")
            with c2:
                st.markdown(f"**{t['status']}**")
                st.caption(f"Due: {format_date(t['deadline'])}")
                st.caption(f"Priority: {t['priority']}")
            with c3:
                if st.button("Edit status", key=f"edit_{t['task_id']}", use_container_width=True):
                    update_task_dialog(t)
                if st.button("Delete", key=f"delete_{t['task_id']}", type="secondary", use_container_width=True):
                    delete_task(student_id, t["task_id"])
                    st.rerun()