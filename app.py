import os
import json
import requests
import streamlit as st
import google.generativeai as genai
from tavily import TavilyClient

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="Zaid AI | Intelligent Assistant", page_icon="🪐", layout="centered", initial_sidebar_state="expanded")

# ============================================================
# CUSTOM STYLING (original design retained)
# ============================================================
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);}
.hero-title {text-align:center;font-size:2.6rem;font-weight:800;background:linear-gradient(90deg,#00c6ff,#a855f7,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0px;}
.hero-subtitle {text-align:center;color:#c9c9d9;font-size:1rem;margin-top:-5px;margin-bottom:20px;}
.chip-row {display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-bottom:25px;}
.chip {background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:20px;padding:6px 16px;font-size:0.85rem;color:#f0f0f5;backdrop-filter:blur(6px);}
div[data-testid="stChatMessage"] {border-radius:16px;padding:6px 4px;margin-bottom:8px;}
section[data-testid="stSidebar"] {background:linear-gradient(180deg,#1a1a2e 0%,#16213e 100%);}
section[data-testid="stSidebar"] * {color:#eaeaf0 !important;}
.stChatInput textarea {border-radius:14px !important;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SECRETS
# ============================================================
def get_secret(key, default=""):
    try:
        value = st.secrets.get(key, default)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(key, default)

GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")
GROQ_API_KEY = get_secret("GROQ_API_KEY")
OPENWEATHER_API_KEY = get_secret("OPENWEATHER_API_KEY")
TAVILY_API_KEY = get_secret("TAVILY_API_KEY")
GEMINI_MODEL_NAME = get_secret("GEMINI_MODEL", "gemini-flash-latest")
GROQ_MODEL_NAME = get_secret("GROQ_MODEL", "llama-3.3-70b-versatile")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

# ============================================================
# KNOWLEDGE BASE + TOOLS
# ============================================================
LINK_KNOWLEDGE_BASE = {
    "capcut": "https://www.capcut.com/",
    "vs code": "https://code.visualstudio.com/download",
    "anaconda": "https://www.anaconda.com/download"
}
SYSTEM_INSTRUCTION = """You are a helpful and powerful AI assistant. Provide accurate, clear and up-to-date answers. For current events, real-time information, or links not in the knowledge base, use the web search tool. If a user asks for a link to a known application, use get_link first. Do not claim to have searched unless the search tool was used."""

def get_link(app_name: str):
    key = app_name.lower().strip()
    if key in LINK_KNOWLEDGE_BASE:
        url = LINK_KNOWLEDGE_BASE[key]
        return f"Here is the link for {app_name}: [{url}]({url})"
    return f"Sorry, I don't have a pre-defined link for {app_name}. You can ask me to search the web for it."

def get_live_weather(city: str):
    if not OPENWEATHER_API_KEY:
        return "Weather is not configured. Add OPENWEATHER_API_KEY to Streamlit Secrets."
    try:
        response = requests.get("https://api.openweathermap.org/data/2.5/weather", params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}, timeout=15)
        response.raise_for_status()
        data = response.json()
        return f"The current weather in {city} is {data['main']['temp']}°C with {data['weather'][0]['description']}."
    except requests.exceptions.RequestException as ex:
        return f"Could not fetch weather data: {ex}"
    except (KeyError, ValueError):
        return "Weather service returned an unexpected response."

def perform_web_search(query: str):
    if not tavily_client:
        return "Web search is not configured. Add TAVILY_API_KEY to Streamlit Secrets."
    try:
        results = tavily_client.search(query=query, search_depth="basic").get("results", [])
        if not results:
            return "No useful search results were found."
        return "\n".join(f"- {r.get('title', 'Result')}: {r.get('content', '')} ({r.get('url', '')})" for r in results[:5])
    except Exception as ex:
        return f"Could not perform web search: {ex}"

def run_tool(name, args):
    try:
        if name == "get_link": return get_link(**args)
        if name == "get_live_weather": return get_live_weather(**args)
        if name == "perform_web_search": return perform_web_search(**args)
        return f"Unknown tool: {name}"
    except Exception as ex:
        return f"Tool {name} failed: {ex}"

# ============================================================
# GEMINI: primary provider. No test prompts at startup, to avoid
# wasting free-tier quota before the user sends a message.
# ============================================================
def build_gemini_chat():
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is missing from Streamlit Secrets.")
    model = genai.GenerativeModel(model_name=GEMINI_MODEL_NAME, tools=[get_live_weather, perform_web_search, get_link], system_instruction=SYSTEM_INSTRUCTION)
    return model.start_chat(enable_automatic_function_calling=True)

# ============================================================
# GROQ: fallback provider, including tool-calling support
# ============================================================
GROQ_TOOLS = [
    {"type":"function","function":{"name":"get_live_weather","description":"Get current weather for a city.","parameters":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}},
    {"type":"function","function":{"name":"perform_web_search","description":"Search the web for current information.","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
    {"type":"function","function":{"name":"get_link","description":"Get a known application website or download link.","parameters":{"type":"object","properties":{"app_name":{"type":"string"}},"required":["app_name"]}}}
]

def ask_groq():
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing. Add a Groq API key to Streamlit Secrets to enable fallback.")
    msgs = [{"role":"system","content":SYSTEM_INSTRUCTION}]
    # The current user prompt is already included in session history.
    for item in st.session_state.messages:
        if item.get("role") in ("user", "assistant") and item.get("content"):
            msgs.append({"role":item["role"],"content":item["content"]})
    headers = {"Authorization":f"Bearer {GROQ_API_KEY}","Content-Type":"application/json"}
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    for _ in range(6):
        payload = {"model":GROQ_MODEL_NAME,"messages":msgs,"tools":GROQ_TOOLS,"tool_choice":"auto","temperature":0.5}
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        if not response.ok:
            try:
                detail = response.json().get("error",{}).get("message",response.text)
            except ValueError:
                detail = response.text
            raise RuntimeError(f"Groq API error ({response.status_code}): {detail}")
        assistant_msg = response.json()["choices"][0]["message"]
        calls = assistant_msg.get("tool_calls") or []
        if not calls:
            return assistant_msg.get("content") or "I couldn't generate a response."
        msgs.append(assistant_msg)
        for call in calls:
            fn = call.get("function",{})
            try:
                args = json.loads(fn.get("arguments","{}"))
            except json.JSONDecodeError:
                args = {}
            result = run_tool(fn.get("name",""), args)
            msgs.append({"role":"tool","tool_call_id":call["id"],"content":str(result)})
    raise RuntimeError("Groq reached the tool-call limit. Please try again.")

# ============================================================
# SESSION STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"assistant","content":"👋 Hey! I'm your AI Assistant. Ask me anything — I can check live weather, search the web, or grab app links for you."}]
if "gemini_chat" not in st.session_state:
    try:
        st.session_state.gemini_chat = build_gemini_chat()
    except Exception:
        st.session_state.gemini_chat = None
if "active_provider" not in st.session_state:
    st.session_state.active_provider = "Gemini"

AVATARS = {"user":"🧑‍💻","assistant":"🪐"}

def reset_conversation():
    st.session_state.messages = [{"role":"assistant","content":"👋 Fresh start! What can I help you with?"}]
    st.session_state.active_provider = "Gemini"
    try:
        st.session_state.gemini_chat = build_gemini_chat()
    except Exception:
        st.session_state.gemini_chat = None

# ============================================================
# SIDEBAR (original content retained; provider status added)
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
    st.markdown("### ⚙️ AI Provider")
    if st.session_state.active_provider == "Gemini":
        st.markdown(f"`{GEMINI_MODEL_NAME}` · Primary")
        st.caption("Groq will take over automatically if Gemini fails.")
    else:
        st.markdown(f"`{GROQ_MODEL_NAME}` · Backup")
        st.caption("Gemini failed earlier in this conversation; using Groq.")
    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        reset_conversation()
        st.rerun()

# ============================================================
# HEADER (original design retained)
# ============================================================
st.markdown('<div class="hero-title">🪐 Zaid AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Real-time answers, live weather & smart links — all in one chat</div>', unsafe_allow_html=True)
provider_chip = GEMINI_MODEL_NAME if st.session_state.active_provider == "Gemini" else f"Groq · {GROQ_MODEL_NAME}"
st.markdown(f"""
<div class="chip-row">
<div class="chip">🌦️ Live Weather</div><div class="chip">🔍 Web Search</div>
<div class="chip">🔗 App Links</div><div class="chip">⚡ {provider_chip}</div>
<div class="chip">🔁 Auto Backup</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# CHAT HISTORY
# ============================================================
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=AVATARS.get(message["role"], "🤖")):
        st.markdown(message["content"])

# ============================================================
# CHAT LOGIC: Gemini first, then switch to Groq on any Gemini error
# ============================================================
if prompt := st.chat_input("Ask me anything... 🚀"):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        placeholder = st.empty()
        with st.spinner("✨ Thinking..."):
            try:
                if st.session_state.active_provider == "Gemini":
                    try:
                        if st.session_state.gemini_chat is None:
                            st.session_state.gemini_chat = build_gemini_chat()
                        response = st.session_state.gemini_chat.send_message(prompt)
                        final_response = response.text
                        used_provider = "Gemini"
                    except Exception as gemini_error:
                        st.session_state.active_provider = "Groq"
                        st.warning("Gemini is unavailable or its quota has been reached. Switching to Groq backup...")
                        try:
                            final_response = ask_groq()
                            used_provider = "Groq"
                        except Exception as groq_error:
                            raise RuntimeError(f"Gemini error: {gemini_error}\n\nGroq error: {groq_error}")
                else:
                    final_response = ask_groq()
                    used_provider = "Groq"
                placeholder.markdown(final_response)
                st.caption(f"Response generated by {used_provider}")
            except Exception as ex:
                final_response = f"⚠️ Sorry, I couldn't process that request.\n\nDetails: {ex}"
                placeholder.error(final_response)
    st.session_state.messages.append({"role":"assistant","content":final_response})
