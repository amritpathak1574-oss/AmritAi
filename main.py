import streamlit as st
import os
import requests
import json
import datetime
import sys
from tavily import TavilyClient
import time
import re

# --- 1. Page Config ---
st.set_page_config(page_title="AmritAI Ultimate", page_icon="🤖", layout="centered")

# --- 2. Keys & Setup ---
# TAVILY_KEY aur GROQ_KEY environment variables/secrets se load honge
GROQ_KEY = os.environ.get("GROQ_KEY")
TAVILY_KEY = os.environ.get("TAVILY_KEY") 

CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
HISTORY_FILE = "chat_history.json"
SECRET_YOUTUBER_CODE = "chiku03"

# --- 3. Database Functions (History Management) ---
def load_all_history():
    """File se poora data load karta hai"""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            # Ensure all users have a 'custom_bots' key for safety
            for user in data:
                if 'custom_bots' not in data[user]:
                    data[user]['custom_bots'] = []
                if 'sessions' not in data[user]:
                    data[user]['sessions'] = {}
            return data
    except:
        return {}

def save_all_history(data):
    """Poora data file mein save karta hai"""
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_current_chat(username, session_id, title, messages):
    """Current chat aur bots ko file mein save karta hai"""
    data = load_all_history()

    if username not in data:
        data[username] = {"sessions": {}, "custom_bots": []} 
    if 'sessions' not in data[username]:
         data[username]['sessions'] = {}

    data[username]["sessions"][session_id] = {
        "title": title,
        "timestamp": str(datetime.datetime.now()),
        "messages": messages
    }

    save_all_history(data)

def save_custom_bots(username, bots_list):
    """Custom bots ki list ko file mein save karta hai"""
    data = load_all_history()
    if username not in data:
        data[username] = {"sessions": {}, "custom_bots": []} 

    data[username]["custom_bots"] = bots_list
    save_all_history(data)

def delete_chat_session(username, session_id):
    """Selected chat session ko history file se delete karta hai"""
    data = load_all_history()
    if username in data and session_id in data[username].get('sessions', {}):
        del data[username]['sessions'][session_id]
        save_all_history(data)
        return True
    return False

def get_user_sessions(username):
    """User ki purani chats ki list deta hai (title: id format mein)"""
    all_data = load_all_history() 

    if username in all_data and 'sessions' in all_data[username]:
        sessions = {
            session_id: details['title']
            for session_id, details in all_data[username]['sessions'].items() 
        }

        sorted_sessions = sorted(sessions.items(), key=lambda item: all_data[username]['sessions'][item[0]]['timestamp'], reverse=True)
        return dict(sorted_sessions)
    return {}

def load_user_bots(username):
    """User ke custom bots ki list load karta hai"""
    all_data = load_all_history()
    if username in all_data and 'custom_bots' in all_data[username]:
        return all_data[username]['custom_bots']
    return []


# --- 4. Helper Function: Dynamic Greeting & Time ---
def get_greeting(name):
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    hour = ist_now.hour

    if 5 <= hour < 12: greeting = "Good Morning ☀️"
    elif 12 <= hour < 17: greeting = "Good Afternoon 🌤️"
    elif 17 <= hour < 21: greeting = "Good Evening 🌆"
    elif 21 <= hour <= 23 or 0 <= hour < 5: greeting = "Good Night 🌙" 
    else: greeting = "Hello 👋" 

    return f"{greeting} **{name}**! Welcome to AmritAI."

# --- 5. Session State Initialization ---
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
if "current_session_title" not in st.session_state:
    st.session_state.current_session_title = "New Chat"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "is_subscriber_mode" not in st.session_state:
    st.session_state.is_subscriber_mode = False
# NEW BOT STATES
if "user_bots" not in st.session_state:
    st.session_state.user_bots = [] 
if "active_bot_name" not in st.session_state:
    st.session_state.active_bot_name = "AmritAI"
