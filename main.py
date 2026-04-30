import streamlit as st
import os, requests, json, datetime
import pytz
from duckduckgo_search import DDGS

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="AmritAI v1.6 Infinity", page_icon="♾️", layout="wide")

GROQ_KEY = os.environ.get("GROQ_KEY")
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #1a1a2e, #16213e); color: white; }
    .amrit-title { 
        font-family: 'Orbitron', sans-serif;
        background: -webkit-linear-gradient(#00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; font-size: 40px; font-weight: bold;
    }
    .thinking-box { 
        background: rgba(0, 242, 254, 0.1); 
        border-left: 4px solid #00f2fe; 
        padding: 15px; border-radius: 10px;
        margin-bottom: 20px; font-family: 'Courier New', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE MANAGEMENT ---
if "messages" not in st.session_state: st.session_state.messages = []
if "bhojpuri_mode" not in st.session_state: st.session_state.bhojpuri_mode = True
if "reasoning_on" not in st.session_state: st.session_state.reasoning_on = True

# --- 3. HELPER FUNCTIONS (The Brain) ---

def get_current_context():
    """Automatically gets the date and time"""
    now = datetime.datetime.now(IST)
    return {
        "date": now.strftime("%d %B %Y"),
        "time": now.strftime("%I:%M %p"),
        "day": now.strftime("%A")
    }

def web_search(query):
    """Unlimited Free Search using DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            context = "\n".join([f"Source: {r['href']}\nInfo: {r['body']}" for r in results])
            return context if context else "No live info found."
    except Exception as e:
        return f"Search error: {e}"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>🚀 AmritAI Lab</h1>", unsafe_allow_html=True)
    st.divider()
    
    st.subheader("System Toggles")
    st.session_state.bhojpuri_mode = st.toggle("🪕 Bhojpuri Mode", value=st.session_state.bhojpuri_mode)
    st.session_state.reasoning_on = st.toggle("🧠 Reasoning Mode (CoT)", value=st.session_state.reasoning_on)
    
    st.divider()
    ctx = get_current_context()
    st.info(f"📅 {ctx['date']}\n\n⏰ {ctx['time']}\n\n🌍 Ghaziabad, India")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 5. MAIN CHAT INTERFACE ---
st.markdown("<h1 class='amrit-title'>AMRIT-AI v1.6 PRO</h1>", unsafe_allow_html=True)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User Input
if prompt := st.chat_input("Pucha babua, ka haal ba?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        try:
            # 1. Automatic Context Building
            ctx = get_current_context()
            live_data = ""
            
            # 2. Check if Search is needed (Simple Keyword Check)
            search_keywords = ["today", "weather", "score", "news", "khabar", "mausam", "aaj"]
            if any(word in prompt.lower() for word in search_keywords):
                with st.spinner("🌐 Internet pe khojat baani..."):
                    live_data = web_search(prompt)

            # 3. Dynamic System Prompt
            sys_p = f"""
            You are AmritAI v1.6, an advanced AI developed by Amrit Pathak.
            AUTONOMOUS CONTEXT:
            - Current Date: {ctx['date']}
            - Current Time: {ctx['time']}
            - Current Day: {ctx['day']}
            - Location: Ghaziabad, UP, India.
            - User: Amrit (11 years old, Air Force School Hindan).
            
            PERSONALITY:
            - Language: {'Bhojpuri-Hindi mix' if st.session_state.bhojpuri_mode else 'Hinglish'}.
            - Tone: Smart, Witty, and Desi.
            
            REAL-TIME DATA:
            {live_data if live_data else "No specific search needed for this query."}

            STRICT RULE:
            If Reasoning Mode is ON, always start your response with 'THOUGHT:' followed by your logic, 
            and then 'FINAL ANSWER:' for the user response.
            """

            # 4. API Call to Groq
            headers = {"Authorization": f"Bearer {GROQ_KEY}"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages[-6:]],
                "temperature": 0.6
            }

            with st.spinner("🧠 AmritAI Sochat ba..." if st.session_state.bhojpuri_mode else "Thinking..."):
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                full_text = response.json()["choices"][0]["message"]["content"]

                # 5. Handle Reasoning Output
                if st.session_state.reasoning_on and "THOUGHT:" in full_text:
                    parts = full_text.split("FINAL ANSWER:")
                    thought_process = parts[0].replace("THOUGHT:", "").strip()
                    final_output = parts[1].strip() if len(parts) > 1 else full_text
                    
                    with st.expander("👁️ View AI's Thought Process", expanded=True):
                        st.markdown(f"<div class='thinking-box'>{thought_process}</div>", unsafe_allow_html=True)
                    st.write(final_output)
                    st.session_state.messages.append({"role": "assistant", "content": final_output})
                else:
                    st.write(full_text)
                    st.session_state.messages.append({"role": "assistant", "content": full_text})
                    
        except Exception as e:
            st.error(f"⚠️ Arre babua, error aa gail: {e}")
