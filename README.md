# AI-Powered Study Planner (FYP)

![Status](https://img.shields.io/badge/status-WIP-orange)
![Python](https://img.shields.io/badge/Python-100%25-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-%23FF6B35.svg?&logo=streamlit&logoColor=white)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL3-yellow.svg)](https://www.gnu.org/licenses/gpl-3.0)

An AI-powered study planner that generates personalized, day‑by‑day study schedules based on your modules, deadlines, available time, and preferences. Built with Streamlit and Python, integrated with a local LLM (Ollama) and a SQL database for saving and tracking plans.

> ⚠️ This project is a **work in progress (WIP)**.  
> Features, UI, and the deployed app may change frequently as I continue developing and refining the system.

---

## 🌐 Live Demo

You can try the app online here:

👉 **[Open the live app](https://ai-study-planner-fyp.streamlit.app)**

No local setup needed – add your modules, deadlines, and availability in the browser and generate an AI‑powered study plan.

---

## ✨ Features

- **AI‑generated study plans** – Generate structured study schedules (e.g., daily blocks, priorities, topics) using a local Ollama model.
- **Module and task management** – Add modules, topics, and tasks with difficulty, estimated time, and due dates.
- **Time‑aware scheduling** – Plans respect your daily availability and upcoming exam/assignment deadlines to avoid overload.
- **Saved study plans** – Persist plans in a SQL database (from `schema.sql`) so you can revisit and update them later.
- **Streamlit web UI** – Clean, interactive interface split into multiple pages under the `pages/` directory.
- **Devcontainer support** – `.devcontainer` folder for a ready‑to‑use VS Code + Docker development environment.

---

## 🧱 Tech Stack

- **Frontend / UI:** Streamlit
- **Backend / Logic:** Python (`app.py`, `pages/`, `utils/`)
- **AI / LLM:** Ollama (local LLM, configurable model)
- **Database:** SQL database based on `schema.sql` (e.g., Postgres/Supabase‑style schema with a `StudyPlan` table)
- **Dev Environment:** VS Code Dev Containers, `requirements.txt` for dependencies

---

## 📁 Project Structure

```text
AI-Study-Planner-FYP/
├── app.py             # Main Streamlit entrypoint / router
├── pages/             # Multi-page Streamlit views
├── utils/             # Helper functions (LLM, DB, scheduling logic)
├── schema.sql         # Database schema (e.g., StudyPlan table)
├── requirements.txt   # Python dependencies
├── .devcontainer/     # Devcontainer configuration
├── .gitignore
├── LICENSE
└── README.md
```
