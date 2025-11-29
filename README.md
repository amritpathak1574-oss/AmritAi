🤖 AmritAI UltimateWelcome to AmritAI Ultimate! This is a powerful, multi-featured chat application built using Streamlit and the Groq API for fast, AI-powered responses. It integrates real-time web search capabilities using the Tavily API and includes features like custom bot creation, chat history, and utility commands.🌟 Key Features⚡ Groq Integration: Super fast AI responses using Groq's low-latency API (Llama 3.1 8B).🌐 Realtime Web Search: Use the /web [query] command to fetch current information from the internet via the Tavily API.💾 Local Chat History: Saves chat sessions and custom bot configurations locally in a JSON file.🤖 Custom Bots: Create and use AI personas with dedicated system prompts.🛠️ Utility Commands: Includes commands for unit conversion (/convert), to-do list management (/todo, /list), and more.🚀 Streamlit Deployment Ready: Fully structured for easy deployment on Streamlit Community Cloud.🛠️ Installation and Setup1. DependenciesYou need to install the following Python libraries. Create a file named requirements.txt and add these dependencies:Plaintext# requirements.txt
streamlit
requests
tavily
Install them using pip:Bashpip install -r requirements.txt
2. API Keys Setup (Crucial Step)For the application to function, you must provide your API keys. Since this app uses Streamlit, the safest way is to use a .streamlit/secrets.toml file.Create a folder named .streamlit in your main project directory.Inside the .streamlit folder, create a file named secrets.toml.Add your keys in the following format:Ini, TOML# .streamlit/secrets.toml

# 1. Groq API Key (For AI responses)
GROQ_KEY = "your_groq_api_key_here"

# 2. Tavily API Key (For /web search command)
TAVILY_KEY = "your_tavily_api_key_here"
Note: For local development, you can also set these as system environment variables.3. Initialize Data FileCreate an empty file named chat_history.json in the main directory. The app will use this file to save user data, chat sessions, and custom bots.Bashtouch chat_history.json 
# Add empty JSON structure to chat_history.json: {}
💻 How to RunEnsure all dependencies are installed and API keys are set up.Run the application using Streamlit:Bashstreamlit run main.py
The app will open in your browser, prompting you to enter a username to begin.📝 Usage and CommandsAmritAI supports special commands that provide utility functions and access to real-time information.CommandDescriptionExample/web [query]Performs a real-time internet search and uses the context to answer. (Requires TAVILY_KEY)/web who won the cricket world cup 2023/convert [val] [u1] to [u2]Converts common units (kg/lbs, km/miles, C/F)./convert 5 kg to lbs/todo [task]Adds a new item to your local to-do list./todo finish the Streamlit app/listDisplays all pending items in your to-do list./list/clearSaves the current chat session and clears the screen to start a new conversation./clear/secret chiku03Activates the special Subscriber Mode (Energetic/YouTuber tone)./secret chiku03
