import streamlit as st
import os, requests, datetime
import pytz
from duckduckgo_search import DDGS

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="AmritAI v1.9 (Command Mode)", page_icon="⚡", layout="wide")

GROQ_KEY = os.environ.get("GROQ_KEY")
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .title-text { 
        text-align: center; color: #58a6ff; font-family: 'Trebuchet MS';
        font-size: 38px; font-weight: bold; margin-bottom: 10px;
    }
    .web-tag { 
        background-color: #238636; color: white; padding: 2px 8px; 
        border-radius: 5px; font-size: 12px; font-weight: bold;
    }
    .thought-box {
        background-color: #161b22; border-left: 4px solid #30363d;
        padding: 15px; border-radius: 5px; color: #8b949e; font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS ---

def get_live_web_data(query):
    """DuckDuckGo Search Logic - Scans websites for snippets"""
    try:
        with DDGS() as ddgs:
            # Adding 2026 for better accuracy
            search_query = f"{query} current updates 2026"
            results = [r for r in ddgs.text(search_query, max_results=4)]
            
            context = "LATEST WEB SEARCH RESULTS:\n"
            for r in results:
                context += f"- Source: {r['href']}\n  Snippet: {r['body']}\n\n"
            return context
    except Exception as e:
        return f"Web search failed: {e}"

def get_context():
    now = datetime.datetime.now(IST)
    return {
        "date": now.strftime("%d %B %Y"),
        "time": now.strftime("%I:%M %p"),
        "day": now.strftime("%A")
    }

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    show_thoughts = st.toggle("Show AI Thinking", value=True)
    st.divider()
    ctx = get_context()
    st.write(f"📅 **Date:** {ctx['date']}")
    st.write(f"⏰ **Time:** {ctx['time']}")
    st.write(f"📍 **Loc:** Ghaziabad, UP")
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. CHAT UI ---
st.markdown("<div class='title-text'>AMRIT-AI v1.9 PRO</div>", unsafe_allow_html=True)
st.caption("Use <span class='web-tag'>/web</span> before your message to search the internet.", unsafe_allow_html=True)

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User Input
if prompt := st.chat_input("Kaise madad karun, Amrit?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        web_info = ""
        is_web_search = prompt.lower().strip().startswith("/web")

        # Logical Routing
        if is_web_search:
            clean_query = prompt.lower().replace("/web", "").strip()
            with st.spinner(f"🌐 Scraping web for '{clean_query}'..."):
                web_info = get_live_web_data(clean_query)
        
        # Build System Prompt
        sys_p = f"""
        You are AmritAI v1.9, developed by Amrit Pathak.
        CONTEXT: Today is {ctx['day']}, {ctx['date']}. Time: {ctx['time']}.
        LANGUAGE: Natural Hinglish (Mix of Hindi & English).
        
        WEB SEARCH MODE:
        - Active: {is_web_search}
        - Data Provided: {web_info if web_info else "None requested."}
        
        INSTRUCTIONS:
        1. If /web mode is active, strictly prioritize the 'Data Provided' above.
        2. If NOT active, do not guess live facts like scores or prices.
        3. Keep the tone like a helpful peer/friend.
        
        FORMAT:
        THOUGHT: (Briefly explain your logic)
        FINAL ANSWER: (The actual response)
        """

        try:
            headers = {"Authorization": f"Bearer {GROQ_KEY}"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages[-6:]],
                "temperature": 0.6
            }

            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            full_res = response.json()["choices"][0]["message"]["content"]

            if "THOUGHT:" in full_res and "FINAL ANSWER:" in full_res:
                parts = full_res.split("FINAL ANSWER:")
                thought = parts[0].replace("THOUGHT:", "").strip()
                answer = parts[1].strip()
                
                if show_thoughts:
                    st.markdown(f"<div class='thought-box'><b>Logic:</b> {thought}</div>", unsafe_allow_html=True)
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.write(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})

        except Exception as e:
            st.error(f"Bhai error aa gaya: {e}")
