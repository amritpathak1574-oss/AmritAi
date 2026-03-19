import streamlit as st
import os, requests, json, datetime, time, random, re
import pytz

# --- 1. CONFIG & UI ---
# App ka naam v1.1 Fusion set kar diya hai
st.set_page_config(page_title="AmritAI v1.1 Fusion", page_icon="🎨", layout="wide")

# Secrets & Timezone
GROQ_KEY = os.environ.get("GROQ_KEY")
SECRET_YOUTUBER_CODE = "chiku03"
IST = pytz.timezone('Asia/Kolkata')

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; }
    .main-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px; padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .amrit-title { 
        color: #00f2fe; 
        text-align: center; 
        text-shadow: 0 0 15px #00f2fe;
        font-family: 'Trebuchet MS', sans-serif;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background: linear-gradient(45deg, #00f2fe, #4facfe);
        color: black;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px #00f2fe; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "tasks" not in st.session_state: st.session_state.tasks = []
if "user_name" not in st.session_state: st.session_state.user_name = None
if "is_subscriber_mode" not in st.session_state: st.session_state.is_subscriber_mode = False
if "persona" not in st.session_state: 
    st.session_state.persona = "You are AmritAI, a witty, helpful AI built by Amrit Pathak. Speak in Hinglish."

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 class='amrit-title'>🚀 AmritAI Lab</h1>", unsafe_allow_html=True)
    st.caption("Version: 1.1 Fusion")
    
    if not st.session_state.user_name:
        name = st.text_input("Enter your name:", placeholder="Amrit...")
        if st.button("Access System 🔑"):
            if name:
                st.session_state.user_name = name
                st.rerun()
    else:
        st.success(f"Welcome, **{st.session_state.user_name}**!")
        if st.session_state.is_subscriber_mode:
            st.warning("🔥 SUBSCRIBER MODE ACTIVE")
        
        st.divider()
        menu = st.radio("Navigation:", ["💬 AI Chat", "🎨 Image Lab", "🎯 Task Manager"])
        
        if st.button("🚪 Logout"):
            st.session_state.user_name = None
            st.session_state.messages = []
            st.rerun()

# --- 4. MAIN LOGIC ---

if not st.session_state.user_name:
    st.markdown("<div class='main-card'><h2 style='text-align:center;'>🤖 Welcome to AmritAI v1.1 Fusion</h2><p style='text-align:center;'>Please login from the sidebar to continue, Bhai!</p></div>", unsafe_allow_html=True)

# --- MODE: IMAGE LAB ---
elif menu == "🎨 Image Lab":
    st.markdown("<h2 class='amrit-title'>🎨 AI Image Generator</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        prompt_img = st.text_input("Describe your image:", placeholder="Example: A futuristic soldier in space, cyberpunk style")
        
        col1, col2 = st.columns(2)
        style = col1.selectbox("Style:", ["Digital Art", "Anime", "Photorealistic", "Cyberpunk", "Sketch"])
        quality = col2.selectbox("Quality:", ["Standard", "High Definition", "Ultra Detail"])

        if st.button("Generate Magic ✨"):
            if prompt_img:
                with st.spinner("AI is painting your imagination..."):
                    try:
                        # Fixed URL & Seed Logic
                        seed = random.randint(1, 999999)
                        # Clean prompt for URL
                        full_prompt = f"{prompt_img}, {style}, {quality}".replace(" ", "%20")
                        img_url = f"https://pollinations.ai/p/{full_prompt}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"
                        
                        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
                        # Fixed width for Streamlit 1.55+
                        st.image(img_url, caption=f"✨ {prompt_img}", width="stretch")
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.success("Image generated! Right-click and 'Save Image As' to download.")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Pehle description likho bhai!")

# --- MODE: TASK MANAGER ---
elif menu == "🎯 Task Manager":
    st.header("🎯 Homework & To-Do List")
    col1, col2 = st.columns([0.8, 0.2])
    t_input = col1.text_input("New Task...")
    if (col2.button("Add") or (t_input and st.session_state.get('last_task') != t_input)) and t_input:
        st.session_state.tasks.append(t_input)
        st.rerun()
    
    for i, t in enumerate(st.session_state.tasks):
        st.write(f"✅ {t}")
    if st.button("Clear All"): st.session_state.tasks = []; st.rerun()

# --- MODE: AI CHAT ---
else:
    st.markdown(f"<h2 class='amrit-title'>💬 Chatting with {st.session_state.user_name}</h2>", unsafe_allow_html=True)
    
    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("Ask AmritAI anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        # Check for Secret Command
        if prompt.lower().startswith("/secret"):
            code = prompt.replace("/secret", "").strip()
            with st.chat_message("assistant"):
                if code == SECRET_YOUTUBER_CODE:
                    st.session_state.is_subscriber_mode = True
                    resp = "🔥 OP Bhai! Subscriber Mode ON ho gaya hai. Swagat hai AmritAI v1.1 Fusion mein!"
                else:
                    resp = "❌ Galat Code! Amrit ki video dhyan se dekho."
                st.write(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})

        elif prompt.lower() == "/clear":
            st.session_state.messages = []
            st.rerun()

        else:
            # AI Response Logic
            with st.chat_message("assistant"):
                try:
                    sys_p = st.session_state.persona
                    if st.session_state.is_subscriber_mode:
                        sys_p += " Mode: Energetic Indian YouTuber. Use words like 'Bhai', 'Op', 'Gajab', 'Ekdum'."

                    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
                    payload = {
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "system", "content": sys_p}, *st.session_state.messages]
                    }
                    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    ans = res.json()["choices"][0]["message"]["content"]
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                except Exception as e:
                    st.error(f"⚠️ API Error: {e}. Check your GROQ_KEY in Secrets.")
