import os
import requests
import streamlit as st
import google.generativeai as genai
from tavily import TavilyClient

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Zaid AI | Intelligent Assistant",
    page_icon="🪐",
    layout="centered"
)

# ============================================================
# API KEYS AND SETTINGS
# ============================================================

def get_secret(name, default=""):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")
GROQ_API_KEY = get_secret("GROQ_API_KEY")
TAVILY_API_KEY = get_secret("TAVILY_API_KEY")
OPENWEATHER_API_KEY = get_secret("OPENWEATHER_API_KEY")

GEMINI_MODEL = get_secret("GEMINI_MODEL", "gemini-3.8-flash")
GROQ_MODEL = get_secret("GROQ_MODEL", "openai/gpt-oss-120b")

# ============================================================
# CUSTOM DESIGN
# ============================================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #100b25, #211044, #10152d);
    color: white;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 850px;
    padding-top: 2rem;
}

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    background: linear-gradient(90deg, #c084fc, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    text-align: center;
    color: #c4b5fd;
    margin-bottom: 25px;
}

.stChatMessage {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 15px;
    padding: 12px;
}

.stChatInput textarea {
    background: #211a3c;
    color: white;
}

div[data-testid="stSidebar"] {
    background: #15102a;
}

.stButton button {
    border-radius: 10px;
    border: 1px solid #8b5cf6;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🪐 Zaid AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Your Intelligent AI Assistant</div>',
    unsafe_allow_html=True
)

# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_provider" not in st.session_state:
    st.session_state.active_provider = "Gemini"

if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = None

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🪐 Zaid AI")
    st.caption("Intelligent Assistant")

    st.divider()

    st.markdown("### AI Provider")

    if st.session_state.active_provider == "Gemini":
        st.success("Gemini Active")
    else:
        st.warning("Groq Active")

    st.caption("Gemini is primary. Groq is automatic backup.")

    st.divider()

    st.markdown("### Available Features")
    st.write("🌦️ Live weather")
    st.write("🌐 Web search")
    st.write("🔗 App links")
    st.write("💬 AI conversation")

    st.divider()

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.active_provider = "Gemini"
        st.session_state.gemini_chat = None
        st.rerun()

    st.caption("Built with Python and Streamlit")

# ============================================================
# WEATHER FUNCTION
# ============================================================

def get_live_weather(city):
    if not OPENWEATHER_API_KEY:
        return "Weather API key is missing."

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"

        response = requests.get(
            url,
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            },
            timeout=15
        )

        data = response.json()

        if response.status_code != 200:
            return data.get("message", "Unable to get weather.")

        temperature = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]

        return (
            f"Weather in {city.title()}:\n"
            f"Temperature: {temperature}°C\n"
            f"Feels like: {feels_like}°C\n"
            f"Conditions: {description}\n"
            f"Humidity: {humidity}%"
        )

    except Exception as e:
        return f"Weather error: {e}"

# ============================================================
# WEB SEARCH FUNCTION
# ============================================================

def perform_web_search(query):
    if not TAVILY_API_KEY:
        return "Tavily API key is missing."

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)

        results = client.search(
            query=query,
            max_results=5
        )

        output = []

        for item in results.get("results", []):
            output.append(
                f"Title: {item.get('title', '')}\n"
                f"Content: {item.get('content', '')}\n"
                f"URL: {item.get('url', '')}"
            )

        return "\n\n".join(output) if output else "No results found."

    except Exception as e:
        return f"Search error: {e}"

# ============================================================
# APP LINKS FUNCTION
# ============================================================

def get_link(app_name):
    apps = {
        "weather": "https://zaid-weather.streamlit.app/",
        "crypto": "https://zaid-crypto.streamlit.app/",
        "news": "https://zaid-news.streamlit.app/",
        "dashboard": "https://zaid-multidashboard.streamlit.app/"
    }

    key = app_name.lower().strip()

    for name, url in apps.items():
        if name in key:
            return f"Here is your {name} app: {url}"

    return "I couldn't find that app link."

# ============================================================
# SIMPLE TOOL ROUTER
# ============================================================

