import streamlit as st
from datetime import date, datetime, timedelta
from utils.supabase_client import supabase


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
            "estimated_time, assignment_id"
        )
        .eq("student_id", student_id)
        .execute()
    )
    return response.data or []


def parse_deadline(d):
    try:
        return datetime.fromisoformat(d).date()
    except Exception:
        return None


def get_student_prefs(student_id: int):
    try:
        resp = (
            supabase.table("Student")
            .select("show_wellbeing")
            .eq("student_id", student_id)
            .execute()
        )
        data = resp.data or []
        if not data:
            return {"show_wellbeing": True}
        return data[0]
    except Exception:
        return {"show_wellbeing": True}


def main():
    st.title("Dashboard")

    student_id = st.session_state.get("student_id", 1)
    tasks = get_tasks(student_id)
    prefs = get_student_prefs(student_id)
    show_wellbeing = prefs.get("show_wellbeing", True)

    if not tasks:
        st.info("You have no tasks yet. Create assignments and auto-generate tasks, or generate a plan.")
        return

    today = date.today()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("status") == "Completed")
    in_progress_tasks = sum(1 for t in tasks if t.get("status") == "In Progress")
    todo_tasks = total_tasks - completed_tasks - in_progress_tasks
    completion_ratio = completed_tasks / total_tasks if total_tasks > 0 else 0

    overdue_tasks, today_tasks, upcoming_tasks = [], [], []
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

    # ---- Progress overview ----
    st.subheader("Progress overview")
    st.progress(completion_ratio, text=f"{completed_tasks}/{total_tasks} tasks completed")

    c1, c2, c3 = st.columns(3)
    c1.metric("To Do", todo_tasks)
    c2.metric("In Progress", in_progress_tasks)
    c3.metric("Completed", completed_tasks)

    # ---- Motivational messages ----
    num_overdue = len(overdue_tasks)
    messages = []

    if completed_tasks >= 1 and completed_tasks < 5:
        messages.append("Nice start - you've already completed your first tasks. Keep the momentum going.")
    elif completed_tasks >= 5 and completed_tasks < 10:
        messages.append("Great work - you've completed 5+ tasks. You're building a strong habit.")
    elif completed_tasks >= 10:
        messages.append("Impressive - 10 or more tasks completed. You're staying on top of your workload.")

    if not messages:
        messages.append("You're on track. Remember to take short breaks and look after your wellbeing as you study.")

    for msg in messages:
        st.info(msg)

    # ---- Today and upcoming tasks ----
    st.markdown("---")
    st.subheader("Today and upcoming tasks")

    # Today
    st.markdown("Today")
    if not today_tasks:
        st.caption("No tasks due today.")
    else:
        for t in today_tasks:
            with st.container(border=True):
                st.markdown(f"**{t['title']}**")
                st.caption(t.get("description") or "No description")
                st.caption(
                    f"Due: {format_date(t['deadline'])}  •  "
                    f"Priority: {t['priority']}  •  Status: {t['status']}"
                )

    # Upcoming next 7 days
    st.markdown("#### Next 7 days")
    horizon = today + timedelta(days=7)
    upcoming_next_week = [
        t for t in upcoming_tasks
        if parse_deadline(t.get("deadline")) and today < parse_deadline(t["deadline"]) <= horizon
    ]

    if not upcoming_next_week:
        st.caption("No upcoming tasks in the next 7 days.")
    else:
        for t in upcoming_next_week:
            with st.container(border=True):
                st.markdown(f"**{t['title']}**")
                st.caption(t.get("description") or "No description")
                st.caption(
                    f"Due: {format_date(t['deadline'])}  •  "
                    f"Priority: {t['priority']}  •  Status: {t['status']}"
                )

    # Overdue
    st.markdown("#### Overdue")
    if not overdue_tasks:
        st.caption("No overdue tasks. Nice!")
    else:
        for t in overdue_tasks:
            with st.container(border=True):
                st.markdown(f"**{t['title']}**")
                st.caption(t.get("description") or "No description")
                st.caption(
                    f"Due: {format_date(t['deadline'])}  •  "
                    f"Priority: {t['priority']}  •  Status: {t['status']}"
                )

if __name__ == "__main__":
    main()