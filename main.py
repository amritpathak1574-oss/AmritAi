import streamlit as st
import os, requests, datetime
import pytz
from duckduckgo_search import DDGS

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="AmritAI v1.8 Search-First", page_icon="🔍", layout="wide")
GROQ_KEY = os.environ.get("GROQ_KEY")
IST = pytz.timezone('Asia/Kolkata')

# --- 2. THE SEARCH ENGINE LOGIC ---
def get_live_web_data(query):
    """
    Ye function Google/DuckDuckGo par jaakar websites ki 
    summary aur links nikaalta hai.
    """
    try:
        with DDGS() as ddgs:
            # Movie queries ke liye hum 'latest' aur '2026' add kar dete hain accuracy ke liye
            enhanced_query = f"{query} latest updates 2026"
            results = [r for r in ddgs.text(enhanced_query, max_results=4)]
            
            context = "WEBSITE DATA FOUND:\n"
            for r in results:
                context += f"- Title: {r['title']}\n  Info: {r['body']}\n  Link: {r['href']}\n\n"
            return context
    except Exception as e:
        return f"Web Search Error: {e}"

# --- 3. UI LAYOUT ---
st.markdown("<h1 style='text-align:center; color:#00d4ff;'>🔍 AmritAI Search-First Edition</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar info
with st.sidebar:
    st.header("⚙️ Settings")
    show_reasoning = st.toggle("Show Thinking Process", value=True)
    now = datetime.datetime.now(IST)
    st.info(f"📅 Date: {now.strftime('%d %B %Y')}\n\n📍 Location: Ghaziabad")

# --- 4. MAIN CHAT LOGIC ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

if prompt := st.chat_input("Movie list ya news pucho..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        # STEP 1: Search trigger (Check if user is asking for live info)
        trigger_words = ["movie", "film", "latest", "news", "match", "weather", "aaj ka", "today"]
        web_context = ""
        
        if any(word in prompt.lower() for word in trigger_words):
            with st.spinner("🌐 Searching top websites for latest list..."):
                web_context = get_live_web_data(prompt)

        # STEP 2: System Prompt with Live Data
        current_date = datetime.datetime.now(IST).strftime("%d %B %Y")
        sys_p = f"""
        You are AmritAI v1.8. 
        Current Date: {current_date}. 
        User Location: Ghaziabad.
        
        INSTRUCTIONS:
        - If 'WEBSITE DATA' is provided below, use it as your primary source.
        - Do NOT hallucinate old movies from 2023. 
        - If the website data says a movie released today, mention it.
        - Style: Friendly Hinglish.
        
        LIVE SEARCH DATA FROM WEBSITES:
        {web_context if web_context else "No live search needed."}
        
        Format:
        THOUGHT: (Your internal logic)
        FINAL ANSWER: (Response for Amrit)
        """

        # STEP 3: Call Groq API
        try:
            headers = {"Authorization": f"Bearer {GROQ_KEY}"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages[-5:]],
                "temperature": 0.5
            }
            
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            ans = res.json()["choices"][0]["message"]["content"]

            # Handle Thinking Process
            if "THOUGHT:" in ans and "FINAL ANSWER:" in ans:
                parts = ans.split("FINAL ANSWER:")
                thought = parts[0].replace("THOUGHT:", "").strip()
                final_ans = parts[1].strip()
                
                if show_reasoning:
                    with st.expander("👁️ AI Thinking Process"):
                        st.write(thought)
                st.write(final_ans)
            else:
                st.write(ans)
                
            st.session_state.messages.append({"role": "assistant", "content": ans})

        except:
            st.error("Bhai, API key ya network ka issue hai!")
