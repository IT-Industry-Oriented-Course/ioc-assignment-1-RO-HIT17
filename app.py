import streamlit as st
import os
import core.config as config
from agent.agent import create_clinical_agent
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="Clinical Workflow Agent", page_icon="🏥", layout="wide")

from dotenv import load_dotenv
load_dotenv()

st.sidebar.header="Configuration"
provider = st.sidebar.selectbox("LLM Provider", ["huggingface", "gemini"], index=0)

if provider == "huggingface":
    api_key = config.HUGGINGFACE_API_TOKEN
else:
    api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    st.sidebar.error("Missing API Key in .env file")
    st.stop()

dry_run = st.sidebar.checkbox("Dry Run Mode", value=False, help="If checked, bookings will be simulated but not saved.")
config.DRY_RUN = dry_run

st.title("🏥 Clinical Workflow Automation Agent")
st.markdown("""
**Purpose**: Assist clinicians with scheduling and eligibility checks.
**Safety**: This agent does NOT provide medical advice.
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_executor" not in st.session_state or st.session_state.get("provider") != provider:
    if api_key:
        try:
            st.session_state.agent_executor = create_clinical_agent(provider, api_key)
            st.session_state.provider = provider
            st.success(f"Agent initialized with {provider}!")
        except Exception as e:
            st.error(f"Failed to initialize agent: {e}")
    else:
        st.warning("Please enter your API Key to proceed.")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])

if prompt := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if "agent_executor" in st.session_state:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    chat_history = []
                    for msg in st.session_state.messages[:-1]: 
                        if msg["role"] == "user":
                            chat_history.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            chat_history.append(AIMessage(content=msg["content"]))

                    response = st.session_state.agent_executor.invoke({
                        "input": prompt,
                        "chat_history": chat_history
                    })
                    output = response['output']
                    st.write(output)
                    st.session_state.messages.append({"role": "assistant", "content": output})
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.error("Agent not initialized. Please check API Key.")