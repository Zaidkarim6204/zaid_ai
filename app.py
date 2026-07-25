import streamlit as st
import google.generativeai as genai
import requests
from tavily import TavilyClient

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Zaid AI | Intelligent Assistant",
    page_icon="🪐",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM STYLING
# ============================================================
st.markdown("""
<style>
    /* Overall app background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }

    /* Title */
    .hero-title {
        text-align: center;
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00c6ff, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .hero-subtitle {
        text-align: center;
        color: #c9c9d9;
        font-size: 1rem;
        margin-top: -5px;
        margin-bottom: 20px;
    }

    /* Capability chips */
    .chip-row {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 25px;
    }
    .chip {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 0.85rem;
        color: #f0f0f5;
        backdrop-filter: blur(6px);
    }

    /* Chat bubbles */
    div[data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 6px 4px;
        margin-bottom: 8px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #eaeaf0 !important;
    }

    /* Input box */
    .stChatInput textarea {
        border-radius: 14px !important;
    }

    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# API KEY CONFIGURATION
# ============================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]

    genai.configure(api_key=GOOGLE_API_KEY)
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

except (FileNotFoundError, KeyError) as e:
    st.error(f"🔑 Secrets file or key not found: {e}. Please check your .streamlit/secrets.toml file.")
    st.stop()

# ============================================================
# KNOWLEDGE BASE
# ============================================================
LINK_KNOWLEDGE_BASE = {
    "capcut": "https://www.capcut.com/",
    "vs code": "https://code.visualstudio.com/download",
    "anaconda": "https://www.anaconda.com/download"
}

# ============================================================
# TOOL FUNCTIONS
# ============================================================
def get_link(app_name: str):
    """
    Provides a download or website link for a specific, known application.
    Use this tool when a user asks for a link to an app in the knowledge base.
    """
    app_key = app_name.lower().strip()
    if app_key in LINK_KNOWLEDGE_BASE:
        url = LINK_KNOWLEDGE_BASE[app_key]
        return f"Here is the link for {app_name}: [{url}]({url})"
    else:
        return f"Sorry, I don't have a pre-defined link for {app_name}. You can ask me to search the web for it."


def get_live_weather(city: str):
    """Fetches the current weather for a given city."""
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        data = response.json()
        return f"The current weather in {city} is {data['main']['temp']}°C with {data['weather'][0]['description']}."
    except requests.exceptions.RequestException as ex:
        return f"Could not fetch weather data. Error: {ex}"


def perform_web_search(query: str):
    """
    Use this tool to get real-time information from the internet, or to find links not in the knowledge base.
    It is ideal for current events, recent discoveries, or any up-to-the-minute information.
    """
    try:
        response = tavily_client.search(query=query, search_depth="basic")
        return "\n".join([f"- {res['content']}" for res in response['results']])
    except Exception as ex:
        return f"Could not perform web search. Error: {ex}"


# ============================================================
# MODEL AND CHAT CONFIGURATION
# ============================================================
system_instruction = """You are a helpful and powerful AI assistant. Your goal is to provide accurate, up-to-date answers.
For any question about current events, real-time information, or to find links not in your knowledge base, you MUST use your web search tool.
If a user asks for a link to a specific application, you should use the 'get_link' tool first."""

# FIXED MODEL NAME: Using the standard stable 'gemini-1.5-flash' identifier
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    tools=[get_live_weather, perform_web_search, get_link],
    system_instruction=system_instruction
)

if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(enable_automatic_function_calling=True)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hey! I'm your AI Assistant. Ask me anything — I can check live weather, search the web, or grab app links for you."}
    ]

# Avatars
AVATARS = {
    "user": "🧑‍💻",
    "assistant": "🪐"
}

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 🪐 Zaid AI")
    st.markdown("Your all-in-one intelligent assistant.")
    st.markdown("---")
    st.markdown("### 🧰 Capabilities")
    st.markdown("🌦️ **Live Weather** — real-time conditions for any city")
    st.markdown("🔍 **Web Search** — up-to-the-minute answers, powered by Tavily")
    st.markdown("🔗 **Smart Links** — instant download links for known apps")
    st.markdown("---")
    st.markdown("### ⚙️ Model")
    st.markdown("`gemini-1.5-flash`")
    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.chat = model.start_chat(enable_automatic_function_calling=True)
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 Fresh start! What can I help you with?"}
        ]
        st.rerun()

# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="hero-title">🪐 Zaid AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Real-time answers, live weather & smart links — all in one chat</div>', unsafe_allow_html=True)

st.markdown("""
<div class="chip-row">
    <div class="chip">🌦️ Live Weather</div>
    <div class="chip">🔍 Web Search</div>
    <div class="chip">🔗 App Links</div>
    <div class="chip">⚡ Gemini 1.5 Flash</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# CHAT HISTORY DISPLAY
# ============================================================
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=AVATARS.get(message["role"], "🤖")):
        st.markdown(message["content"])

# ============================================================
# MAIN CHAT LOGIC
# ============================================================
if prompt := st.chat_input("Ask me anything... 🚀"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        message_placeholder = st.empty()
        with st.spinner("✨ Thinking..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                final_response = response.text
                message_placeholder.markdown(final_response)
            except Exception as e:
                final_response = f"⚠️ An error occurred: {e}"
                message_placeholder.markdown(final_response)

    st.session_state.messages.append({"role": "assistant", "content": final_response})
