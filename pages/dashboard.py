import streamlit as st
from datetime import date, datetime, timedelta
from utils.supabase_client import supabase

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

    if completion_ratio >= 0.75:
        messages.append("You've finished most of your tasks - consider reviewing or starting ahead on future work.")
    elif 0.4 <= completion_ratio < 0.75:
        messages.append("You're making steady progress. A short focused session today could push you closer to your goal.")
    elif 0 < completion_ratio < 0.4:
        messages.append("You've taken the first steps. Try completing one more task today to build confidence.")

    if num_overdue > 0:
        messages.append(
            "Some tasks are overdue. Pick one overdue task and focus on just that for a short, uninterrupted session."
        )
    elif not overdue_tasks and completion_ratio == 0:
        messages.append("You have upcoming tasks but nothing started yet. Choose one small task and begin with 20-30 minutes.")

    if not messages:
        messages.append("You're on track. Remember to take short breaks and look after your wellbeing as you study.")

    for msg in messages:
        st.info(msg)

    # ---- Wellbeing panel ----
    if show_wellbeing:
        st.markdown("### Wellbeing support")
        st.info(
            "Short breaks, sleep, and realistic plans matter as much as study time. "
            "If you feel overwhelmed, it is okay to slow down and ask for support."
        )
        st.markdown(
            "- University wellbeing services: "
            "[Kingston Wellbeing](https://www.kingston.ac.uk/student-support/health-and-wellbeing/)\n"
            "- Talk to your personal tutor or course team if deadlines feel unmanageable.\n"
            "- Try a 5-10 minute walk or breathing exercise before starting a difficult task."
        )

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
                st.caption(f"Due: {t['deadline']}  •  Priority: {t['priority']}  •  Status: {t['status']}")

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
                st.caption(f"Due: {t['deadline']}  •  Priority: {t['priority']}  •  Status: {t['status']}")

    # Overdue
    st.markdown("#### Overdue")
    if not overdue_tasks:
        st.caption("No overdue tasks. Nice!")
    else:
        for t in overdue_tasks:
            with st.container(border=True):
                st.markdown(f"**{t['title']}**")
                st.caption(t.get("description") or "No description")
                st.caption(f"Due: {t['deadline']}  •  Priority: {t['priority']}  •  Status: {t['status']}")

    # Reminders
    st.markdown("#### Reminders")

    urgent = []
    soon = []
    for t in tasks:
        d = parse_deadline(t.get("deadline"))
        if not d:
            continue
        days_left = (d - today).days
        if t.get("status") == "Completed":
            continue
        if days_left < 0:
            urgent.append((t, "Overdue"))
        elif days_left == 0:
            urgent.append((t, "Due today"))
        elif 0 < days_left <= 2:
            urgent.append((t, f"Due in {days_left} day(s)"))
        elif 3 <= days_left <= 7:
            soon.append((t, f"Due in {days_left} day(s)"))

    if not urgent and not soon:
        st.caption("No urgent reminders. You are on track.")
    else:
        if urgent:
            st.markdown("**Urgent**")
            for t, label in urgent:
                st.write(f"{label}: **{t['title']}** (deadline {t['deadline']})")
        if soon:
            st.markdown("**Coming up soon**")
            for t, label in soon:
                st.write(f"{label}: **{t['title']}** (deadline {t['deadline']})")


if __name__ == "__main__":
    main()