def handle_special_request(prompt):
    text = prompt.lower().strip()

    # Weather requests
    weather_words = [
        "weather", "temperature", "forecast",
        "how hot", "how cold"
    ]

    if any(word in text for word in weather_words):
        city = ""

        for phrase in [" in ", " at ", " for "]:
            if phrase in text:
                city = text.split(phrase)[-1].strip()
                break

        city = city.replace("?", "").replace(".", "")

        if city:
            return get_live_weather(city)

    # App link requests
    if any(word in text for word in [
        "app link", "website link", "open my app",
        "crypto app", "weather app", "news app",
        "dashboard link"
    ]):
        return get_link(text)

    # Web search requests
    search_triggers = [
        "search the web",
        "search online",
        "search for",
        "latest news",
        "find online",
        "look up"
    ]

    if any(trigger in text for trigger in search_triggers):
        query = prompt

        for trigger in search_triggers:
            if trigger in text:
                index = text.find(trigger)
                query = prompt[index + len(trigger):].strip()
                break

        if query:
            return perform_web_search(query)

    return None

# ============================================================
# GEMINI SETUP
# ============================================================

def ask_gemini(prompt):
    global_model = None

    if not GOOGLE_API_KEY:
        raise Exception("Google Gemini API key is missing.")

    genai.configure(api_key=GOOGLE_API_KEY)

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=(
            "You are Zaid AI, a helpful, intelligent assistant. "
            "Give clear, accurate and friendly answers. "
            "Use concise explanations when appropriate."
        )
    )

    if st.session_state.gemini_chat is None:
        history = []

        for message in st.session_state.messages[:-1]:
            history.append({
                "role": (
                    "user" if message["role"] == "user"
                    else "model"
                ),
                "parts": [message["content"]]
            })

        st.session_state.gemini_chat = model.start_chat(
            history=history
        )

    response = st.session_state.gemini_chat.send_message(prompt)

    return response.text

# ============================================================
# GROQ BACKUP
# ============================================================

def ask_groq(prompt):
    if not GROQ_API_KEY:
        raise Exception("Groq API key is missing.")

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [{
        "role": "system",
        "content": (
            "You are Zaid AI, a helpful and intelligent assistant. "
            "Give clear, accurate and friendly answers."
        )
    }]

    for message in st.session_state.messages:
        messages.append({
            "role": message["role"],
            "content": message["content"]
        })

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        try:
            error_message = response.json()["error"]["message"]
        except Exception:
            error_message = response.text

        raise Exception(
            f"Groq API error ({response.status_code}): "
            f"{error_message}"
        )

    result = response.json()

    return result["choices"][0]["message"]["content"]

# ============================================================
# AI RESPONSE HANDLER
# ============================================================

def generate_response(prompt):

    # Check local tools first
    tool_result = handle_special_request(prompt)

    if tool_result:
        return tool_result

    # Try Gemini first
    if st.session_state.active_provider == "Gemini":
        try:
            return ask_gemini(prompt)

        except Exception as gemini_error:
            st.session_state.active_provider = "Groq"
            st.session_state.gemini_chat = None

            if not GROQ_API_KEY:
                raise Exception(
                    f"Gemini failed: {gemini_error}\n\n"
                    "Groq API key is missing."
                )

            st.warning(
                "⚠️ Gemini is unavailable. "
                "Automatically switching to Groq..."
            )

    # Groq fallback
    try:
        return ask_groq(prompt)

    except Exception as groq_error:
        raise Exception(
            f"Gemini is unavailable and Groq failed.\n\n"
            f"Groq details: {groq_error}"
        )

# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

if not st.session_state.messages:
    st.markdown(
        "👋 Hey! I'm your AI Assistant. "
        "Ask me anything — I can check live weather, "
        "search the web, or grab app links for you."
    )

for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "🪐"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# ============================================================
# CHAT INPUT
# ============================================================

if prompt := st.chat_input("Message Zaid AI..."):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🪐"):
        try:
            with st.spinner("Thinking..."):
                answer = generate_response(prompt)

            st.markdown(answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as e:
            st.error("⚠️ Sorry, I couldn't process that request.")
            st.caption(f"Details: {e}")
