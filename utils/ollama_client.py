import requests
from datetime import date, timedelta

# Ollama model initialisation
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

# 
def generate_study_plan(tasks, days_ahead=7):
    if not tasks:
        return "You have no tasks yet. Add some tasks first so I can create a study plan."

    task_lines = []
    for t in tasks:
        line = (
            f"- {t.get('title','(no title)')} "
            f"(due {t.get('deadline','N/A')}, "
            f"priority {t.get('priority','N/A')}, "
            f"status {t.get('status','N/A')}, "
            f"estimated {t.get('estimated_time','N/A')})"
        )
        task_lines.append(line)
    tasks_text = "\n".join(task_lines)


    today = date.today()
    plan_dates = [today + timedelta(days=i) for i in range(days_ahead)]

    plan_dates_text = "\n".join(
        f"- {d.isoformat()} ({d.strftime('%a')})" for d in plan_dates
    )

    prompt = f"""
You are an AI study coach.

Today's date is {today.isoformat()}.

The student has the following tasks:
{tasks_text}

Create a clear study plan that:
- uses these specific dates for the next {days_ahead} days (one section per date):
{plan_dates_text}
- for each date, list which tasks to work on and roughly how many hours,
- focuses on earlier deadlines, aim on finishing tasks a day before the deadline.
- is written as bullet points grouped by the actual date (e.g. "2026-03-06 (Fri)").

Do NOT use generic labels like "Day 1" or "Day 2". Always use the real calendar dates above.
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        #"stream": False,
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip() or "No plan text returned by the model."
    except Exception as e:
        return f"Error talking to the LLM: {e}"
