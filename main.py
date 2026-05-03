import streamlit as st
import os, requests, datetime
import pytz
from duckduckgo_search import DDGS

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="AmritAI v2.0 Pro", page_icon="🌐", layout="wide")
GROQ_KEY = os.environ.get("GROQ_KEY") # Apni API Key yahan set karein
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .search-header { color: #00d4ff; font-weight: bold; font-size: 24px; }
    .summary-box { 
        background: #161b22; border: 1px solid #30363d; 
        padding: 20px; border-radius: 10px; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE SEARCH & SCRAPE ENGINE ---
def get_web_summary_data(query):
    """
    Ye function wahi 'q=...' wala kaam karta hai.
    Internet se snippets nikaal kar ek raw text banata hai.
    """
    try:
        with DDGS() as ddgs:
            # Hum query mein 'latest 2026' add kar dete hain taaki results fresh aayein
            search_query = f"{query} latest updates 2026"
            results = [r for r in ddgs.text(search_query, max_results=5)]
            
            if not results:
                return None
                
            raw_context = ""
            for i, r in enumerate(results):
                raw_context += f"SOURCE {i+1} [{r['href']}]: {r['body']}\n\n"
            return raw_context
    except Exception as e:
        return f"Error fetching data: {e}"

# --- 3. UI LAYOUT ---
st.markdown("<h1 style='text-align:center;'>⚡ AmritAI Pro v2.0</h1>", unsafe_allow_html=True)
st.caption("Tip: Type **/web** followed by your question for live internet summary.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for status
with st.sidebar:
    st.header("📊 System Status")
    now = datetime.datetime.now(IST)
    st.write(f"📅 **Date:** {now.strftime('%d %B %Y')}")
    st.write(f"📍 **Location:** Ghaziabad")
    st.divider()
    if st.button("Clear Memory"):
        st.session_state.chat_history = []
        st.rerun()

# --- 4. CHAT LOGIC ---
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Kaise madad karun?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        raw_web_data = ""
        is_search = prompt.lower().strip().startswith("/web")

        # STEP 1: If /web is detected, trigger search
        if is_search:
            actual_query = prompt.lower().replace("/web", "").strip()
            with st.spinner(f"🔍 Searching websites for '{actual_query}'..."):
                raw_web_data = get_web_summary_data(actual_query)
        
        # STEP 2: System Prompt Engineering (LLM Instruction)
        current_date = datetime.datetime.now(IST).strftime("%d %B %Y")
        
        if is_search and raw_web_data:
            sys_p = f"""
            You are a Web Intelligence Expert.
            DATE: {current_date}
            
            TASK: Use the RAW WEB DATA below to answer the user's query: "{actual_query}".
            
            RAW WEB DATA:
            ---
            {raw_web_data}
            ---
            
            INSTRUCTIONS:
            1. Summarize the information clearly in Hinglish.
            2. Mention the facts found in the sources.
            3. If the data is missing, say you couldn't find specific live info.
            4. Keep it friendly but accurate.
            """
        else:
            sys_p = f"You are AmritAI, a helpful assistant. Today is {current_date}. Speak in Hinglish."

        # STEP 3: API Call to Groq
        try:
            headers = {"Authorization": f"Bearer {GROQ_KEY}"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_p}, *st.session_state.chat_history[-5:]],
                "temperature": 0.5
            }
            
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            ans = res.json()["choices"][0]["message"]["content"]
            
            st.markdown(f"<div class='summary-box'>{ans}</div>", unsafe_allow_html=True)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})

        except Exception as e:
            st.error(f"Bhai, API call fail ho gayi: {e}")
