import streamlit as st
import os, requests, json, datetime, time, re
import pytz

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="AmritAI v1.2 Fusion", page_icon="🧠", layout="wide")

GROQ_KEY = os.environ.get("GROQ_KEY")
SECRET_YOUTUBER_CODE = "chiku03"
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #1a1a2e, #16213e); color: white; }
    .main-card {
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(10px);
        border-radius: 15px; padding: 20px;
        border: 1px solid rgba(0, 242, 254, 0.2);
    }
    .amrit-title { color: #00f2fe; text-align: center; text-shadow: 0 0 15px #00f2fe; }
    .reasoning-box { background: rgba(0, 242, 254, 0.1); border-left: 5px solid #00f2fe; padding: 10px; font-style: italic; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "user_name" not in st.session_state: st.session_state.user_name = None
if "is_subscriber_mode" not in st.session_state: st.session_state.is_subscriber_mode = False
if "reasoning_enabled" not in st.session_state: st.session_state.reason_enabled = False

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 class='amrit-title'>🚀 AmritAI v1.2</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_name:
        name = st.text_input("Apna naam likho:")
        if st.button("Access 🔑"):
            st.session_state.user_name = name
            st.rerun()
    else:
        st.success(f"User: **{st.session_state.user_name}**")
        
        # --- REASONING TOGGLE ---
        st.divider()
        st.subheader("🧠 Brain Power")
        reason_on = st.toggle("Reasoning Mode (Deep Think)", value=st.session_state.reason_enabled)
        st.session_state.reason_enabled = reason_on
        
        if reason_on:
            st.info("AI ab har cheez ko step-by-step sochega.")
        
        st.divider()
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        if st.button("🚪 Logout"):
            st.session_state.user_name = None
            st.rerun()

# --- 4. MAIN CONTENT ---
if not st.session_state.user_name:
    st.markdown("<div class='main-card'><h2 style='text-align:center;'>🤖 Welcome to AmritAI Fusion</h2><p style='text-align:center;'>Login karke Reasoning Mode ON karo!</p></div>", unsafe_allow_html=True)
else:
    st.markdown(f"<h3 class='amrit-title'>💬 Smart Chat Engine</h3>", unsafe_allow_html=True)
    
    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("AmritAI se logical baat karo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        with st.chat_message("assistant"):
            try:
                # ADVANCED REASONING PROMPT
                sys_p = "You are AmritAI, built by Amrit Pathak. Speak in Hinglish."
                
                if st.session_state.reason_enabled:
                    sys_p += """ 
                    REASONING MODE ACTIVE: 
                    1. Before answering, break down the problem logically.
                    2. Use step-by-step thinking.
                    3. For math/coding, explain the logic first.
                    4. Always try to find the most efficient solution.
                    """
                
                if st.session_state.is_subscriber_mode:
                    sys_p += " Personality: Energetic YouTuber style."

                headers = {"Authorization": f"Bearer {GROQ_KEY}"}
                payload = {
                    "model": "llama-3.3-70b-versatile", # 70B model reasoning ke liye best hai
                    "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages],
                    "temperature": 0.6 if st.session_state.reason_enabled else 0.8
                }
                
                with st.spinner("🤔 Thinking deeply..." if st.session_state.reason_enabled else "AI is typing..."):
                    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    ans = res.json()["choices"][0]["message"]["content"]
                    
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
            except:
                st.error("API Error! Key check karo bhai.")
