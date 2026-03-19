import streamlit as st
import os, requests, json, datetime, time, re
import pytz

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="AmritAI v1.1 Fusion", page_icon="🛡️", layout="wide")

GROQ_KEY = os.environ.get("GROQ_KEY")
SECRET_YOUTUBER_CODE = "chiku03"
IST = pytz.timezone('Asia/Kolkata')

# Professional Dark Theme CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; }
    .main-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px; padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .amrit-title { color: #00f2fe; text-align: center; text-shadow: 0 0 15px #00f2fe; }
    .stButton>button { border-radius: 20px; background: #00f2fe; color: black; font-weight: bold; width: 100%; }
    code { color: #ff79c6 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "tasks" not in st.session_state: st.session_state.tasks = []
if "user_name" not in st.session_state: st.session_state.user_name = None
if "is_subscriber_mode" not in st.session_state: st.session_state.is_subscriber_mode = False

# --- 3. HELPER FUNCTIONS ---
def get_custom_greeting():
    now = datetime.datetime.now(IST)
    hour = now.hour
    if 5 <= hour < 12: return "Good Morning ☀️"
    elif 12 <= hour < 17: return "Good Afternoon 🌤️"
    elif 17 <= hour < 21: return "Good Evening 🌆"
    else: return "Good Night 🌙"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 class='amrit-title'>🚀 AmritAI Lab</h1>", unsafe_allow_html=True)
    st.caption("v1.1 Fusion | Coding Pro Edition")
    
    if not st.session_state.user_name:
        name = st.text_input("Enter your name:")
        if st.button("Access 🔑"):
            st.session_state.user_name = name
            st.rerun()
    else:
        st.success(f"User: **{st.session_state.user_name}**")
        if st.session_state.is_subscriber_mode:
            st.warning("🔥 SUBSCRIBER MODE: ON")
        
        st.divider()
        menu = st.radio("Navigation:", ["💬 Coding Engine", "🎯 My Tasks"])
        
        if st.button("🚪 Logout"):
            st.session_state.user_name = None
            st.session_state.messages = []
            st.rerun()

# --- 5. MAIN CONTENT ---

if not st.session_state.user_name:
    st.markdown(f"<div class='main-card'><h2 style='text-align:center;'>🤖 Welcome to AmritAI v1.1</h2><p style='text-align:center;'>Bhai, login karke coding shuru karo!</p></div>", unsafe_allow_html=True)

elif menu == "🎯 My Tasks":
    st.header("🎯 Task Manager")
    col1, col2 = st.columns([0.8, 0.2])
    t_input = col1.text_input("Add a new task...")
    if col2.button("Add") and t_input:
        st.session_state.tasks.append(t_input)
        st.rerun()
    for t in st.session_state.tasks: st.write(f"✅ {t}")
    if st.button("Clear All"): st.session_state.tasks = []; st.rerun()

else: # CODING ENGINE
    greeting = get_custom_greeting()
    st.markdown(f"<h2 class='amrit-title'>{greeting}, {st.session_state.user_name}!</h2>", unsafe_allow_html=True)
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("Write code or ask a doubt..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        # Commands
        if prompt.lower().startswith("/secret"):
            code = prompt.replace("/secret", "").strip()
            with st.chat_message("assistant"):
                if code == SECRET_YOUTUBER_CODE:
                    st.session_state.is_subscriber_mode = True
                    resp = "🔥 OP Bhai! Coding Mode + YouTuber Swag Activated!"
                else:
                    resp = "❌ Code galat hai!"
                st.write(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})

        elif prompt.lower() == "/clear":
            st.session_state.messages = []
            st.rerun()

        else:
            with st.chat_message("assistant"):
                try:
                    # PRO CODING PERSONA (Claude/Gemini Style)
                    sys_p = """You are AmritAI v1.1 Fusion, an elite coding expert built by Amrit Pathak. 
                    Your coding skills are on par with Claude 3.5 and Gemini 1.5 Pro. 
                    1. Write clean, efficient, and well-commented code.
                    2. Explain logic step-by-step.
                    3. If there is a bug, find it and fix it immediately.
                    4. Speak in Hinglish but keep technical terms in English.
                    5. Use Markdown for code blocks."""
                    
                    if st.session_state.is_subscriber_mode:
                        sys_p += " Also, add a bit of YouTuber swag like 'Bhai' and 'Op' in your explanations."

                    headers = {"Authorization": f"Bearer {GROQ_KEY}"}
                    payload = {
                        "model": "llama-3.3-70b-versatile", # One of the best for coding
                        "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages]
                    }
                    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    ans = res.json()["choices"][0]["message"]["content"]
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                except:
                    st.error("API Error! Key check karo.")
