import streamlit as st
from datetime import date
from utils.supabase_client import supabase


st.title("Assignments")


# ---------- Data layer ----------


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


def add_assignment(student_id: int):
    supabase.table("Assignment").insert({
        "student_id": student_id,
        "title": st.session_state.assignment_title,
        "description": st.session_state.assignment_description,
        "module": st.session_state.assignment_module,
        "deadline": st.session_state.assignment_deadline.isoformat(),
    }).execute()
    st.success("Assignment added successfully!")


def delete_assignment(student_id: int, assignment_id: int):
    supabase.table("Assignment") \
        .delete() \
        .eq("student_id", student_id) \
        .eq("assignment_id", assignment_id) \
        .execute()
    st.success("Assignment deleted.")


# ---------- Main layout ----------


student_id = st.session_state.get("student_id", 1)
assignments = get_assignments(student_id)

st.subheader("All Assignments")
if not assignments:
    st.info("No assignments yet. Add your first assignment below.")
else:
    for a in assignments:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{a['title']}** ({a.get('module') or 'No module'})")
                st.caption(a.get("description") or "No description")
                st.caption(f"Deadline: {a['deadline']}")
            with c2:
                if st.button("Delete", key=f"delete_assignment_{a['assignment_id']}", use_container_width=True):
                    delete_assignment(student_id, a["assignment_id"])
                    st.rerun()

st.markdown("---")

st.subheader("Add New Assignment")

with st.form("add_assignment_form"):
    st.text_input("Title", key="assignment_title")
    st.text_input("Module (optional)", key="assignment_module")
    st.text_area("Description (optional)", key="assignment_description")
    st.date_input("Deadline", key="assignment_deadline", value=date.today())

    submitted = st.form_submit_button("Add Assignment", type="primary", use_container_width=True)
    if submitted:
        add_assignment(student_id)
        st.rerun()