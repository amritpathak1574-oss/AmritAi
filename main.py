import streamlit as st
import os, requests, datetime
import pytz
from duckduckgo_search import DDGS

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="AmritAI v3.0", page_icon="🛡️", layout="wide")
GROQ_KEY = os.environ.get("GROQ_KEY")
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .bot-answer { background: #1c2128; padding: 20px; border-radius: 12px; border-left: 5px solid #238636; }
    .source-pill { background: #21262d; border: 1px solid #30363d; border-radius: 20px; 
                   padding: 4px 10px; font-size: 12px; color: #8b949e; display: inline-block; margin: 2px; }
    .search-badge { background: #0d2840; border: 1px solid #1f6feb; border-radius: 6px; 
                    padding: 6px 12px; font-size: 12px; color: #58a6ff; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SMART AUTO-SEARCH DETECTION ---
SEARCH_KEYWORDS = [
    # Movies/Entertainment
    "movie", "film", "release", "ott", "netflix", "amazon prime", "hotstar",
    "bollywood", "hollywood", "web series", "trailer",
    # News/Current events  
    "news", "aaj", "today", "abhi", "latest", "recent", "current",
    "kya hua", "happened", "broke", "announced",
    # Sports
    "ipl", "cricket", "match", "score", "result", "tournament",
    "football", "fifa", "nba",
    # Tech/Products
    "launched", "release", "update", "version", "new phone", "price",
    # People/Politics
    "election", "vote", "minister", "president", "ceo", "arrested",
    # Market
    "stock", "share", "market", "rate", "crypto", "bitcoin",
]

def should_auto_search(query: str) -> bool:
    """
    Query analyze karke decide karta hai search karna chahiye ya nahi.
    Hinglish + English dono handle karta hai.
    """
    q_lower = query.lower()
    
    # /web command - always search
    if q_lower.startswith("/web"):
        return True
    
    # Keyword matching
    if any(kw in q_lower for kw in SEARCH_KEYWORDS):
        return True
    
    # Year mention (2024, 2025, 2026)
    import re
    if re.search(r'\b202[4-6]\b', q_lower):
        return True
    
    return False

# --- 3. IMPROVED SEARCH WITH SOURCES ---
def get_verified_web_data(query: str) -> tuple[str, list]:
    """
    DuckDuckGo se search karta hai, 2026 results prefer karta hai.
    Returns: (formatted_context, sources_list)
    """
    try:
        clean_query = query.replace("/web", "").strip()
        
        # Multiple search strategies - best results ke liye
        search_queries = [
            f"{clean_query} 2026",
            f"{clean_query} May 2026",
        ]
        
        all_results = []
        seen_urls = set()
        
        with DDGS() as ddgs:
            for sq in search_queries:
                results = list(ddgs.text(sq, max_results=4))
                for r in results:
                    if r['href'] not in seen_urls:
                        seen_urls.add(r['href'])
                        all_results.append(r)
                if len(all_results) >= 6:
                    break
        
        if not all_results:
            return "Koi fresh results nahi mile.", []
        
        # Format context for AI
        raw_data = f"LIVE WEB DATA (Searched: {datetime.datetime.now(IST).strftime('%d %b %Y %H:%M IST')}):\n\n"
        sources = []
        
        for i, r in enumerate(all_results[:6], 1):
            raw_data += f"[{i}] {r['title']}\n{r['body']}\nURL: {r['href']}\n\n"
            sources.append({
                "title": r['title'][:50] + "..." if len(r['title']) > 50 else r['title'],
                "url": r['href']
            })
        
        return raw_data, sources
        
    except Exception as e:
        return f"Search Error: {e}", []

# --- 4. UI LAYOUT ---
st.markdown("<h1 style='text-align:center; color:#238636;'>🛡️ AmritAI v3.0</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#8b949e;'>Auto Web Search • Anti-Hallucination • Real-time Data</p>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("### 📊 Live Monitor")
    now = datetime.datetime.now(IST)
    st.info(f"📅 {now.strftime('%d %B %Y')}\n\n🕐 {now.strftime('%H:%M')} IST\n\n📍 Ghaziabad")
    
    st.markdown("### ⚡ Auto-Search Triggers")
    st.caption("Yeh topics pe auto search hoga:")
    st.caption("🎬 Movies • 📰 News • 🏏 Sports\n💻 Tech • 📈 Market • 👤 People")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.caption("💡 `/web <query>` - Force search\n💡 Normal chat - Auto detect")

# --- 5. CHAT ENGINE ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Kuch bhi pucho... auto search karega jab zaroorat ho!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        # Auto-detect if search needed
        needs_search = should_auto_search(prompt)
        web_context = ""
        sources = []
        
        if needs_search:
            search_query = prompt.replace("/web", "").strip()
            with st.spinner(f"🔍 Searching live web data..."):
                web_context, sources = get_verified_web_data(search_query)

        # Show search badge if searched
        if needs_search and web_context:
            st.markdown('<div class="search-badge">🌐 Live web data used</div>', unsafe_allow_html=True)

        # --- SYSTEM PROMPT ---
        sys_p = f"""You are AmritAI v3.0. Today is {now.strftime('%d %B %Y, %H:%M IST')}.

STRICT RULES:
1. If 'LIVE WEB DATA' is provided, prioritize it completely over your training data.
2. Never mention movies, news, or events from 2023-2024 as "current" or "new".
3. If web data seems outdated (mentions old dates), clearly say: "Search results purane lag rahe hain."
4. If no web data provided, answer from knowledge but add: "Yeh mere training data pe based hai."
5. Be concise and helpful. Tone: Friendly developer Hinglish.
6. For movies/shows: Only mention what's explicitly in the web data.

WEB DATA:
{web_context if web_context else "No live search performed. Use training knowledge."}

Response format: Direct answer, no unnecessary preamble."""

        try:
            headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": sys_p},
                    *st.session_state.messages[-6:]
                ],
                "temperature": 0.2,
                "max_tokens": 1024
            }
            
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            res.raise_for_status()
            
            answer = res.json()["choices"][0]["message"]["content"]
            
            st.markdown(f"<div class='bot-answer'>{answer}</div>", unsafe_allow_html=True)
            
            # Show sources if searched
            if sources:
                st.markdown("**📎 Sources:**")
                sources_html = " ".join([
                    f'<a href="{s["url"]}" target="_blank" class="source-pill">🔗 {s["title"]}</a>'
                    for s in sources[:4]
                ])
                st.markdown(sources_html, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})

        except requests.exceptions.Timeout:
            st.error("⏱️ Request timeout. Dobara try karo!")
        except Exception as e:
            st.error(f"❌ Error: {e}")