if "active_bot_prompt" not in st.session_state:
    st.session_state.active_bot_prompt = None 


# --- 6. System Brain ---
def get_system_prompt():
    user = st.session_state.user_name if st.session_state.user_name else "User"

    if st.session_state.active_bot_prompt:
        return {"role": "system", "content": st.session_state.active_bot_prompt}

    base_prompt = f"You are AmritAI. User: {user}. Tone: Hinglish, Witty, Helpful. Built by Pro Python Developer."

    if st.session_state.get('is_subscriber_mode'):
        return {"role": "system", "content": base_prompt + " MODE: Subscriber (Energetic, Slang, YouTuber style)."}
    else:
        return {"role": "system", "content": base_prompt}

# --- 7. Helper Functions (AI/Tools) ---

def generate_chat_title(messages):
    if len(messages) < 2: return "New Chat"
    history_for_title = messages[:4]
    system_msg = "You are a Chat Titler. Summarize the content of these messages into a short, catchy title (max 5 words) in English. Return ONLY the title text."
    api_history = [{"role": "system", "content": system_msg}] + history_for_title

    try:
        if not GROQ_KEY: return "Error: GROQ_KEY Missing"

        response = requests.post(
            CHAT_URL, 
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b-instant", "messages": api_history, "stream": False, "temperature": 0.3}
        )

        if response.status_code == 200:
            title = response.json()['choices'][0]['message']['content'].strip()
            title = title.replace('"', '').replace("'", '').replace('**', '').split('\n')[0]
            if len(title) < 3 or title.lower() in ["new chat", "untitled chat", ""]:
                return f"Chat on {messages[0]['content'].split()[0].replace('/', '')}"
            return title[:30]

    except Exception as e:
        print(f"Title generation error: {e}")

    return f"Chat-{datetime.datetime.now().strftime('%H:%M:%S')}" 

def get_groq_response(messages, model="llama-3.1-8b-instant"):
    if not GROQ_KEY: yield "⚠️ GROQ_KEY missing."
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {"model": model, "messages": messages, "stream": True, "temperature": 0.7}
    try:
        with requests.post(CHAT_URL, headers=headers, json=data, stream=True) as res:
            if res.status_code == 200:
                for line in res.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            json_str = decoded_line[6:]
                            if json_str.strip() == "[DONE]": break
                            try:
                                json_data = json.loads(json_str)
                                chunk = json_data["choices"][0]["delta"].get("content", "")
                                if chunk: yield chunk
                            except: continue
    except Exception as e: yield f"⚠️ Network Error: {e}"

def search_web(query, fetch_content=False): 
    # 🔥 FIX 1: Explicitly check TAVILY_KEY availability
    if not TAVILY_KEY: return "⚠️ Tavily Key Missing" 
    try:
        tavily = TavilyClient(api_key=TAVILY_KEY)
        if fetch_content:
            response = tavily.get_search_context(query, search_depth="advanced", max_tokens=1500, include_answer=False)
            return response if response else "No content."
        else:
            response = tavily.search(query, search_depth="basic", max_results=3)
            # Yahaan hum context ko aur robust bana rahe hain
            context = "\n".join([f"- Title: {r['title']}\n  Content: {r['content'][:250]}..." for r in response['results']])
            return context if context else "No results found for your query."
    except Exception as e: 
        # Yeh network ya invalid key ka generic error catch karega
        return f"Error: Tavily API call failed. Details: {e}"

def convert_units(value, unit_from, unit_to):
    try:
        if unit_from[0] == 'k' and unit_to[0] == 'l': return f"**Mass:** {value} Kg = {value * 2.204:.2f} Lbs"
        if unit_from[0] == 'c' and unit_to[0] == 'f': return f"**Temp:** {value} C = {(value*9/5)+32:.2f} F"
        if unit_from[0] == 'k' and unit_to[0] == 'm': return f"**Dist:** {value} Km = {value * 0.621:.2f} Miles"
        return "❌ Conversion not supported."
    except: return "❌ Error in conversion."

