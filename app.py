import os
import re
import json
import requests
import streamlit as st
import google.generativeai as genai
from tavily import TavilyClient
from datetime import datetime

# ============================================================
# ZAID AI — PREMIUM PURPLE AI WORKSPACE
# ============================================================

st.set_page_config(
    page_title="Zaid AI | Your AI Workspace",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- CONFIGURATION -------------------------

def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, None)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)

GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")
GROQ_API_KEY = get_secret("GROQ_API_KEY")
TAVILY_API_KEY = get_secret("TAVILY_API_KEY")
OPENWEATHER_API_KEY = get_secret("OPENWEATHER_API_KEY")
GEMINI_MODEL = get_secret("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_MODEL = get_secret("GROQ_MODEL", "openai/gpt-oss-120b")

APP_LINKS = {
    "Weather": "https://zaid-weather.streamlit.app/",
    "Crypto": "https://zaid-crypto.streamlit.app/",
    "News": "https://zaid-news.streamlit.app/",
    "Dashboard": "https://zaid-multidashboard.streamlit.app/",
}

# -------------------- SESSION STATE -------------------------

defaults = {
    "messages": [],
    "archived_chats": [],
    "active_provider": "Gemini",
    "selected_model": "Gemini",
    "page": "Chat",
    "gemini_chat": None,
    "chat_title": "New Chat",
    "chat_started": False,
    "output_count": 0,
    "search_count": 0,
    "weather_count": 0,
    "request_count": 0,
    "pending_prompt": None,
    "library_items": [],
    "show_config": False,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -------------------- CUSTOM CSS ----------------------------

st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg: #090611;
    --panel: rgba(29, 20, 46, .78);
    --panel2: rgba(43, 27, 64, .62);
    --line: rgba(211, 177, 255, .15);
    --muted: #b7a9c9;
    --purple: #a855f7;
    --pink: #e879f9;
    --blue: #818cf8;
}
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp {
    color: #f8f4ff;
    background:
      radial-gradient(ellipse at 52% 4%, rgba(126, 34, 206, .22), transparent 36%),
      radial-gradient(ellipse at 92% 30%, rgba(88, 28, 135, .16), transparent 30%),
      linear-gradient(135deg, #090611 0%, #130b20 52%, #090b18 100%);
}
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1450px; padding-top: 1.2rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(19, 12, 31, .99), rgba(12, 10, 22, .99));
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
.brand-row { display:flex; align-items:center; gap:11px; padding:7px 2px 18px; }
.brand-orb {
    width:40px;height:40px;border-radius:14px;display:flex;align-items:center;justify-content:center;
    background:linear-gradient(135deg,#a855f7,#6d28d9 55%,#4f46e5);
    box-shadow:0 0 25px rgba(168,85,247,.4);font-size:21px;
}
.brand-name {font-family:'Space Grotesk';font-size:21px;font-weight:700;color:#fff;line-height:1.1;}
.brand-sub {font-size:11px;color:#a99abf;margin-top:3px;}
.side-label {font-size:10px;color:#877a9a;letter-spacing:1.4px;text-transform:uppercase;font-weight:700;margin:16px 0 7px;}
.hero {text-align:center;padding:38px 10px 12px;}
.hero-orb {
    width:72px;height:72px;border-radius:50%;margin:0 auto 18px;display:flex;align-items:center;justify-content:center;
    font-size:31px;color:#fff;
    background:radial-gradient(circle at 32% 25%,#f0abfc 0%,#a855f7 27%,#6b21a8 58%,#251044 100%);
    box-shadow:0 0 20px rgba(192,132,252,.55),0 0 55px rgba(147,51,234,.35),inset 0 2px 10px rgba(255,255,255,.35);
    border:1px solid rgba(233,213,255,.45);
}
.hero h1 {font-family:'Space Grotesk';font-size:clamp(27px,4vw,40px);font-weight:600;letter-spacing:-1.3px;margin:0;color:#fff;}
.hero p {color:#b7a9c9;font-size:14px;margin:9px auto 0;max-width:570px;}
.topbar {
    display:flex;align-items:center;justify-content:space-between;gap:10px;
    background:rgba(26,17,40,.72);border:1px solid var(--line);border-radius:16px;padding:10px 14px;margin-bottom:12px;
}
.pill {
    display:inline-flex;align-items:center;gap:7px;padding:6px 11px;border:1px solid var(--line);
    border-radius:999px;background:rgba(255,255,255,.045);font-size:11px;color:#d9c8ee;
}
.dot {width:7px;height:7px;border-radius:50%;background:#4ade80;box-shadow:0 0 9px #4ade80;}
.panel {
    background:linear-gradient(145deg,rgba(42,27,61,.75),rgba(22,17,36,.88));
    border:1px solid var(--line);border-radius:18px;padding:17px 18px;
    box-shadow:0 12px 35px rgba(0,0,0,.12);
}
.panel-title {font-size:13px;font-weight:700;color:#eee5fa;margin-bottom:5px;}
.panel-sub {font-size:11px;color:#9f91b2;}
.metric {font-family:'Space Grotesk';font-size:27px;font-weight:700;color:#fff;margin-top:8px;}
.metric-note {font-size:10px;color:#a78bfa;margin-top:2px;}
.section-heading {font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#cbb8e2;margin:20px 0 10px;}
.feature-card {
    min-height:122px;padding:16px;border-radius:17px;border:1px solid var(--line);
    background:linear-gradient(145deg,rgba(55,31,77,.70),rgba(24,18,39,.85));
}
.feature-icon {font-size:22px;margin-bottom:9px;}
.feature-name {font-size:13px;font-weight:700;color:#fff;}
.feature-desc {font-size:10px;color:#a99bb9;line-height:1.5;margin-top:5px;}
.stButton > button {
    border:1px solid rgba(192,132,252,.24);border-radius:11px;
    background:rgba(139,92,246,.12);color:#f1e8ff;font-weight:600;
    min-height:38px;transition:all .18s ease;
}
.stButton > button:hover {border-color:#c084fc;background:rgba(168,85,247,.23);color:#fff;}
.stButton > button[kind="primary"] {
    background:linear-gradient(100deg,#9333ea,#6d28d9);border:0;color:white;
}
[data-testid="stChatMessage"] {
    background:rgba(255,255,255,.045);border:1px solid rgba(211,177,255,.12);
    border-radius:17px;padding:12px 15px;margin-bottom:10px;
}
[data-testid="stChatInput"] {
    background:rgba(31,21,47,.96);border:1px solid rgba(192,132,252,.32);border-radius:16px;
}
[data-testid="stChatInput"] textarea {color:#fff;}
[data-testid="stChatInput"] button {background:linear-gradient(135deg,#a855f7,#7c3aed);}
div[data-testid="stSelectbox"] > div > div {background:rgba(32,22,48,.9);}
hr {border-color:rgba(211,177,255,.12);}
a {color:#c4b5fd !important;}
.small-muted {font-size:11px;color:#998ba9;}
@media(max-width:700px) {
 .block-container{padding: .7rem .7rem 2rem;}
 .hero{padding-top:22px;}
}
</style>
""", unsafe_allow_html=True)

# -------------------- API / TOOL FUNCTIONS -----------------

def get_weather(city: str) -> str:
    if not OPENWEATHER_API_KEY:
        return "Weather isn't configured yet. Add `OPENWEATHER_API_KEY` to your Codespaces secrets."
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=15,
        )
        data = r.json()
        if r.status_code != 200:
            return f"Couldn't get weather for {city}: {data.get('message', 'Unknown error')}."
        st.session_state.weather_count += 1
        w = data["weather"][0]
        return (
            f"### 🌦️ Weather in {data.get('name', city.title())}\n\n"
            f"- **Temperature:** {data['main']['temp']}°C\n"
            f"- **Feels like:** {data['main']['feels_like']}°C\n"
            f"- **Conditions:** {w['description'].capitalize()}\n"
            f"- **Humidity:** {data['main']['humidity']}%\n"
            f"- **Wind:** {data.get('wind', {}).get('speed', 'N/A')} m/s"
        )
    except requests.RequestException as e:
        return f"Weather connection error: {e}"
    except (KeyError, ValueError, TypeError):
        return "The weather service returned an unexpected response."

def web_search(query: str) -> str:
    if not TAVILY_API_KEY:
        return "Web search isn't configured yet. Add `TAVILY_API_KEY` to your Codespaces secrets."
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        result = client.search(query=query, max_results=5)
        rows = result.get("results", [])
        if not rows:
            return "No useful search results were found."
        st.session_state.search_count += 1
        output = ["### 🌐 Web search results"]
        for i, item in enumerate(rows, 1):
            title = item.get("title") or "Search result"
            url = item.get("url") or ""
            content = item.get("content") or ""
            output.append(f"**{i}. [{title}]({url})**\n\n{content}")
        return "\n\n".join(output)
    except Exception as e:
        return f"Search error: {e}"

def special_request(prompt: str):
    low = prompt.lower().strip()

    # User's personal app links
    if any(x in low for x in ["app link", "website link", "open my app", "link to my", "crypto app", "weather app", "news app", "dashboard link"]):
        for name, url in APP_LINKS.items():
            if name.lower() in low:
                return f"Here is your **{name} app**: {url}"
        return "Which app do you need? Weather, Crypto, News, or Dashboard?"

    # Weather
    if any(x in low for x in ["weather", "temperature", "forecast", "how hot", "how cold"]):
        match = re.search(r"\b(?:in|at|for)\s+([A-Za-z][A-Za-z .'-]*?)(?:\?|\.|$)", prompt, re.I)
        if match:
            return get_weather(match.group(1).strip())
        return "Which city should I check? Example: **Weather in Dubai**."

    # Explicit web-search commands
    triggers = ["search the web for", "search online for", "search for", "look up", "find online", "latest news about"]
    for trigger in triggers:
        if low.startswith(trigger):
            query = prompt[len(trigger):].strip(" :")
            return web_search(query) if query else "What should I search for?"
    return None

def ask_gemini(prompt: str) -> str:
    if not GOOGLE_API_KEY:
        raise RuntimeError("Gemini API key is missing. Add GOOGLE_API_KEY to Codespaces secrets.")
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=(
            "You are Zaid AI, a capable, friendly AI assistant. "
            "Answer accurately, structure responses clearly, and be concise when suitable. "
            "Never pretend to have performed actions you have not performed."
        ),
    )
    if st.session_state.gemini_chat is None:
        history = []
        for msg in st.session_state.messages[:-1]:
            history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]],
            })
        st.session_state.gemini_chat = model.start_chat(history=history)
    response = st.session_state.gemini_chat.send_message(prompt)
    answer = getattr(response, "text", None)
    if not answer:
        raise RuntimeError("Gemini returned an empty response.")
    return answer

def ask_groq() -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("Groq API key is missing. Add GROQ_API_KEY to Codespaces secrets.")
    messages = [{
        "role": "system",
        "content": "You are Zaid AI, a helpful and accurate AI assistant. Be clear, friendly and structured.",
    }]
    messages.extend({"role": m["role"], "content": m["content"]} for m in st.session_state.messages)
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": GROQ_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 2048},
        timeout=60,
    )
    if r.status_code != 200:
        try:
            detail = r.json().get("error", {}).get("message", r.text)
        except ValueError:
            detail = r.text
        raise RuntimeError(f"Groq API error {r.status_code}: {detail}")
    answer = r.json()["choices"][0]["message"]["content"]
    if not answer:
        raise RuntimeError("Groq returned an empty response.")
    return answer

def generate_answer(prompt: str) -> str:
    tool_answer = special_request(prompt)
    if tool_answer is not None:
        return tool_answer

    if st.session_state.active_provider == "Gemini":
        try:
            return ask_gemini(prompt)
        except Exception as gemini_error:
            st.session_state.active_provider = "Groq"
            st.session_state.gemini_chat = None
            if not GROQ_API_KEY:
                raise RuntimeError(f"Gemini failed: {gemini_error}\n\nGroq backup key is also missing.")
            st.warning("Gemini is unavailable. Switching to Groq backup…")

    return ask_groq()

def reset_chat():
    st.session_state.messages = []
    st.session_state.gemini_chat = None
    st.session_state.active_provider = "Gemini"
    st.session_state.chat_title = "New Chat"
    st.session_state.chat_started = False

# -------------------- SIDEBAR -------------------------------

with st.sidebar:
    st.markdown("""
    <div class="brand-row">
      <div class="brand-orb">✦</div>
      <div><div class="brand-name">Zaid AI</div><div class="brand-sub">Your intelligent workspace</div></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("＋  New Chat", use_container_width=True, type="primary"):
        reset_chat()
        st.session_state.page = "Chat"
        st.rerun()

    st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)
    nav_items = ["Chat", "Dashboard", "AI Tools", "Library", "Archived"]
    for item in nav_items:
        icon = {"Chat":"◉", "Dashboard":"▦", "AI Tools":"✧", "Library":"▤", "Archived":"◷"}[item]
        if st.button(f"{icon}  {item}", key=f"nav_{item}", use_container_width=True):
            st.session_state.page = item
            st.rerun()

    st.markdown('<div class="side-label">Your apps</div>', unsafe_allow_html=True)
    for app_name, url in APP_LINKS.items():
        st.markdown(f"↗ [{app_name}]({url})")

    st.markdown('<div class="side-label">Recent chats</div>', unsafe_allow_html=True)
    if st.session_state.messages:
        st.caption(st.session_state.chat_title)
    else:
        st.markdown('<div class="small-muted">Your recent conversations will appear here.</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="panel"><div class="panel-title">✦ Zaid AI</div><div class="panel-sub">Gemini primary · Groq backup</div></div>', unsafe_allow_html=True)
    if st.button("⚙ Configuration", use_container_width=True):
        st.session_state.show_config = not st.session_state.show_config
    if st.session_state.show_config:
        st.caption(f"Gemini: {'Connected key' if GOOGLE_API_KEY else 'Key missing'}")
        st.caption(f"Groq: {'Connected key' if GROQ_API_KEY else 'Key missing'}")
        st.caption(f"Tavily: {'Connected key' if TAVILY_API_KEY else 'Key missing'}")
        st.caption(f"OpenWeather: {'Connected key' if OPENWEATHER_API_KEY else 'Key missing'}")
    st.markdown('<div class="small-muted">Made with Python · Streamlit</div>', unsafe_allow_html=True)

# -------------------- TOP BAR --------------------------------

left, right = st.columns([5, 2])
with left:
    st.markdown(f'<div class="pill">✦ &nbsp; {st.session_state.page} workspace</div>', unsafe_allow_html=True)
with right:
    provider_options = ["Gemini", "Groq"]
    selected = st.selectbox(
        "AI model",
        provider_options,
        index=provider_options.index(st.session_state.selected_model),
        label_visibility="collapsed",
        key="provider_picker",
    )
    if selected != st.session_state.selected_model:
        st.session_state.selected_model = selected
        st.session_state.active_provider = selected
        st.session_state.gemini_chat = None
        st.rerun()

# -------------------- CHAT PAGE ------------------------------

if st.session_state.page == "Chat":
    st.markdown("""
    <div class="hero">
      <div class="hero-orb">✦</div>
      <h1>Ready to create something new?</h1>
      <p>Ask Zaid AI anything. Brainstorm ideas, get answers, search the web or use your personal tools.</p>
    </div>
    """, unsafe_allow_html=True)

    quick = st.columns(3)
    quick_prompts = [
        ("✧  Brainstorm", "Help me brainstorm ideas for a new project."),
        ("⌘  Make a plan", "Help me create a practical plan for my goals."),
        ("⌕  Search web", "Search the web for the latest AI developments."),
    ]
    for col, (label, value) in zip(quick, quick_prompts):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.pending_prompt = value
                st.rerun()

    # Existing conversation
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🪐"):
            st.markdown(msg["content"])

    prompt = st.chat_input("✦  Ask anything…")
    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        if not st.session_state.chat_started:
            st.session_state.chat_title = prompt[:34] + ("…" if len(prompt) > 34 else "")
            st.session_state.chat_started = True
        st.session_state.request_count += 1

        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🪐"):
            try:
                with st.spinner("Zaid AI is thinking…"):
                    answer = generate_answer(prompt)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.output_count += 1
            except Exception as e:
                st.error("I couldn't complete that request.")
                st.caption(str(e))
        st.rerun()

    st.markdown('<div class="section-heading">Explore AI tools</div>', unsafe_allow_html=True)
    tool_cols = st.columns(4)
    tool_cards = [
        ("🎨", "Image Generator", "Plan an image concept or prompt."),
        ("✍️", "Text Generator", "Draft, rewrite and improve text."),
        ("📊", "Data Analyzer", "Explore data and explain insights."),
        ("⌘", "Code Assistant", "Write and debug code with AI."),
    ]
    for col, (ico, name, desc) in zip(tool_cols, tool_cards):
        with col:
            st.markdown(f'<div class="feature-card"><div class="feature-icon">{ico}</div><div class="feature-name">{name}</div><div class="feature-desc">{desc}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-heading">Quick access</div>', unsafe_allow_html=True)
    app_cols = st.columns(4)
    for col, (name, url) in zip(app_cols, APP_LINKS.items()):
        with col:
            st.markdown(f'<div class="panel"><div class="panel-title">{name}</div><div class="panel-sub">Your Zaid project</div><br><a href="{url}" target="_blank">Open app ↗</a></div>', unsafe_allow_html=True)

# -------------------- DASHBOARD PAGE ------------------------

elif st.session_state.page == "Dashboard":
    st.title("▦  AI Dashboard")
    st.caption("A snapshot of your Zaid AI activity in this session.")
    metrics = st.columns(4)
    metric_data = [
        ("AI Requests", st.session_state.request_count, "Prompts sent"),
        ("Outputs", st.session_state.output_count, "AI responses completed"),
        ("Web Searches", st.session_state.search_count, "Tavily searches"),
        ("Weather Checks", st.session_state.weather_count, "Live weather lookups"),
    ]
    for col, (label, value, note) in zip(metrics, metric_data):
        with col:
            st.markdown(f'<div class="panel"><div class="panel-sub">{label}</div><div class="metric">{value:,}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-heading">Provider status</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="panel"><div class="panel-title">Google Gemini</div><div class="metric" style="font-size:20px">{ "Configured" if GOOGLE_API_KEY else "Needs API key" }</div><div class="panel-sub">Primary AI provider · {GEMINI_MODEL}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="panel"><div class="panel-title">Groq</div><div class="metric" style="font-size:20px">{ "Configured" if GROQ_API_KEY else "Needs API key" }</div><div class="panel-sub">Backup AI provider · {GROQ_MODEL}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-heading">Recent activity</div>', unsafe_allow_html=True)
    if st.session_state.messages:
        for msg in st.session_state.messages[-6:]:
            role = "You" if msg["role"] == "user" else "Zaid AI"
            st.markdown(f"**{role}:** {msg['content'][:180]}{'…' if len(msg['content']) > 180 else ''}")
    else:
        st.info("Start a conversation to see activity here.")

# -------------------- AI TOOLS PAGE --------------------------

elif st.session_state.page == "AI Tools":
    st.title("✧  AI Tools")
    st.caption("Choose a task and Zaid AI will help you in the chat workspace.")
    tool_specs = [
        ("✍️ Text Generator", "Write a professional LinkedIn post about my latest project."),
        ("📊 Data Analyzer", "Help me analyze a dataset and identify useful insights."),
        ("⌘ Code Assistant", "Help me debug and improve my Python code."),
        ("💡 Brainstorm", "Give me creative ideas for a useful AI application."),
    ]
    cols = st.columns(2)
    for i, (name, prompt_text) in enumerate(tool_specs):
        with cols[i % 2]:
            st.markdown(f'<div class="panel"><div class="panel-title">{name}</div><div class="panel-sub">Start this workflow with Zaid AI.</div></div>', unsafe_allow_html=True)
            if st.button(f"Start {name}", key=f"tool_{i}", use_container_width=True):
                st.session_state.pending_prompt = prompt_text
                st.session_state.page = "Chat"
                st.rerun()

    st.markdown('<div class="section-heading">Live tools</div>', unsafe_allow_html=True)
    wcol, scol = st.columns(2)
    with wcol:
        city = st.text_input("Weather city", placeholder="e.g. Dubai")
        if st.button("Check weather", use_container_width=True):
            if city.strip():
                st.markdown(get_weather(city.strip()))
            else:
                st.warning("Enter a city first.")
    with scol:
        query = st.text_input("Web search query", placeholder="e.g. latest AI news")
        if st.button("Search web", use_container_width=True):
            if query.strip():
                st.markdown(web_search(query.strip()))
            else:
                st.warning("Enter a search query first.")

# -------------------- LIBRARY PAGE ---------------------------

elif st.session_state.page == "Library":
    st.title("▤  Library")
    st.caption("Save useful notes and prompts during this session.")
    note = st.text_area("Add a note or prompt", placeholder="Save an idea, prompt, or useful piece of text…")
    if st.button("Save to Library", type="primary"):
        if note.strip():
            st.session_state.library_items.append({
                "text": note.strip(),
                "saved_at": datetime.now().strftime("%d %b %Y, %H:%M"),
            })
            st.success("Saved to your session library.")
            st.rerun()
        else:
            st.warning("Write something before saving.")
    st.markdown('<div class="section-heading">Saved items</div>', unsafe_allow_html=True)
    if not st.session_state.library_items:
        st.info("Your saved notes will appear here. Session notes reset when the session ends.")
    for i, item in enumerate(reversed(st.session_state.library_items)):
        with st.expander(f"Saved note · {item['saved_at']}"):
            st.write(item["text"])
            if st.button("Delete note", key=f"delete_note_{i}"):
                actual_index = len(st.session_state.library_items) - 1 - i
                st.session_state.library_items.pop(actual_index)
                st.rerun()

# -------------------- ARCHIVED PAGE --------------------------

elif st.session_state.page == "Archived":
    st.title("◷  Archived chats")
    st.caption("Archive the current conversation to keep it in this session's archive.")
    if st.session_state.messages:
        if st.button("Archive current conversation", type="primary"):
            st.session_state.archived_chats.append({
                "title": st.session_state.chat_title,
                "messages": st.session_state.messages.copy(),
                "archived_at": datetime.now().strftime("%d %b %Y, %H:%M"),
            })
            reset_chat()
            st.success("Conversation archived.")
            st.rerun()
    if not st.session_state.archived_chats:
        st.info("No archived conversations yet.")
    for i, chat in enumerate(reversed(st.session_state.archived_chats)):
        with st.expander(f"{chat['title']} · {chat['archived_at']}"):
            for msg in chat["messages"]:
                st.markdown(f"**{'You' if msg['role'] == 'user' else 'Zaid AI'}:** {msg['content']}")
