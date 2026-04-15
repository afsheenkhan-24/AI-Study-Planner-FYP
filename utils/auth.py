import streamlit as st
from utils.supabase_client import get_supabase_client


def _get_or_create_student_for_user(user):
    """
    Map a Supabase Auth user (UUID id) to a numeric Student.student_id.

    - Looks up Student by auth_user_id.
    - If not found, creates a new Student row with defaults and returns its student_id.
    """
    supabase = get_supabase_client()

    # 1) find existing Student row by auth_user_id
    resp = (
        supabase.table("Student")
        .select("student_id")
        .eq("auth_user_id", user.id)
        .execute()
    )
    data = resp.data or []
    if data:
        return data[0]["student_id"]

    # 2) If not found, create a new Student row and let DB assign numeric student_id
    metadata = user.user_metadata or {}
    name = metadata.get("full_name") or "Student"
    email = user.email or metadata.get("email") or ""

    insert_resp = supabase.table("Student").insert({
        "auth_user_id": user.id,
        "name": name,
        "email": email, 
        "study_days": ["Mon", "Tue", "Wed", "Thu"],
        "reminder_time_pref": "Evening",
        "timezone": "Europe/London",
        "show_wellbeing": True
    }).execute()

    student_row = insert_resp.data[0]
    return student_row["student_id"]


def run_auth() -> bool:
    if st.session_state.get("user") and st.session_state.get("student_id") is not None:
        return True

    supabase = get_supabase_client()

    st.title("PlanMyStudy")
    st.caption("Plan your study time, tasks, and assignments")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    # ---- LOGIN ----
    with tab_login:
        st.subheader("Sign in to your account")

        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Sign in", key="btn_login", use_container_width=True):
            if not login_email or not login_password:
                st.warning("Please enter your email and password.")
            else:
                try:
                    response = supabase.auth.sign_in_with_password(
                        {
                            "email": login_email,
                            "password": login_password,
                        }
                    )
                    user = response.user
                    if user:
                        try:
                            student_id = _get_or_create_student_for_user(user)
                        except Exception as e:
                            st.error(f"Error looking up student profile: {e}")
                            st.stop()

                        st.session_state["user"] = user
                        st.session_state["student_id"] = student_id

                        if "profile" not in st.session_state:
                            st.session_state["profile"] = {}
                        metadata = user.user_metadata or {}
                        st.session_state["profile"]["full_name"] = metadata.get("full_name", "")
                        st.session_state["profile"]["email"] = user.email or metadata.get("email", "")

                        st.rerun()
                    else:
                        st.error("Sign in failed. Please check your credentials.")
                except Exception as e:
                    st.error(f"Sign in error: {e}")

    # ---- REGISTER ----
    with tab_register:
        st.subheader("Create an account")

        reg_name = st.text_input("Name", key="reg_name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input(
            "Password",
            type="password",
            key="reg_password",
            help="Minimum 6 characters.",
        )
        reg_password_confirm = st.text_input(
            "Confirm password",
            type="password",
            key="reg_password_confirm",
        )

        if st.button("Register", key="btn_register", use_container_width=True):
            if not reg_name or not reg_email or not reg_password:
                st.warning("Please fill in all fields.")
            elif reg_password != reg_password_confirm:
                st.error("Passwords do not match.")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    response = supabase.auth.sign_up(
                        {
                            "email": reg_email,
                            "password": reg_password,
                            "options": {
                                "data": {
                                    "full_name": reg_name
                                }
                            },
                        }
                    )
                    user = response.user
                    if user:
                        try:
                            # Create Student row now so profile exists immediately
                            student_id = _get_or_create_student_for_user(user)
                            st.session_state["user"] = user
                            st.session_state["student_id"] = student_id
                        except Exception as e:
                            st.warning(f"Account created, but profile setup had an issue: {e}")

                        st.success(
                            f"Account created for {reg_name}. "
                            "Please check your email to confirm your account, then sign in."
                        )
                    else:
                        st.error("Registration failed. Please try again.")
                except Exception as e:
                    st.error(f"Registration error: {e}")

    return False


def sign_out():
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.pop("user", None)
    st.session_state.pop("student_id", None)
    st.session_state.pop("profile", None)
    st.rerun()