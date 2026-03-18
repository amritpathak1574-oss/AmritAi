import streamlit as st
import os, requests, json, datetime, time, re
import pytz

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="AmritAI v1 Fusion", page_icon="🛡️", layout="wide")

GROQ_KEY = os.environ.get("GROQ_KEY")
SECRET_YOUTUBER_CODE = "chiku03" # Tumhara secret code
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; }
    .festive-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px; padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .amrit-title { color: #00f2fe; text-align: center; text-shadow: 0 0 10px #00f2fe; font-family: 'Trebuchet MS'; }
    .stButton>button { border-radius: 20px; background: #00f2fe; color: black; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "tasks" not in st.session_state: st.session_state.tasks = []
if "user_name" not in st.session_state: st.session_state.user_name = None
if "is_subscriber_mode" not in st.session_state: st.session_state.is_subscriber_mode = False
if "persona" not in st.session_state: 
    st.session_state.persona = "You are AmritAI, a witty, helpful AI built by Amrit Pathak. Speak in Hinglish."

# --- 3. HELPER FUNCTIONS ---
def get_greeting():
    hour = datetime.datetime.now(IST).hour
    if 5 <= hour < 12: return "Good Morning ☀️"
    elif 12 <= hour < 17: return "Good Afternoon 🌤️"
    else: return "Good Evening 🌆"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 class='amrit-title'>🚀 AmritAI Lab</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_name:
        name = st.text_input("Enter your name to start:")
        if st.button("Access AI 🔑"):
            st.session_state.user_name = name
            st.rerun()
    else:
        st.success(f"Logged in as: **{st.session_state.user_name}**")
        if st.session_state.is_subscriber_mode:
            st.warning("🔥 SUBSCRIBER MODE ACTIVE")
        
        st.divider()
        menu = st.radio("Navigation:", ["💬 Chat Engine", "🎯 My Tasks", "🛠️ Custom Persona"])
        
        if st.button("🚪 Logout"):
            st.session_state.user_name = None
            st.session_state.messages = []
            st.rerun()

# --- 5. MAIN LOGIC ---

if not st.session_state.user_name:
    st.info("Sidebar mein apna naam likh kar login karo, Amrit!")

elif menu == "🎯 My Tasks":
    st.header("🎯 To-Do Manager")
    col1, col2 = st.columns([0.8, 0.2])
    t_input = col1.text_input("New Task...")
    if col2.button("Add") and t_input:
        st.session_state.tasks.append(t_input)
        st.rerun()
    
    for i, t in enumerate(st.session_state.tasks):
        st.write(f"✅ {t}")
    if st.button("Clear Completed"): st.session_state.tasks = []; st.rerun()

elif menu == "🛠️ Custom Persona":
    st.header("🛠️ Bot Personality")
    new_p = st.text_area("AI ko kaise behave karna chahiye?", value=st.session_state.persona)
    if st.button("Update Persona"):
        st.session_state.persona = new_p
        st.success("AI updated!")

else: # CHAT ENGINE
    st.markdown(f"### {get_greeting()} {st.session_state.user_name}!")
    
    # Show History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("Message AmritAI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        # CHECK FOR COMMANDS
        if prompt.lower().startswith("/secret"):
            code = prompt.replace("/secret", "").strip()
            with st.chat_message("assistant"):
                if code == SECRET_YOUTUBER_CODE:
                    st.session_state.is_subscriber_mode = True
                    resp = "🔥 Subscriber Mode ON! Ab AmritAI ekdum YouTuber style mein baat karega. Swagat hai, Bhai!"
                else:
                    resp = "❌ Galat code! Sahi secret code use karo."
                st.write(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})

        elif prompt.lower() == "/clear":
            st.session_state.messages = []
            st.rerun()

        else:
            # AI RESPONSE
            with st.chat_message("assistant"):
                try:
                    # Subscriber mode logic
                    sys_p = st.session_state.persona
                    if st.session_state.is_subscriber_mode:
                        sys_p += " Mode: Energetic YouTuber, use slang like 'Bhai', 'Op', 'Gajab'."

                    headers = {"Authorization": f"Bearer {GROQ_KEY}"}
                    payload = {
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": sys_p},
                            *st.session_state.messages
                        ]
                    }
                    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    ans = res.json()["choices"][0]["message"]["content"]
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                except:
                    st.error("API Error! Secrets mein GROQ_KEY check karo.")
