# 🚀 AI-Powered Skill Assessment & Learning Plan Agent

**Verify technical proficiency, identify skill gaps, and bridge them with AI.**

A resume tells you what someone *claims* to know—not how well they actually know it. This project is a dual-portal AI agent designed to take a Job Description and a candidate's resume, conversationally assess real proficiency through scenario-based questioning, and generate a personalized learning plan complete with curated resources and time estimates.

---

## ✨ Key Features

### 👨‍💼 Interviewer / Admin Dashboard
* **Dynamic Job Profiles:** Create and manage specific job roles. The AI uses these descriptions to benchmark candidate performance.
* **Global Assessment Control:** Set the number of questions per interview and define strict time limits (e.g., 60 seconds per response).
* **Editable AI Logic:** Modify the core system prompt directly from the UI to change the AI's personality or interviewing style.
* **Result Management:** View detailed evaluation reports for every candidate and delete past records as needed.

### 👩‍💻 Candidate Portal
* **Automated Resume Parsing:** Upload a PDF resume; the AI extracts relevant skills and prepares a custom assessment on the fly.
* **Live Pressure Timer:** A real-time JavaScript countdown timer creates a realistic interview environment.
* **Smart Evaluation:** If a candidate exceeds the time limit, the system silently flags the delay to the grading engine to dock points for speed.
* **Personalized Roadmap:** At the end of the session, candidates receive a score out of 5 for each skill and a bulleted learning plan with timeframes and resources.

---

## 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/)
* **AI Orchestration:** [LangChain](https://www.langchain.com/)
* **LLM:** Google Gemini 2.0 / 1.5 Flash
* **Document Parsing:** `pypdf` (LangChain PyPDFLoader)
* **Storage:** Local JSON (for Hackathon MVP simplicity)

---

## 📂 Project Structure

- `app.py`: The main application file handling UI routing, state management, and the dashboard logic.
- `chains.py`: The backend logic containing LangChain execution chains for skill extraction and interview responses.
- `prompts.py`: Centralized prompt management for skill extraction and final report generation.
- `requirements.txt`: List of all Python dependencies.
- `database.json`: Local storage for job roles, settings, and interview results.

---

## 🚀 How to Run Locally

Follow these steps to set up the project on any operating system (**Windows, macOS, or Linux**).

### 1. Prerequisites
* **Python 3.9+**
* A **Google Gemini API Key** (Get one for free at [Google AI Studio](https://aistudio.google.com/))

### 2. Installation
```bash
# Clone the repository
git clone [https://github.com/SomeshPadiyar/AI-Skill_Assessment_DeccanAI.git](https://github.com/SomeshPadiyar/AI-Skill_Assessment_DeccanAI.git)
cd AI-Skill_Assessment_DeccanAI

# Create a virtual environment
# macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# Windows:
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
