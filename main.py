import streamlit as st
import os, requests, json, datetime, time
import pytz

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="AmritAI v1.4 Desi Fusion", page_icon="🔥", layout="wide")

GROQ_KEY = os.environ.get("GROQ_KEY")
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d); color: white; }
    .desi-card {
        background: rgba(0, 0, 0, 0.6);
        border-radius: 15px; padding: 20px;
        border: 2px solid #fdbb2d;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .amrit-title { 
        font-family: 'Courier New', monospace;
        color: #fdbb2d; text-align: center; font-size: 45px; font-weight: bold;
        text-shadow: 3px 3px 0px #b21f1f;
    }
    .thinking-box { 
        background: rgba(253, 187, 45, 0.1); 
        border-left: 5px solid #fdbb2d; 
        padding: 15px; font-style: italic; color: #fdbb2d;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "bhojpuri_mode" not in st.session_state: st.session_state.bhojpuri_mode = False

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#fdbb2d;'>🚩 AmritAI Desi</h1>", unsafe_allow_html=True)
    st.divider()
    
    st.subheader("⚙️ System Settings")
    # THE BEST UPDATE: BHOJPURI TOGGLE
    b_mode = st.toggle("🪕 Bhojpuri Mode (Desi Style)", value=st.session_state.bhojpuri_mode)
    st.session_state.bhojpuri_mode = b_mode
    
    st.divider()
    reason_on = st.toggle("🧠 Reasoning (Chain of Thought)", value=True)
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. MAIN INTERFACE ---
st.markdown("<h1 class='amrit-title'>AMRIT-AI v1.4 FUSION</h1>", unsafe_allow_html=True)

if st.session_state.bhojpuri_mode:
    st.warning("🔥 Bhojpuri Mode Chalu Ba! Ab AI ekdum garda machai.")

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

if prompt := st.chat_input("Kaise ho bhai? Kuch pucho..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        try:
            # DESI SYSTEM PROMPT
            sys_p = "You are AmritAI, built by Amrit Pathak. "
            if st.session_state.bhojpuri_mode:
                sys_p += """
                PERSONALITY: You are a witty, smart, and helpful person from Bihar/UP. 
                LANGUAGE: Use Bhojpuri-Hindi mix. Use words like 'Garda', 'Ka ho', 'Babua', 'Bujhala'. 
                STYLE: Be funny but very intelligent.
                """
            else:
                sys_p += "Use Hinglish. Be professional and smart."

            if reason_on:
                sys_p += " Use Chain of Thought. Start with 'THOUGHT:' and then 'FINAL ANSWER:'."

            headers = {"Authorization": f"Bearer {GROQ_KEY}"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages[-6:]],
                "temperature": 0.7
            }

            with st.spinner("🤔 AI Sochat ba..." if st.session_state.bhojpuri_mode else "Thinking..."):
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                full_res = res.json()["choices"][0]["message"]["content"]

                if reason_on and "THOUGHT:" in full_res:
                    parts = full_res.split("FINAL ANSWER:")
                    thought = parts[0].replace("THOUGHT:", "").strip()
                    answer = parts[1].strip() if len(parts) > 1 else full_res
                    
                    with st.expander("👁️ Dekha AI ka Dimag (Thought)", expanded=True):
                        st.markdown(f"<div class='thinking-box'>{thought}</div>", unsafe_allow_html=True)
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.write(full_res)
                    st.session_state.messages.append({"role": "assistant", "content": full_res})
        except:
            st.error("Galti ho gail! API key check kara babua.")
