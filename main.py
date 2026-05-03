import streamlit as st
import os, requests, datetime
import pytz
from duckduckgo_search import DDGS

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="AmritAI v2.1 (Anti-Hallucination)", page_icon="🛡️", layout="wide")
GROQ_KEY = os.environ.get("GROQ_KEY") 
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .status-card { background: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    .bot-answer { background: #1c2128; padding: 20px; border-radius: 12px; border-left: 5px solid #238636; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SEARCH LOGIC (Strictly 2026) ---
def get_verified_web_data(query):
    """
    Search engine se data uthata hai aur query mein 
    '2026' force karta hai taaki results purane na aayein.
    """
    try:
        with DDGS() as ddgs:
            # Force current year for accuracy
            strict_query = f"{query} released in April May 2026 India"
            results = [r for r in ddgs.text(strict_query, max_results=6)]
            
            if not results:
                return "Bhai, internet par iske baare mein koi fresh 2026 ki news nahi mili."
                
            raw_data = "CURRENT INTERNET SNIPPETS (MAY 2026):\n"
            for r in results:
                raw_data += f"- {r['body']} (Source: {r['href']})\n\n"
            return raw_data
    except Exception as e:
        return f"Search Error: {e}"

# --- 3. UI LAYOUT ---
st.markdown("<h1 style='text-align:center; color:#238636;'>🛡️ AmritAI v2.1 Pro</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("### 📊 Live Monitor")
    now = datetime.datetime.now(IST)
    st.info(f"📅 Date: {now.strftime('%d %B %Y')}\n\n📍 Loc: Ghaziabad")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. CHAT ENGINE ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

if prompt := st.chat_input("Type '/web movie list' to test..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        is_web = prompt.lower().strip().startswith("/web")
        web_context = ""
        
        if is_web:
            q = prompt.lower().replace("/web", "").strip()
            with st.spinner(f"🌐 Verifying live data for 2026..."):
                web_context = get_verified_web_data(q)

        # --- THE ANTI-HALLUCINATION PROMPT ---
        sys_p = f"""
        You are AmritAI v2.1. Today's Date is {now.strftime('%d %B %Y')}.
        
        STRICT RULES:
        1. If 'CURRENT INTERNET SNIPPETS' are provided, ONLY use them.
        2. IGNORE your internal memory of movies from 2023-2024 (like Bholaa, Pathaan, Jawan). 
        3. If the snippets don't mention a movie, don't invent it.
        4. If the snippets mention 2023 movies, say: "Bhai search results purane hain."
        5. Tone: Helpful Developer Friend (Hinglish).
        
        WEB DATA PROVIDED:
        {web_context if web_context else "No live data. Answer generally."}
        
        Format:
        THOUGHT: (Explain why you are filtering out old info)
        FINAL ANSWER: (The clean, 2026-only response)
        """

        try:
            headers = {"Authorization": f"Bearer {GROQ_KEY}"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages[-4:]],
                "temperature": 0.3 # Temperature kam rakha hai taaki AI 'creative' na bane (hallucinate na kare)
            }
            
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            ans_raw = res.json()["choices"][0]["message"]["content"]
            
            if "FINAL ANSWER:" in ans_raw:
                thought = ans_raw.split("FINAL ANSWER:")[0].replace("THOUGHT:", "").strip()
                answer = ans_raw.split("FINAL ANSWER:")[1].strip()
                
                with st.expander("👁️ How I filtered hallucinations"):
                    st.write(thought)
                st.markdown(f"<div class='bot-answer'>{answer}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.write(ans_raw)
                st.session_state.messages.append({"role": "assistant", "content": ans_raw})

        except Exception as e:
            st.error(f"Bhai, error aa gaya: {e}")
