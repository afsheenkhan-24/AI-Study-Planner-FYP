import streamlit as st
from datetime import date, datetime, timedelta
import pandas as pd
from utils.supabase_client import supabase
from utils.auth import run_auth


run_auth()
if "student_id" not in st.session_state or st.session_state.student_id is None:
    st.stop()

student_id: int = st.session_state.student_id


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
            .select("study_days, reminder_time_pref, timezone, show_wellbeing, theme, font_size")
            .eq("student_id", student_id)
            .execute()
        )
        data = resp.data or []
        if not data:
            return {"show_wellbeing": True, "theme": "Light", "font_size": "Normal"}
        return data[0]
    except Exception:
        return {"show_wellbeing": True, "theme": "Light", "font_size": "Normal"}


def compute_streak(tasks):
    today = date.today()
    completed_dates = set()
    for t in tasks:
        if t.get("status") == "Completed":
            try:
                d = datetime.fromisoformat(t.get("deadline")).date()
            except Exception:
                continue
            completed_dates.add(d)

    streak = 0
    current = today
    while current in completed_dates:
        streak += 1
        current = current - timedelta(days=1)
    return streak


def main():
    st.title("Dashboard")

    st.markdown("---")

    tasks = get_tasks(student_id)
    prefs = get_student_prefs(student_id)
    show_wellbeing = prefs.get("show_wellbeing", True)
    study_days = prefs.get("study_days") or []
    reminder_pref = prefs.get("reminder_time_pref", "Evening")

    if not tasks:
        st.info("You have no tasks yet. Create assignments and auto-generate tasks, or generate a plan.")
        return

    today = date.today()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("status") == "Completed")
    in_progress_tasks = sum(1 for t in tasks if t.get("status") == "In Progress")
    postponed_tasks = sum(1 for t in tasks if t.get("status") == "Postponed")
    todo_tasks = total_tasks - completed_tasks - in_progress_tasks - postponed_tasks
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("To Do", todo_tasks)
    c2.metric("In Progress", in_progress_tasks)
    c3.metric("Completed", completed_tasks)
    c4.metric("Postponed", postponed_tasks)

    streak = compute_streak(tasks)
    st.caption(f"Current completion streak: {streak} day(s)")

    # ---- Motivational messages ----
    num_overdue = len(overdue_tasks)
    messages = []

    if completed_tasks >= 1 and completed_tasks < 5:
        messages.append("Nice start - you've already completed your first tasks. Keep the momentum going.")
    elif completed_tasks >= 5 and completed_tasks < 10:
        messages.append("Great work - you've completed 5+ tasks. You're building a strong habit.")
    elif completed_tasks >= 10:
        messages.append("Impressive - 10 or more tasks completed. You're staying on top of your workload.")

    if num_overdue:
        messages.append(
            "You have some overdue tasks. Let's adjust your plan and tackle one small item first."
        )

    if not messages:
        messages.append("You're on track. Remember to take short breaks and look after your wellbeing as you study.")

    for msg in messages:
        st.info(msg)

    # ---- Today and upcoming tasks ----
    st.markdown("---")
    st.subheader("Today and upcoming tasks")

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

    # ---- Reminders ----
    st.markdown("---")
    st.subheader("Reminders")

    REMINDER_WINDOW_DAYS = 2
    reminder_cutoff = today + timedelta(days=REMINDER_WINDOW_DAYS)
    reminder_tasks = [
        t for t in upcoming_tasks
        if parse_deadline(t.get("deadline")) and today <= parse_deadline(t["deadline"]) <= reminder_cutoff
        and t.get("status") != "Completed"
    ]

    if not overdue_tasks and not today_tasks and not reminder_tasks:
        st.caption("No reminders at the moment. You're all caught up.")
    else:
        for t in overdue_tasks:
            with st.container(border=True):
                st.warning(
                    f"Overdue: **{t['title']}** "
                    f"(was due {format_date(t['deadline'])}, status: {t['status']})"
                )
        for t in today_tasks:
            with st.container(border=True):
                st.info(
                    f"Due today ({reminder_pref.lower()}): **{t['title']}** "
                    f"(due {format_date(t['deadline'])}, status: {t['status']})"
                )
        for t in reminder_tasks:
            with st.container(border=True):
                st.caption(
                    f"Coming up soon ({reminder_pref.lower()}): **{t['title']}** – "
                    f"due {format_date(t['deadline'])}, Priority: {t['priority']}, Status: {t['status']}"
                )

    # ---- Wellbeing support ----
    if show_wellbeing:
        st.markdown("---")
        st.subheader("Wellbeing support (optional)")
        st.caption(
            "Studying is demanding. Remember to take breaks, sleep well, and reach out if you feel overwhelmed."
        )
        st.markdown(
            "- Kingston University wellbeing services: https://www.kingston.ac.uk/student-support/wellbeing/\n"
            "- Mind (mental health charity): https://www.mind.org.uk/\n"
            "- Samaritans (24/7 listening support): https://www.samaritans.org/"
        )

    # ---- Export upcoming schedule ----
    st.markdown("---")
    st.subheader("Export upcoming schedule")

    df = pd.DataFrame(tasks)
    if not df.empty:
        cols = ["title", "description", "deadline", "priority", "status", "estimated_time"]
        export_df = df[cols]
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download schedule as CSV",
            data=csv,
            file_name="study_schedule.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.caption("No tasks available to export.")


if __name__ == "__main__":
    main()