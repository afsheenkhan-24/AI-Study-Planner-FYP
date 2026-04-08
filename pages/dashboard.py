import streamlit as st
from utils.supabase_client import supabase


def get_tasks(student_id: int):
    response = (
        supabase.table("Task")
        .select("task_id, title, description, deadline, priority, status, estimated_time")
        .eq("student_id", student_id)
        .execute()
    )
    return response.data or []


def main():
    st.title("AI Study Planner Dashboard")

    student_id = st.session_state.get("student_id", 1)
    tasks = get_tasks(student_id)

    if not tasks:
        st.info("You have no tasks yet. Go to the Tasks page to add your first task.")
        return

    # ---- Progress summary ----
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("status") == "Completed")
    in_progress_tasks = sum(1 for t in tasks if t.get("status") == "In Progress")
    todo_tasks = total_tasks - completed_tasks - in_progress_tasks

    completion_ratio = completed_tasks / total_tasks if total_tasks > 0 else 0

    st.subheader("Overall progress")
    st.progress(completion_ratio, text=f"{completed_tasks}/{total_tasks} tasks completed")

    col1, col2, col3 = st.columns(3)
    col1.metric("To Do", todo_tasks)
    col2.metric("In Progress", in_progress_tasks)
    col3.metric("Completed", completed_tasks)

    st.markdown("---")

    # ---- Deadline-focused views ----
    from datetime import date, datetime

    today = date.today()

    def parse_deadline(d):
        try:
            return datetime.fromisoformat(d).date()
        except Exception:
            return None

    today_tasks = []
    upcoming_tasks = []
    overdue_tasks = []

    for t in tasks:
        d = parse_deadline(t.get("deadline"))
        if not d:
            continue
        if d < today:
            overdue_tasks.append(t)
        elif d == today:
            today_tasks.append(t)
        else:
            upcoming_tasks.append(t)

    # Overdue
    st.subheader("Overdue tasks")
    if not overdue_tasks:
        st.caption("No overdue tasks. Nice!")
    else:
        for t in overdue_tasks:
            with st.container(border=True):
                st.markdown(f"**{t['title']}**")
                st.caption(t.get("description") or "No description")
                st.caption(f"Due: {t['deadline']}  •  Priority: {t['priority']}  •  Status: {t['status']}")

    st.markdown("---")

    # Today
    st.subheader("Today")
    if not today_tasks:
        st.caption("No tasks due today.")
    else:
        for t in today_tasks:
            with st.container(border=True):
                st.markdown(f"**{t['title']}**")
                st.caption(t.get("description") or "No description")
                st.caption(f"Due: {t['deadline']}  •  Priority: {t['priority']}  •  Status: {t['status']}")

    st.markdown("---")

    # Upcoming (next 7 days)
    from datetime import timedelta

    horizon = today + timedelta(days=7)
    upcoming_next_week = [
        t for t in upcoming_tasks
        if parse_deadline(t.get("deadline")) and today < parse_deadline(t["deadline"]) <= horizon
    ]

    st.subheader("Upcoming (next 7 days)")
    if not upcoming_next_week:
        st.caption("No upcoming tasks in the next 7 days.")
    else:
        for t in upcoming_next_week:
            with st.container(border=True):
                st.markdown(f"**{t['title']}**")
                st.caption(t.get("description") or "No description")
                st.caption(f"Due: {t['deadline']}  •  Priority: {t['priority']}  •  Status: {t['status']}")


if __name__ == "__main__":
    main()