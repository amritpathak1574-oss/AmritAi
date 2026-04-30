import streamlit as st
import os, requests, json, datetime
import pytz
from duckduckgo_search import DDGS

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="AmritAI v1.7 Pro", page_icon="⚡", layout="wide")

GROQ_KEY = os.environ.get("GROQ_KEY")
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .amrit-title { 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #00d4ff; text-align: center; font-size: 35px; font-weight: 700;
        letter-spacing: 2px;
    }
    .thinking-box { 
        background: rgba(255, 255, 255, 0.05); 
        border-left: 4px solid #00d4ff; 
        padding: 12px; border-radius: 8px;
        margin-bottom: 20px; font-size: 14px; color: #a0a0a0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC FUNCTIONS ---
def get_time_info():
    now = datetime.datetime.now(IST)
    return {
        "full": now.strftime("%d %B %Y, %I:%M %p"),
        "day": now.strftime("%A")
    }

def web_search(query):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            return "\n".join([f"Source: {r['href']}\nInfo: {r['body']}" for r in results])
    except:
        return "Search failed, but I will answer based on my knowledge."

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#00d4ff;'>🛠️ Control Center</h2>", unsafe_allow_html=True)
    st.divider()
    reasoning_on = st.toggle("Show AI Thinking (CoT)", value=True)
    st.divider()
    t_info = get_time_info()
    st.write(f"📅 **Date:** {t_info['full']}")
    st.write(f"📍 **Location:** Ghaziabad")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 4. CHAT INTERFACE ---
st.markdown("<h1 class='amrit-title'>AMRIT-AI PRO v1.7</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        try:
            # Automatic context gathering
            t_info = get_time_info()
            live_data = ""
            
            # Smart Search Trigger
            search_words = ["weather", "news", "score", "today", "latest", "price", "match"]
            if any(w in prompt.lower() for w in search_words):
                with st.spinner("Searching the web for latest info..."):
                    live_data = web_search(prompt)

            # System Prompt (Strictly Hinglish)
            sys_p = f"""
            You are AmritAI v1.7, created by Amrit Pathak.
            - Current Context: {t_info['full']}, {t_info['day']}.
            - Language: Hinglish (Natural Hindi + English mix).
            - Style: Smart, helpful, peer-like.
            - Real-time Data: {live_data}
            
            STRICT FORMAT:
            If Reasoning is enabled, start with 'THOUGHT:' for your internal logic, 
            then 'FINAL ANSWER:' for the user.
            """

            headers = {"Authorization": f"Bearer {GROQ_KEY}"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages[-6:]],
                "temperature": 0.7
            }

            with st.spinner("Processing..."):
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                res_content = response.json()["choices"][0]["message"]["content"]

                if reasoning_on and "THOUGHT:" in res_content:
                    parts = res_content.split("FINAL ANSWER:")
                    thought = parts[0].replace("THOUGHT:", "").strip()
                    answer = parts[1].strip() if len(parts) > 1 else res_content
                    with st.expander("👁️ View Reasoning", expanded=False):
                        st.markdown(f"<div class='thinking-box'>{thought}</div>", unsafe_allow_html=True)
                    st.write(answer)
                else:
                    st.write(res_content)
                
                st.session_state.messages.append({"role": "assistant", "content": res_content})

        except Exception as e:
            st.error("Bhai, system mein kuch error hai. API check karo!")
