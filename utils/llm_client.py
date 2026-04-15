import json
from typing import List, Dict, Any
from datetime import date, timedelta, datetime
from groq import Groq
import streamlit as st


GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
MODEL_NAME = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)


def format_date(date_str: str) -> str:
    try:
        d = datetime.fromisoformat(date_str).date()
        return d.strftime("%d %b %Y")
    except Exception:
        return date_str


# Map "Mon", "Tue", ... to Python weekday numbers (Mon = 0)
_DAY_TO_WEEKDAY = {
    "Mon": 0,
    "Tue": 1,
    "Wed": 2,
    "Thu": 3,
    "Fri": 4,
    "Sat": 5,
    "Sun": 6,
}


def _next_n_study_dates(days_ahead: int, study_days: List[str]) -> List[date]:
    """
    Return up to `days_ahead` upcoming dates starting today that fall on the
    student's preferred study days. If study_days is empty, use consecutive days.
    """
    today = date.today()
    preferred_weekdays = [_DAY_TO_WEEKDAY[d] for d in study_days if d in _DAY_TO_WEEKDAY]

    dates: List[date] = []
    current = today
    limit = days_ahead * 7  # safety cap

    if not preferred_weekdays:
        # No preference: just consecutive days
        for i in range(days_ahead):
            dates.append(today + timedelta(days=i))
        return dates

    while len(dates) < days_ahead and limit > 0:
        if current.weekday() in preferred_weekdays:
            dates.append(current)
        current = current + timedelta(days=1)
        limit -= 1

    # If we still didn't get enough, fill remaining with consecutive days
    while len(dates) < days_ahead:
        dates.append(current)
        current = current + timedelta(days=1)

    return dates


def generate_study_plan(
    tasks: List[Dict[str, Any]],
    days_ahead: int = 7,
    study_days: List[str] | None = None,
) -> str:
    """
    Generate a study plan using the LLM.
    - ONLY uses the provided tasks (no invented tasks).
    - Schedules over upcoming dates that match student's preferred study_days.
    - Instructions explicitly forbid scheduling after each task's deadline.
    """
    if not tasks:
        return "You have no tasks that need work. All tasks are completed or overdue."

    if study_days is None:
        study_days = []

    task_lines = []
    for t in tasks:
        raw_deadline = t.get("deadline", "N/A")
        pretty_deadline = format_date(raw_deadline) if raw_deadline != "N/A" else "N/A"
        line = (
            f"- {t.get('title', '(no title)')} "
            f"(due {pretty_deadline}, "
            f"priority {t.get('priority', 'N/A')}, "
            f"status {t.get('status', 'N/A')}, "
            f"estimated {t.get('estimated_time', 'N/A')})"
        )
        task_lines.append(line)

    tasks_text = "\n".join(task_lines)

    plan_dates = _next_n_study_dates(days_ahead, study_days)
    plan_dates_text = "\n".join(
        f"- {d.strftime('%d %b %Y')} ({d.strftime('%a')})" for d in plan_dates
    )

    today = date.today()
    preferred_days_text = ", ".join(study_days) if study_days else "any day"

    prompt = f"""You are an AI study coach.
Today's date is {today.strftime('%d %b %Y')}.

The student has the following tasks (these are the ONLY tasks you may use):
{tasks_text}

The student prefers to study on: {preferred_days_text}.

Create a clear study plan that:
- uses ONLY the tasks listed above; do NOT invent any new tasks, modules, or deadlines,
- uses these specific dates (one section per date):
{plan_dates_text}
- for each date, assigns one or more of the listed tasks and roughly how many hours,
- NEVER schedules work on a task after its own deadline,
- focuses on earlier deadlines, aiming to finish tasks at least one day before the deadline,
- respects the student's preferred study days (do not invent other dates),
- is written as bullet points grouped by the actual date (e.g. "10 Apr 2026 (Fri)").

If a task's deadline has already passed, you MUST NOT schedule it on any future date.
If there are no tasks that need work on a given date, clearly say that the student can rest that day.
Do NOT create any tasks or deadlines that are not in the list above.
"""

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful AI study coach."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=1024,
        )

        content = completion.choices[0].message.content
        if not content:
            return "The model returned an empty response."

        return content.strip()

    except Exception as e:
        return f"Error talking to Groq API: {e}"


def generate_subtasks_with_llm(
    title: str,
    description: str,
    sessions: int = 5,
) -> List[str]:
    """
    Ask the LLM to propose a small list of subtask names for an assignment.
    Returns a list of short labels, length <= sessions.
    """
    if sessions <= 0:
        return []

    prompt = f"""You are an AI study coach helping a student break down one assignment.

Assignment title: "{title}"
Assignment description:
{description or "(no description provided)"}

Create a list of {sessions} short, concrete subtasks that the student can schedule on different days.
Each subtask should be a brief phrase like "Research sources", "Draft introduction", "Edit and proofread".

Return ONLY valid JSON: an array of strings, e.g.
["Research topic", "Plan outline", "Draft first version", "Revise", "Final checks"]"""

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful AI study coach."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=256,
        )

        content = completion.choices[0].message.content
        if not content:
            return []

        subtasks = json.loads(content)
        if isinstance(subtasks, list):
            subtasks = [str(s).strip() for s in subtasks if str(s).strip()]
            if len(subtasks) > sessions:
                subtasks = subtasks[:sessions]
            return subtasks
        return []
    except Exception:
        return []