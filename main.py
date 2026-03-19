import streamlit as st
import os, requests, json, datetime, time, re
import pytz

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="AmritAI v1.1 Fusion", page_icon="🤖", layout="wide")

GROQ_KEY = os.environ.get("GROQ_KEY")
SECRET_YOUTUBER_CODE = "chiku03"
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; }
    .main-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        border-radius: 15px; padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .amrit-title { color: #00f2fe; text-align: center; text-shadow: 0 0 15px #00f2fe; font-family: 'Trebuchet MS'; }
    .stButton>button { border-radius: 20px; background: #00f2fe; color: black; font-weight: bold; width: 100%; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px #00f2fe; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INTELLIGENT HELPERS ---
def get_smart_greeting():
    now = datetime.datetime.now(IST)
    hour = now.hour
    if 5 <= hour < 12:
        return "🌅 Good Morning, Amrit! Aaj kya naya build karna hai?"
    elif 12 <= hour < 17:
        return "☀️ Good Afternoon! Kaise chal rahi hai coding?"
    elif 17 <= hour < 21:
        return "🌆 Good Evening! Chai-vibe aur AI, perfect combination."
    else:
        return "🌙 Late Night Session? AmritAI is active!"

# --- 3. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "tasks" not in st.session_state: st.session_state.tasks = []
if "user_name" not in st.session_state: st.session_state.user_name = None
if "is_subscriber_mode" not in st.session_state: st.session_state.is_subscriber_mode = False
# AI Persona ko thoda intelligent aur "Witty" banaya hai
if "persona" not in st.session_state: 
    st.session_state.persona = """You are AmritAI v1.1 Fusion, an intelligent and witty AI built by Amrit Pathak. 
    Speak in a mix of Hindi and English (Hinglish). Be helpful, creative, and sometimes crack jokes. 
    If someone asks who made you, proudly say Amrit Pathak. If subscriber mode is OFF, be a professional friend."""

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 class='amrit-title'>🚀 AmritAI Lab</h1>", unsafe_allow_html=True)
    st.caption("v1.1 Fusion | Smart Edition")
    
    if not st.session_state.user_name:
        name = st.text_input("Apna naam likho:", key="login_name")
        if st.button("Enter AI Zone 🔑"):
            if name:
                st.session_state.user_name = name
                st.rerun()
    else:
        st.success(f"Logged in as: **{st.session_state.user_name}**")
        if st.session_state.is_subscriber_mode:
            st.warning("🔥 SUBSCRIBER MODE: ON")
        
        st.divider()
        menu = st.radio("Navigation:", ["💬 Smart Chat", "🎯 My Tasks", "⚙️ Brain Settings"])
        
        if st.button("🚪 Logout"):
            st.session_state.user_name = None
            st.session_state.messages = []
            st.rerun()

# --- 5. MAIN CONTENT ---

if not st.session_state.user_name:
    st.markdown(f"<div class='main-card'><h2 style='text-align:center;'>🤖 Welcome to AmritAI</h2><p style='text-align:center;'>{get_smart_greeting()}</p></div>", unsafe_allow_html=True)

elif menu == "🎯 My Tasks":
    st.header("🎯 Task Manager")
    col1, col2 = st.columns([0.8, 0.2])
    t_input = col1.text_input("Homework ya project task likho...")
    if col2.button("Add") and t_input:
        st.session_state.tasks.append(t_input)
        st.rerun()
    
    for i, t in enumerate(st.session_state.tasks):
        st.write(f"✅ {t}")
    if st.button("Clear All"): st.session_state.tasks = []; st.rerun()

elif menu == "⚙️ Brain Settings":
    st.header("⚙️ AI Intelligence Control")
    st.write("Yahan se tum AI ka behavior modify kar sakte ho.")
    new_p = st.text_area("Update System Instructions:", value=st.session_state.persona, height=150)
    if st.button("Update Intelligence"):
        st.session_state.persona = new_p
        st.success("Brain Updated! Ab AI naye tarike se sochega.")

else: # SMART CHAT ENGINE
    st.markdown(f"<h3 style='text-align:center;'>{get_smart_greeting()}</h3>", unsafe_allow_html=True)
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("AmritAI se kuch pucho..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        # Commands Check
        if prompt.lower().startswith("/secret"):
            code = prompt.replace("/secret", "").strip()
            with st.chat_message("assistant"):
                if code == SECRET_YOUTUBER_CODE:
                    st.session_state.is_subscriber_mode = True
                    resp = "🔥 OP Bhai! Subscriber mode ON! Ab system YouTuber style mein response dega. Gajab!"
                else:
                    resp = "❌ Galat code! Sahi secret try karo."
                st.write(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})

        elif prompt.lower() == "/clear":
            st.session_state.messages = []
            st.rerun()

        else:
            # GROQ INTELLIGENCE CALL
            with st.chat_message("assistant"):
                try:
                    sys_p = st.session_state.persona
                    if st.session_state.is_subscriber_mode:
                        sys_p += " Current Mode: Energetic Indian YouTuber. Use slang like 'Op', 'Bhai', 'Bawa'."

                    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
                    payload = {
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages]
                    }
                    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    ans = res.json()["choices"][0]["message"]["content"]
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                except:
                    st.error("API Error! Secrets mein key check karo.")
