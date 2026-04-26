import streamlit as st
import streamlit.components.v1 as components
import tempfile
import uuid
import json
import os
import time
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from chains import extract_skills, get_interview_chain, generate_report
from google.api_core.exceptions import ResourceExhausted

# --- 1. CONFIG & PREMIUM UI STYLING ---
st.set_page_config(page_title="AI Skill Assessor", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .css-1d391kg { background-color: #161A22; }
    .skill-badge {
        background-color: #238636;
        color: white;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.85em;
        margin-right: 6px;
        font-weight: 600;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE MANAGEMENT ---
DB_FILE = "database.json"

DEFAULT_SYSTEM_PROMPT = """You are an expert technical interviewer. Assess the candidate on EXACTLY these skills: {skills_to_test}. 
Ask ONE practical, scenario-based question at a time. Wait for the user's answer. 
Do not give them the answer. Acknowledge their response briefly, then ask the next question about the next skill. 
STOP asking questions immediately once you have asked about all the specified skills. Say 'INTERVIEW COMPLETE' when done."""

def init_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "settings": {
                "num_questions": 3,
                "time_limit_seconds": 60,
                "system_prompt": DEFAULT_SYSTEM_PROMPT,
                "job_roles": {
                    "Software Engineer": "General SWE role. Requires algorithms, data structures, and system design.",
                    "Data Engineer": "Focus on data pipelines, Kafka, PySpark, and distributed systems."
                }
            },
            "sessions": []
        }
        with open(DB_FILE, "w") as f:
            json.dump(default_data, f, indent=4)

def load_db():
    init_db()
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_db()

# DB Migration for existing DBs
if "system_prompt" not in db["settings"]:
    db["settings"]["system_prompt"] = DEFAULT_SYSTEM_PROMPT
    save_db(db)

# --- 3. SESSION STATE ---
if "view" not in st.session_state:
    st.session_state.view = "landing" 

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.skills_to_test = []
    st.session_state.turn_count = 0
    st.session_state.messages = []
    st.session_state.candidate_name = ""
    st.session_state.selected_role = ""
    st.session_state.question_start_time = None

def navigate_to(view_name):
    st.session_state.view = view_name
    st.rerun()

# --- 4. JS TIMER COMPONENT ---
def render_live_timer(time_limit):
    js_code = f"""
    <div id="timer_box" style="padding:10px; background-color:#1E2127; border: 1px solid #30363D; border-radius: 8px; text-align: center; color: white; font-family: sans-serif;">
        <h2 id="timer_text" style="margin:0; font-weight:600;">⏱️ {time_limit}s Remaining</h2>
    </div>
    <script>
        var timeLeft = {time_limit};
        var elem = document.getElementById('timer_text');
        var box = document.getElementById('timer_box');
        
        var timerId = setInterval(function() {{
            timeLeft--;
            if (timeLeft > 10) {{
                elem.innerHTML = "⏱️ " + timeLeft + "s Remaining";
            }} else if (timeLeft > 0) {{
                elem.innerHTML = "⚠️ " + timeLeft + "s Remaining";
                elem.style.color = "#FF4B4B";
            }} else {{
                clearInterval(timerId);
                elem.innerHTML = "🛑 TIME IS UP! Press Enter to Submit.";
                elem.style.color = "#FF4B4B";
                box.style.borderColor = "#FF4B4B";
            }}
        }}, 1000);
    </script>
    """
    components.html(js_code, height=80)

# ==========================================
# VIEW: LANDING PAGE
# ==========================================
if st.session_state.view == "landing":
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>Welcome to the Assessment Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8B949E;'>Select your role to continue.</p><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            # Navigates directly to the dashboard, skipping login
            if st.button("👨‍💼 I am an Interviewer", use_container_width=True): navigate_to("admin_dash")
            st.write("")
            if st.button("👩‍💻 I am a Candidate", use_container_width=True, type="primary"): navigate_to("candidate_form")
            
    st.markdown("""
        <div style='position: fixed; bottom: 20px; right: 25px; color: #8B949E; font-size: 20px; font-weight: 600; letter-spacing: 0.5px;'>
            by - Somesh Padiyar
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# VIEW: ADMIN DASHBOARD
# ==========================================
elif st.session_state.view == "admin_dash":
    st.sidebar.title("👨‍💼 Admin Panel")
    # Updated to a "Back to Home" button
    if st.sidebar.button("← Back to Home"):
        navigate_to("landing")
        
    st.title("Interviewer Dashboard")
    tab1, tab2 = st.tabs(["📊 Assessment Results", "⚙️ Platform Settings"])
    
    with tab1:
        if not db["sessions"]: 
            st.info("No candidates have completed assessments yet.")
        else:
            for s in reversed(db["sessions"]):
                with st.container(border=True):
                    st.markdown(f"### {s['candidate_name']} <span style='font-size: 0.6em; color: #8B949E;'>| Role: {s['job_role']}</span>", unsafe_allow_html=True)
                    skills_html = ', '.join([f"<span class='skill-badge'>{skill}</span>" for skill in s['skills']])
                    st.markdown(f"<p><b>Target Skills:</b> {skills_html}</p>", unsafe_allow_html=True)
                    
                    with st.expander("✅ View Final Assessment Report"):
                        st.markdown(s['report'])
                    
                    if st.button("🗑️ Delete Record", key=f"del_sess_{s['id']}"):
                        db["sessions"] = [sess for sess in db["sessions"] if sess['id'] != s['id']]
                        save_db(db)
                        st.rerun()

    with tab2:
        st.subheader("Global Settings")
        col_s1, col_s2 = st.columns(2)
        with col_s1: new_num = st.number_input("Questions per Assessment", min_value=1, max_value=10, value=db["settings"]["num_questions"])
        with col_s2: new_time = st.number_input("Time Limit per Question (Seconds)", min_value=15, max_value=300, value=db["settings"]["time_limit_seconds"])
        
        st.markdown("**Core Interview AI Instructions (System Prompt)**")
        new_prompt = st.text_area("Edit how the AI acts (Use {skills_to_test} to inject the skills)", value=db["settings"]["system_prompt"], height=150)
            
        if st.button("Save Global Settings", type="primary"):
            db["settings"]["num_questions"] = new_num
            db["settings"]["time_limit_seconds"] = new_time
            db["settings"]["system_prompt"] = new_prompt
            save_db(db)
            st.success("Settings updated!")
            st.rerun()
            
        st.write("---")
        st.subheader("Manage Job Profiles")
        
        st.markdown("Expand a role below to edit its title and description, or delete it.")
        for role_name, role_desc in list(db["settings"]["job_roles"].items()):
            with st.expander(f"⚙️ {role_name}"):
                edit_name = st.text_input("Job Title", value=role_name, key=f"name_{role_name}")
                edit_desc = st.text_area("Job Description (The AI uses this to find skill gaps)", value=role_desc, key=f"desc_{role_name}", height=100)
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    if st.button("💾 Save Changes", key=f"save_{role_name}"):
                        if edit_name != role_name:
                            del db["settings"]["job_roles"][role_name]
                        db["settings"]["job_roles"][edit_name] = edit_desc
                        save_db(db)
                        st.success("Profile updated!")
                        st.rerun()
                with col_btn2:
                    if st.button("🗑️ Delete Role", key=f"del_{role_name}"):
                        if len(db["settings"]["job_roles"]) > 1:
                            del db["settings"]["job_roles"][role_name]
                            save_db(db)
                            st.rerun()
                        else:
                            st.error("You must keep at least one job profile.")
                            
        st.write("---")
        st.markdown("**Add New Role**")
        col_new1, col_new2 = st.columns(2)
        with col_new1: new_role_name = st.text_input("New Job Title", key="new_role_title")
        with col_new2: new_role_desc = st.text_area("Job Description / Requirements", key="new_role_desc")
        if st.button("➕ Add Job Role"):
            if new_role_name and new_role_desc:
                db["settings"]["job_roles"][new_role_name] = new_role_desc
                save_db(db)
                st.success(f"Added {new_role_name}!")
                st.rerun()

# ==========================================
# VIEW: CANDIDATE FORM
# ==========================================
elif st.session_state.view == "candidate_form":
    st.button("← Back to Home", on_click=lambda: navigate_to("landing"))
    st.title("Candidate Assessment Intake")
    
    with st.container(border=True):
        candidate_name = st.text_input("Full Name")
        selected_role = st.selectbox("Select Job Profile", list(db["settings"]["job_roles"].keys()))
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
        
        if st.button("Start Assessment", type="primary", use_container_width=True):
            if candidate_name and uploaded_file:
                st.session_state.candidate_name = candidate_name
                st.session_state.selected_role = selected_role
                with st.spinner("Analyzing resume and preparing custom assessment..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        temp_file_path = temp_file.name
                    
                    loader = PyPDFLoader(temp_file_path)
                    docs = loader.load()
                    resume_text = " ".join([doc.page_content for doc in docs])
                    st.session_state.resume_text = resume_text 
                    
                    try:
                        num_q = db["settings"]["num_questions"]
                        skills = extract_skills(db["settings"]["job_roles"][selected_role], resume_text, num_q)
                        
                        skills = skills[:num_q] 
                        st.session_state.skills_to_test = skills
                        
                        interview_chain = get_interview_chain(db["settings"]["system_prompt"])
                        initial_response = interview_chain.invoke(
                            {"skills_to_test": ", ".join(skills), "user_input": "Start the interview."},
                            config={"configurable": {"session_id": st.session_state.session_id}}
                        )
                        st.session_state.messages.append({"role": "assistant", "content": initial_response})
                        st.session_state.question_start_time = time.time()
                        navigate_to("interview")
                    except ResourceExhausted:
                        st.error("⚠️ API limit! Wait 60s.")
            else: st.warning("Please enter your name and upload a resume.")

# ==========================================
# VIEW: CANDIDATE INTERVIEW
# ==========================================
elif st.session_state.view == "interview":
    st.title("💬 Technical Interview")
    st.caption(f"Candidate: {st.session_state.candidate_name} | Role: {st.session_state.selected_role}")
    st.markdown("---")
    
    limit_sec = db["settings"]["time_limit_seconds"]
    num_q = db["settings"]["num_questions"]
    
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
            
    if st.session_state.turn_count < num_q:
        
        render_live_timer(limit_sec)
        
        user_input = st.chat_input("Type your answer here...")
        
        if user_input:
            time_taken = int(time.time() - st.session_state.question_start_time)
            
            if time_taken > (limit_sec + 5):
                system_note = f"\n\n[SYSTEM EVALUATION NOTE: The candidate took {time_taken} seconds, exceeding the {limit_sec}s limit. Deduct points for speed.]"
            else:
                system_note = ""
            
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.chat_message("user").write(user_input)
            
            with st.spinner("Evaluating response..."):
                try:
                    interview_chain = get_interview_chain(db["settings"]["system_prompt"])
                    response = interview_chain.invoke(
                        {"skills_to_test": ", ".join(st.session_state.skills_to_test), "user_input": user_input + system_note},
                        config={"configurable": {"session_id": st.session_state.session_id}}
                    )
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.turn_count += 1
                    st.session_state.question_start_time = time.time() 
                    st.rerun() 
                    
                except ResourceExhausted:
                    st.error("⚠️ API rate limit reached. Please wait 60 seconds.")
                    
    else:
        st.success("✅ Assessment Complete! No further questions.")
        if st.button("Submit Assessment & Generate Results", type="primary"):
            with st.spinner("Finalizing results..."):
                report = generate_report(st.session_state.session_id)
                session_data = {
                    "id": st.session_state.session_id,
                    "candidate_name": st.session_state.candidate_name,
                    "job_role": st.session_state.selected_role,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "skills": st.session_state.skills_to_test,
                    "report": report
                }
                db["sessions"].append(session_data)
                save_db(db)
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.skills_to_test = []
                st.session_state.turn_count = 0
                st.session_state.messages = []
                st.session_state.question_start_time = None
                navigate_to("landing")