def list_tasks():
    if not st.session_state.tasks: return "🎉 No tasks."
    return "🎯 Pending List:\n" + "\n".join([f"**{i+1}.** {t}" for i, t in enumerate(st.session_state.tasks)])


# --- 8. MAIN UI ---

# 🛑 LOGIN SCREEN
if not st.session_state.user_name:
    st.title("🤖 AmritAI Login")
    with st.form("login"):
        name = st.text_input("Enter Name:")
        if st.form_submit_button("Start 🚀") and name:
            st.session_state.user_name = name
            st.session_state.user_bots = load_user_bots(name) 
            st.rerun()

# ✅ CHAT SCREEN
else:
    # --- SIDEBAR (HISTORY & TOOLS) ---
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        st.caption(f"Active Bot: **{st.session_state.active_bot_name}**")
        st.caption(f"Current Chat: **{st.session_state.current_session_title}**")

        st.markdown("---")

        # 🔥 BOT SELECTOR
        st.subheader("🤖 Custom Bots")

        bot_options = ["AmritAI (Default)"] + [bot['name'] for bot in st.session_state.user_bots]

        try:
            default_index = bot_options.index(st.session_state.active_bot_name)
        except ValueError:
            default_index = 0

        selected_bot_name = st.selectbox("Select Bot:", bot_options, index=default_index, key="bot_selector")

        if selected_bot_name != st.session_state.active_bot_name:
            st.session_state.active_bot_name = selected_bot_name

            if selected_bot_name == "AmritAI (Default)":
                st.session_state.active_bot_prompt = None
            else:
                selected_bot = next((bot for bot in st.session_state.user_bots if bot['name'] == selected_bot_name), None)
                if selected_bot:
                    st.session_state.active_bot_prompt = selected_bot['prompt']

            st.session_state.messages = []
            st.session_state.current_session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            st.session_state.current_session_title = f"New Chat with {st.session_state.active_bot_name}"
            st.rerun()

        # 🔥 BOT CREATOR FORM
        with st.expander("➕ Build Your Own Bot (No Code)"):
            with st.form("bot_creator_form", clear_on_submit=True):
                new_bot_name = st.text_input("Bot Name (e.g., Sarcastic Professor)", max_chars=30)
                new_bot_prompt = st.text_area("Bot Personality & Description (System Prompt)", height=150, placeholder="Example: You are a grumpy, ultra-sarcastic coding instructor who only replies in 2 sentences using Python slang and emojis.")

                if st.form_submit_button("💾 Create & Use This Bot"):
                    if new_bot_name and new_bot_prompt:
                        new_bot = {"name": new_bot_name, "prompt": new_bot_prompt}

                        if new_bot_name in [b['name'] for b in st.session_state.user_bots]:
                             st.error(f"Bot name '{new_bot_name}' already exists. Use a unique name.")
                        else:
                            st.session_state.user_bots.append(new_bot)
                            save_custom_bots(st.session_state.user_name, st.session_state.user_bots)

                            st.success(f"Bot '{new_bot_name}' created and activated! Chat history cleared.")
                            time.sleep(1)
                            st.rerun() 
                    else:
                        st.warning("Please fill out both fields.")

        st.markdown("---")

        # 📜 HISTORY SELECTOR
        st.subheader("📜 Chat History")

        if st.button("➕ New Chat"):
            if len(st.session_state.messages) > 0:
                save_current_chat(st.session_state.user_name, st.session_state.current_session_id, st.session_state.current_session_title, st.session_state.messages)
            st.session_state.messages = []
            st.session_state.tasks = []
            st.session_state.current_session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            st.session_state.current_session_title = f"New Chat with {st.session_state.active_bot_name}"
            st.rerun()

        # Load Old Chats
        all_sessions = get_user_sessions(st.session_state.user_name)

        if all_sessions:
            session_titles = list(all_sessions.values())
            session_ids = list(all_sessions.keys())

            try:
                current_idx = session_ids.index(st.session_state.current_session_id)
            except ValueError:
                current_idx = 0 if session_titles else -1

            initial_index = current_idx if current_idx >= 0 else 0

            selected_title = st.selectbox("Load Past Chat:", session_titles, index=initial_index, key="history_box")
            selected_id = session_ids[session_titles.index(selected_title)]

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📂 Load Selected Chat"):
                    all_data = load_all_history()
                    loaded_msgs = all_data[st.session_state.user_name]['sessions'][selected_id]["messages"]
                    loaded_title = all_data[st.session_state.user_name]['sessions'][selected_id]["title"]

                    st.session_state.messages = loaded_msgs
                    st.session_state.current_session_id = selected_id
                    st.session_state.current_session_title = loaded_title
                    st.success(f"Chat Loaded: {loaded_title}")
                    time.sleep(1)
                    st.rerun()

            with col2:
                if st.button("🗑️ Delete Selected Chat"):
                    is_current_chat = (selected_id == st.session_state.current_session_id)

                    if delete_chat_session(st.session_state.user_name, selected_id):
                        st.success(f"Deleted: {selected_title}")

                        if is_current_chat:
                            st.session_state.messages = []
                            st.session_state.current_session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                            st.session_state.current_session_title = f"New Chat with {st.session_state.active_bot_name}"

                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Deletion failed.")

        st.markdown("---")

        with st.expander("💡 Available Commands"):
            st.markdown(
                """
                | Command | Use Case |
                | :--- | :--- |
                | **`/web [query]`** | Current internet se search karke jawab deta hai. |
                | **`/convert [val] [u1] to [u2]`** | Units convert karta hai (e.g., `/convert 5 kg to lbs`). |
                | **`/todo [task]`** | To-do list mein item add karta hai. |
                | **`/list`** | Pending To-Do items dikhata hai. |
                | **`/clear`** | Current chat ko save karke screen clear karta hai. |
                | **`/secret [code]`** | Subscriber mode on karta hai. |
                """
            )

        st.markdown("---")
        st.caption("AmritAI v32.2 (Web Fix & Auth Removed)")
        if st.button("🚪 Logout"):
            if st.session_state.messages:
                 save_current_chat(st.session_state.user_name, st.session_state.current_session_id, st.session_state.current_session_title, st.session_state.messages)
            st.session_state.user_name = None
            st.session_state.messages = []
            st.session_state.active_bot_name = "AmritAI" 
            st.rerun()

    # --- MAIN CHAT AREA ---
    st.title(f"🤖 AmritAI Ultimate ({st.session_state.active_bot_name})")

    # Greeting Message Fix
    if st.session_state.current_session_title.startswith("New Chat") and len(st.session_state.messages) == 0:
        st.success(get_greeting(st.session_state.user_name))

    # Display History 
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("is_image"): st.image(msg["content"])
            else: st.markdown(msg["content"])

    # User Input
    if prompt := st.chat_input(f"Message {st.session_state.user_name}..."):
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        current_sys_prompt = get_system_prompt()

        # --- COMMANDS ---

        if prompt.lower() == "/clear":
            if st.session_state.messages:
                save_current_chat(st.session_state.user_name, st.session_state.current_session_id, st.session_state.current_session_title, st.session_state.messages)
            st.session_state.messages = []
            st.session_state.current_session_title = f"New Chat with {st.session_state.active_bot_name}"
            st.rerun()

        elif prompt.lower().startswith("/secret"):
            code = prompt[7:].strip()
            with st.chat_message("assistant"):
                resp = "🔥 Subscriber Mode ON!" if code == SECRET_YOUTUBER_CODE else "❌ Wrong Code."
            st.markdown(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})

        elif prompt.lower().startswith("/convert"):
            match = re.match(r"/convert\s*([\d.]+)\s*(\w+)\s*to\s*(\w+)", prompt.strip(), re.IGNORECASE)
            with st.chat_message("assistant"):
                resp = convert_units(float(match.group(1)), match.group(2), match.group(3)) if match else "Format Error."
            st.markdown(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})

        elif prompt.lower() == "/list":
            with st.chat_message("assistant"):
                resp = list_tasks()
            st.markdown(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})

        elif prompt.lower().startswith("/todo"):
            task = prompt[5:].strip()
            if task:
                st.session_state.tasks.append(task)
                resp = f"✅ Task added: **{task}**"
            else:
                resp = "❌ Please provide a task."
            with st.chat_message("assistant"):
                st.markdown(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})

        # 🔥 /WEB Command FIX with Confirmation and Clear Error Display
        elif prompt.lower().startswith("/web"):
            query = prompt[4:].strip()

            if not query:
                with st.chat_message("assistant"):
                    resp = "❌ Bhai, /web ke baad search query bhi toh do!"
                    st.markdown(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})
            else:
                # 1. Confirmation Message
                confirmation_msg = f"✅ **Searching the web** for: *'{query}'*..."
                confirmation_placeholder = st.empty()
                with confirmation_placeholder.chat_message("assistant"):
                    st.markdown(confirmation_msg)

                # 2. Get Search Context
                context = search_web(query)

                # 3. Handle Errors (Key Missing/Failure)
                if "⚠️ Tavily Key Missing" in context or "Error: Tavily API call failed" in context:
                    final_resp = context
                    # Display the error clearly
                    with confirmation_placeholder.chat_message("assistant"):
                        st.markdown(final_resp)
                elif "No results found" in context:
                     final_resp = "⚠️ Web search successful, but no relevant results found. Try a different query."
                     with confirmation_placeholder.chat_message("assistant"):
                        st.markdown(final_resp)
                else:
                    # 4. Prepare Tool Prompt for AI
                    tool_prompt = f"""
                    You have performed a web search. The results are provided below in the 'tool_output'.
                    Based ONLY on the provided search results, generate a concise and helpful answer in Hinglish.
                    If the search results are insufficient, state that clearly.

                    --- SEARCH CONTEXT ---
                    {context}
                    --- END CONTEXT ---

                    User's Original Query: {query}
                    """

                    # Use the tool_prompt as the immediate system context
                    api_hist = [{"role": "system", "content": tool_prompt}] + st.session_state.messages 

                    # Clear the confirmation placeholder and write the final response
                    confirmation_placeholder.empty() 
                    with st.chat_message("assistant"):
                        final_resp = st.write_stream(get_groq_response(api_hist))

                # 5. Save Final Message
                st.session_state.messages.append({"role": "assistant", "content": final_resp})


        # --- NORMAL CHAT & AI RESPONSE ---
        else:
            api_hist = [current_sys_prompt] + st.session_state.messages
            with st.chat_message("assistant"):
                resp = st.write_stream(get_groq_response(api_hist))
            st.session_state.messages.append({"role": "assistant", "content": resp})

        # 💾 POST-RESPONSE LOGIC

        # 1. Generate Title if chat is brand new
        if st.session_state.current_session_title.startswith("New Chat") and len(st.session_state.messages) > 1:
            with st.spinner("🤖 Generating chat title..."):
                new_title = generate_chat_title(st.session_state.messages)
                st.session_state.current_session_title = new_title
                save_current_chat(st.session_state.user_name, st.session_state.current_session_id, st.session_state.current_session_title, st.session_state.messages)
                st.rerun() 

        # 2. Save latest AI message
        else:
            save_current_chat(st.session_state.user_name, st.session_state.current_session_id, st.session_state.current_session_title, st.session_state.messages)
