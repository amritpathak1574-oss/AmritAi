import streamlit as st
import os, requests, datetime
import pytz
from tavily import TavilyClient

# --- 1. SETTINGS & CONFIG ---
st.set_page_config(
    page_title="AmritAI v3.0",
    page_icon="🛡️",
    layout="wide"
)

GROQ_KEY   = os.environ.get("GROQ_KEY")
TAVILY_KEY = os.environ.get("TAVILY_KEY")
IST        = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;700&display=swap');

    .stApp { background-color: #080c10; color: #e6edf3; font-family: 'Syne', sans-serif; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #21262d; }

    /* Chat input */
    [data-testid="stChatInput"] textarea {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 12px !important;
    }

    /* User message */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 8px;
        margin-bottom: 8px;
    }

    /* Assistant message */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: #0d1117;
        border-radius: 12px;
        margin-bottom: 8px;
    }

    .bot-answer {
        background: linear-gradient(135deg, #0d1f12 0%, #0d1117 100%);
        padding: 20px 24px;
        border-radius: 12px;
        border-left: 4px solid #2ea043;
        font-size: 15px;
        line-height: 1.7;
        color: #e6edf3;
        white-space: pre-wrap;
    }

    .search-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #0d2033;
        border: 1px solid #1f6feb;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 12px;
        color: #58a6ff;
        margin-bottom: 10px;
        font-family: 'JetBrains Mono', monospace;
    }

    .source-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 11px;
        color: #8b949e;
        margin: 3px 2px;
        text-decoration: none;
        transition: border-color 0.2s;
        font-family: 'JetBrains Mono', monospace;
    }
    .source-pill:hover { border-color: #58a6ff; color: #58a6ff; }

    .tavily-answer {
        background: #0d2033;
        border: 1px solid #1f6feb30;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 13px;
        color: #79c0ff;
        margin-bottom: 12px;
        font-family: 'JetBrains Mono', monospace;
    }

    .stat-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        font-size: 13px;
    }

    h1 { font-family: 'Syne', sans-serif !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)


# --- 2. AUTO-SEARCH DETECTION ---
SEARCH_KEYWORDS = [
    # Entertainment
    "movie", "film", "release", "ott", "netflix", "amazon prime", "hotstar", "jiohotstar",
    "bollywood", "hollywood", "web series", "trailer", "review", "sequel",
    # News
    "news", "aaj", "today", "abhi", "latest", "recent", "current", "breaking",
    "kya hua", "happened", "announced", "launched",
    # Sports
    "ipl", "cricket", "match", "score", "result", "tournament", "football",
    "fifa", "nba", "wpl", "standings",
    # Tech
    "phone", "update", "version", "new model", "price", "specs",
    # People / Politics
    "election", "vote", "minister", "president", "pm", "ceo", "arrested", "died",
    # Finance
    "stock", "share", "market", "rate", "crypto", "bitcoin", "sensex", "nifty",
    # Weather
    "weather", "mausam", "barish", "temperature",
]

def should_auto_search(query: str) -> bool:
    import re
    q = query.lower()
    if q.startswith("/web"):
        return True
    if any(kw in q for kw in SEARCH_KEYWORDS):
        return True
    if re.search(r'\b202[4-6]\b', q):
        return True
    return False


# --- 3. TAVILY SEARCH ---
def get_verified_web_data(query: str) -> tuple[str, list, str]:
    """
    Tavily se live web data fetch karta hai.
    Returns: (context_for_ai, sources_list, quick_answer)
    """
    if not TAVILY_KEY:
        return "TAVILY_KEY environment variable set nahi hai!", [], ""

    try:
        client   = TavilyClient(api_key=TAVILY_KEY)
        clean_q  = query.replace("/web", "").strip()
        now_str  = datetime.datetime.now(IST).strftime('%d %b %Y %H:%M IST')

        response = client.search(
            query        = f"{clean_q} 2026",
            search_depth = "basic",
            max_results  = 5,
            include_answer = True,
        )

        sources      = []
        quick_answer = response.get("answer", "")
        raw_data     = f"LIVE WEB DATA (Searched: {now_str}):\n\n"

        if quick_answer:
            raw_data += f"TAVILY QUICK ANSWER: {quick_answer}\n\n"

        for i, r in enumerate(response.get("results", []), 1):
            title   = r.get("title", "")
            content = r.get("content", "")
            url     = r.get("url", "")
            raw_data += f"[{i}] {title}\n{content}\nURL: {url}\n\n"
            sources.append({
                "title": (title[:48] + "…") if len(title) > 48 else title,
                "url":   url,
            })

        if not sources:
            return "Tavily se koi result nahi mila.", [], ""

        return raw_data, sources, quick_answer

    except Exception as e:
        return f"Tavily Search Error: {e}", [], ""


