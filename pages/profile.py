import streamlit as st
from utils.supabase_client import supabase

st.title("Profile Settings")


def get_or_create_student(student_id: int):
    resp = (
        supabase.table("Student")
        .select("student_id, name, study_days, reminder_time_pref, timezone")
        .eq("student_id", student_id)
        .execute()
    )
    data = resp.data or []
    if data:
        return data[0]

    insert_resp = supabase.table("Student").insert({
        "student_id": student_id,
        "name": f"Student {student_id}",
        "study_days": ["Mon", "Tue", "Wed", "Thu"],
        "reminder_time_pref": "Evening",
        "timezone": "Europe/London",
        "show_wellbeing": True,
    }).execute()
    return insert_resp.data[0]


def update_profile(
    student_id: int,
    name: str,
    study_days,
    reminder_time_pref: str,
    timezone: str,
    show_wellbeing: bool,
):
    supabase.table("Student").update({
        "name": name,
        "study_days": study_days,
        "reminder_time_pref": reminder_time_pref,
        "timezone": timezone,
        "show_wellbeing": show_wellbeing,
    }).eq("student_id", student_id).execute()
    st.success("Profile updated.")


student_id = st.session_state.get("student_id", 1)
student = get_or_create_student(student_id)

name = st.text_input("Name", value=student.get("name") or "")

st.subheader("Study preferences")

day_options = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
current_days = student.get("study_days") or []
study_days = st.multiselect(
    "Preferred study days",
    options=day_options,
    default=[d for d in current_days if d in day_options] or ["Mon", "Tue", "Wed", "Thu"],
)

reminder_time_pref = st.selectbox(
    "Preferred reminder time",
    options=["Morning", "Afternoon", "Evening"],
    index=["Morning", "Afternoon", "Evening"].index(
        student.get("reminder_time_pref", "Evening")
    ),
)

st.subheader("Time zone")

timezone = st.text_input(
    "Time zone (IANA format, e.g. Europe/London)",
    value=student.get("timezone") or "Europe/London",
)

if st.button("Save profile", type="primary"):
    update_profile(student_id, name, study_days, reminder_time_pref, timezone)