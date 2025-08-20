# 🤖 AI Assistant with Live Tools

An advanced, conversational AI chatbot built with Python and Streamlit, powered by the Google Gemini Pro model. This AI assistant can understand user prompts and interact with live, real-world services using a suite of integrated tools.

*[Live Demo Link](https://zaidai-9bgkrzfbpp78hnk3idyj9p.streamlit.app/)*



## About The Project

This project goes beyond a standard chatbot by implementing a "tool-enabled" AI architecture. The Gemini model is equipped with a set of functions that allow it to access live information and perform real-world actions. The AI intelligently analyzes the user's prompt and decides which tool to use, if any, to provide the most accurate and up-to-date response.

This demonstrates a modern, agent-based approach to building AI applications that can interact with external systems.

---

### Key Features

* *Conversational AI Core:* Powered by Google's gemini-1.5-flash for fluid, context-aware conversations.
* *Live Web Search:* Uses the Tavily Search API to answer questions about current events and topics beyond its training data.
* *Real-Time Weather:* Fetches current weather data for any city in the world via the OpenWeatherMap API.
* *Email Sending:* Can send emails directly from the chat interface using a secure connection.
* *Automatic Function Calling:* The Gemini model autonomously decides which tool to call based on the user's request.

---

### Technologies Used

* *Language:* Python
* *Framework:* Streamlit
* *AI Model:* Google Gemini Pro
* *Core Libraries:* google-generativeai, requests, tavily-python
* *APIs:* Tavily Search API, OpenWeatherMap API

---

### Setup and Local Installation

To run this project locally, you will need to provide your own API keys.

1.  *Clone the repository:*
    bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    
2.  *Create a Conda environment:*
    bash
    conda create -n ai_env python=3.9
    conda activate ai_env
    
3.  *Install dependencies:*
    bash
    pip install -r requirements.txt
    
4.  *Add your API Keys and Credentials:*
    * Create a folder named .streamlit in the main project directory.
    * Inside this folder, create a file named secrets.toml.
    * Add your five secret keys to this file in the following format:
        toml
        GOOGLE_API_KEY = "your_google_api_key"
        OPENWEATHER_API_KEY = "your_openweathermap_api_key"
        TAVILY_API_KEY = "your_tavily_api_key"
        SENDER_EMAIL = "your.email@gmail.com"
        EMAIL_PASSWORD = "your_16_character_google_app_password"
        
5.  *Run the app:*
    bash
    streamlit run app.py
    
