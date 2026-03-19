import streamlit as st
import os, requests, json, datetime, time
import pytz

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="AmritAI v1.1 Fusion", page_icon="🎨", layout="wide")

GROQ_KEY = os.environ.get("GROQ_KEY")
SECRET_YOUTUBER_CODE = "chiku03"
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460); color: white; }
    .amrit-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px; padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .amrit-title { color: #00f2fe; text-align: center; text-shadow: 0 0 10px #00f2fe; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "user_name" not in st.session_state: st.session_state.user_name = None
if "is_subscriber_mode" not in st.session_state: st.session_state.is_subscriber_mode = False

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 class='amrit-title'>🚀 AmritAI v1.1</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user_name:
        name = st.text_input("Apna Naam Likho:")
        if st.button("Entry 🔑"):
            st.session_state.user_name = name
            st.rerun()
    else:
        st.success(f"User: **{st.session_state.user_name}**")
        menu = st.radio("Select Mode:", ["💬 AI Chat", "🎨 Image Lab", "🎯 Task Manager"])
        
        if st.button("🚪 Logout"):
            st.session_state.user_name = None
            st.rerun()

# --- 4. MAIN INTERFACE ---

if not st.session_state.user_name:
    st.info("Bhai, pehle sidebar mein apna naam toh likho!")

elif menu == "🎨 Image Lab":
    st.header("🎨 AI Image Generator")
    st.write("Yahan tum jo likhoge, AI uski image bana dega!")
    
    prompt_img = st.text_input("Kya generate karna hai? (e.g. A futuristic car in space)")
    
    col1, col2 = st.columns(2)
    with col1:
        model_type = st.selectbox("Style:", ["Default", "Cyberpunk", "Anime", "Realistic"])
    with col2:
        aspect = st.selectbox("Size:", ["Square (1:1)", "Wide (16:9)", "Tall (9:16)"])

    if st.button("Generate Image ✨"):
        if prompt_img:
            with st.spinner("AI Brush chala raha hai... thoda rukiye..."):
                # Pollinations AI API (Free & No Key)
                encoded_prompt = prompt_img.replace(" ", "%20")
                img_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={datetime.datetime.now().second}&model=flux"
                
                st.image(img_url, caption=f"Generated: {prompt_img}", use_container_width=True)
                st.success("Image Taiyar hai! Right-click karke save karlo.")
        else:
            st.warning("Pehle kuch likho toh sahi!")

elif menu == "🎯 Task Manager":
    st.header("🎯 Homework & Tasks")
    # Purana Task logic yahan rahega...
    st.write("Tasks feature is active.")

else: # AI CHAT
    st.title(f"💬 Chatting with {st.session_state.user_name}")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("Ask AmritAI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        # AI Call Logic
        with st.chat_message("assistant"):
            try:
                headers = {"Authorization": f"Bearer {GROQ_KEY}"}
                # Check for subscriber mode
                sys_msg = "You are AmritAI, a witty assistant."
                if st.session_state.is_subscriber_mode:
                    sys_msg += " Talk like an energetic Indian YouTuber."

                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "system", "content": sys_msg}, *st.session_state.messages]
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                ans = res.json()["choices"][0]["message"]["content"]
                st.write(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except:
                st.error("API Error! Key check karo.")