# --- 4. UI HEADER ---
st.markdown("""
    <div style='text-align:center; padding: 20px 0 8px;'>
        <h1 style='font-size:2.2rem; margin:0; background: linear-gradient(90deg,#2ea043,#58a6ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
            🛡️ AmritAI v3.0
        </h1>
        <p style='color:#8b949e; font-size:13px; margin:6px 0 0; font-family: JetBrains Mono, monospace;'>
            Tavily Search • Auto-Detect • Anti-Hallucination • Real-time Data
        </p>
    </div>
""", unsafe_allow_html=True)


# --- 5. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "search_count" not in st.session_state:
    st.session_state.search_count = 0


# --- 6. SIDEBAR ---
with st.sidebar:
    now = datetime.datetime.now(IST)

    st.markdown("### 📊 Live Status")
    st.markdown(f"""
        <div class='stat-card'>
            📅 <b>{now.strftime('%d %B %Y')}</b><br>
            🕐 {now.strftime('%H:%M:%S')} IST<br>
            📍 Ghaziabad, UP
        </div>
        <div class='stat-card'>
            🔍 Searches this session: <b>{st.session_state.search_count}</b><br>
            💬 Messages: <b>{len(st.session_state.messages)}</b>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚡ Auto-Search Topics")
    st.markdown("""
        <div style='font-size:12px; color:#8b949e; line-height:2;'>
        🎬 Movies & OTT<br>
        📰 Breaking News<br>
        🏏 Sports & Scores<br>
        💻 Tech Launches<br>
        📈 Market & Crypto<br>
        👤 People & Politics<br>
        🌦️ Weather
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
        <div style='font-size:11px; color:#484f58; font-family: JetBrains Mono, monospace;'>
        💡 <code>/web query</code> → force search<br>
        💡 Normal chat → auto detect
        </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.search_count = 0
        st.rerun()


# --- 7. CHAT HISTORY DISPLAY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# --- 8. MAIN CHAT ENGINE ---
if prompt := st.chat_input("Kuch bhi pucho… movies, news, sports, tech sab!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):

        # Auto-detect search
        needs_search    = should_auto_search(prompt)
        web_context     = ""
        sources         = []
        quick_answer    = ""

        if needs_search:
            with st.spinner("🔍 Tavily se live data fetch kar raha hun..."):
                web_context, sources, quick_answer = get_verified_web_data(prompt)
                st.session_state.search_count += 1

        # Search badge
        if needs_search and sources:
            st.markdown(
                f'<div class="search-badge">🌐 Tavily Live Search • {len(sources)} sources</div>',
                unsafe_allow_html=True
            )

        # Tavily quick answer preview
        if quick_answer:
            st.markdown(
                f'<div class="tavily-answer">⚡ {quick_answer}</div>',
                unsafe_allow_html=True
            )

        # System prompt
        sys_p = f"""You are AmritAI v3.0. Today is {now.strftime('%d %B %Y, %H:%M IST')}.

STRICT RULES:
1. If 'LIVE WEB DATA' is provided, use it as your primary source. Prioritize it over training data.
2. Never present 2023-2024 events as "current" or "latest".
3. If web data seems outdated, say clearly: "Search results thode purane lag rahe hain."
4. If no web data, answer from knowledge but mention: "Yeh mere training data pe based hai, verify karna."
5. Tone: Friendly developer friend, Hinglish. Concise and direct.
6. For movies/shows/news: Only state what is explicitly in the web data.
7. Never hallucinate URLs, names, or statistics.

WEB DATA PROVIDED:
{web_context if web_context else "No live search performed. Use training knowledge carefully."}

Respond directly without preamble. Be helpful and precise."""

        # Groq API call
        try:
            if not GROQ_KEY:
                st.error("❌ GROQ_KEY environment variable set nahi hai!")
                st.stop()

            headers = {
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type":  "application/json"
            }
            payload = {
                "model":      "llama-3.3-70b-versatile",
                "messages":   [
                    {"role": "system", "content": sys_p},
                    *st.session_state.messages[-8:]   # last 8 messages for context
                ],
                "temperature": 0.2,
                "max_tokens":  1024,
            }

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers = headers,
                json    = payload,
                timeout = 30,
            )
            res.raise_for_status()

            answer = res.json()["choices"][0]["message"]["content"]

            # Display answer
            st.markdown(
                f'<div class="bot-answer">{answer}</div>',
                unsafe_allow_html=True
            )

            # Sources
            if sources:
                st.markdown(
                    "<div style='margin-top:12px; font-size:12px; color:#8b949e;'>📎 Sources:</div>",
                    unsafe_allow_html=True
                )
                pills_html = " ".join([
                    f'<a href="{s["url"]}" target="_blank" class="source-pill">🔗 {s["title"]}</a>'
                    for s in sources
                ])
                st.markdown(pills_html, unsafe_allow_html=True)

            st.session_state.messages.append({"role": "assistant", "content": answer})

        except requests.exceptions.Timeout:
            st.error("⏱️ Request timeout. Thoda wait karke dobara try karo!")
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ API Error {e.response.status_code}: {e.response.text[:200]}")
        except KeyError:
            st.error("❌ Groq response format unexpected. API key check karo.")
        except Exception as e:
            st.error(f"❌ Error: {e}")
