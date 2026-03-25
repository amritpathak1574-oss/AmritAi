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
    .amrit-title { color: #00f2fe; text-align: center; text-shadow: 0 0 15px #00f2fe; }
    .thinking-box { background: rgba(0, 242, 254, 0.05); border-radius: 10px; padding: 15px; border-left: 4px solid #00f2fe; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "user_name" not in st.session_state: st.session_state.user_name = None
if "is_subscriber_mode" not in st.session_state: st.session_state.is_subscriber_mode = False
if "reasoning_on" not in st.session_state: st.session_state.reasoning_on = False

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 class='amrit-title'>🚀 AmritAI Lab</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_name:
        u_name = st.text_input("Enter Name:")
        if st.button("Login 🔑"):
            st.session_state.user_name = u_name
            st.rerun()
    else:
        st.success(f"Hi, **{st.session_state.user_name}**!")
        
        st.divider()
        st.subheader("🧠 Intelligence")
        # Reasoning Toggle
        reason_val = st.toggle("Chain of Thought (CoT)", value=st.session_state.reasoning_on)
        st.session_state.reasoning_on = reason_val
        
        if reason_val:
            st.info("AI ab 'Deep Thinking' mode mein hai.")
        
        st.divider()
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        if st.button("🚪 Logout"):
            st.session_state.user_name = None
            st.rerun()

# --- 4. CHAT INTERFACE ---
if not st.session_state.user_name:
    st.info("Bhai, login kar lo sidebar se!")
else:
    st.markdown(f"<h3 class='amrit-title'>💬 Smart Chat Engine</h3>", unsafe_allow_html=True)

    # Show History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("AmritAI se logical sawaal pucho..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        with st.chat_message("assistant"):
            try:
                # ADVANCED SYSTEM PROMPT
                sys_p = "You are AmritAI, built by Amrit Pathak. Speak in Hinglish."
                
                if st.session_state.reasoning_on:
                    # AI ko instructions di hain ki wo 'THOUGHT:' tag use kare
                    sys_p += """
                    ULTRA REASONING MODE:
                    1. Pehle 'THOUGHT:' tag ke andar apni step-by-step logic aur reasoning likho.
                    2. Dekho ki sawal mein koi trick (jaise 'survivors' wala point) toh nahi hai.
                    3. Phir 'FINAL ANSWER:' tag ke baad main jawab do.
                    4. Be logical and super smart.
                    """
                
                if st.session_state.is_subscriber_mode:
                    sys_p += " Personality: Energetic YouTuber."

                headers = {"Authorization": f"Bearer {GROQ_KEY}"}
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages],
                    "temperature": 0.5 if st.session_state.reasoning_on else 0.8
                }

                with st.spinner("🤔 Analyzing Logic..."):
                    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    full_response = res.json()["choices"][0]["message"]["content"]

                    # --- CHAIN OF THOUGHT LOGIC ---
                    if st.session_state.reasoning_on and "THOUGHT:" in full_response:
                        # Thought aur Final Answer ko alag karna
                        parts = full_response.split("FINAL ANSWER:")
                        thought_part = parts[0].replace("THOUGHT:", "").strip()
                        final_part = parts[1].strip() if len(parts) > 1 else "Error processing logic."
                        
                        # Expandable box for Thought process
                        with st.expander("👁️ View AI's Thought Process", expanded=True):
                            st.markdown(f"<div class='thinking-box'>{thought_part}</div>", unsafe_allow_html=True)
                        
                        st.write(final_part)
                        st.session_state.messages.append({"role": "assistant", "content": final_part})
                    else:
                        st.write(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"⚠️ Error: {e}. Key check karo bhai.")
