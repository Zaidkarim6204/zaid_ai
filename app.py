import streamlit as st
import google.generativeai as genai
import os
import requests
import smtplib
from email.mime.text import MIMEText
from tavily import TavilyClient

# --- Page Configuration ---
st.set_page_config(
    page_title="Zaid's AI Assistant",
    page_icon="🤖",
    layout="centered"
)

# --- API Key Configuration ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    
    genai.configure(api_key=GOOGLE_API_KEY)
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    
except (FileNotFoundError, KeyError) as e:
    st.error(f"Secrets file or key not found: {e}. Please check your .streamlit/secrets.toml file.")
    st.stop()

# --- Tool Functions ---
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
    Use this tool to get real-time information from the internet. 
    It is ideal for answering questions about current events, recent discoveries, 
    or any topic that requires up-to-the-minute information, such as who a current political leader is.
    """
    try:
        response = tavily_client.search(query=query, search_depth="basic")
        return "\n".join([f"- {res['content']}" for res in response['results']])
    except Exception as ex:
        return f"Could not perform web search. Error: {ex}"
        
def send_email(to_address: str, subject: str, body: str):
    """Sends an email from the configured sender address."""
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_address

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            smtp_server.sendmail(SENDER_EMAIL, to_address, msg.as_string())
        return f"Email successfully sent to {to_address}."
    except Exception as ex:
        return f"Failed to send email. Error: {ex}"

# --- Model and Chat Configuration ---
# ADDED A SYSTEM INSTRUCTION
system_instruction = """You are a helpful and powerful AI assistant. Your goal is to provide accurate, up-to-date answers. 
For any question about current events, recent news, or specific real-time information (like who a current leader is or what the weather is),
you MUST use your available tools. Do not rely on your internal knowledge for such questions, as it may be outdated."""

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    tools=[get_live_weather, perform_web_search, send_email],
    system_instruction=system_instruction
)
chat = model.start_chat(enable_automatic_function_calling=True)

# --- Main App UI ---
st.title("🤖 Zaid's AI Assistant")
st.caption("This chatbot can search the web, check live weather, and send emails.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help you today?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Main Chat Logic ---
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            try:
                response = chat.send_message(prompt)
                
                final_response = response.parts[-1].text
                message_placeholder.markdown(final_response)
                
            except Exception as e:
                final_response = f"An error occurred: {e}"
                message_placeholder.markdown(final_response)

    st.session_state.messages.append({"role": "assistant", "content": final_response})