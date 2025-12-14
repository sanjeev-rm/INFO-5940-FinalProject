"""
Hotel Guest Service Training System
Main Streamlit Application

This application provides a real-time chat interface for training hotel front desk staff
using AI agents that simulate guest interactions and provide coaching feedback.
"""

import streamlit as st
import asyncio
from datetime import datetime
import json

# Import our custom modules
from agents.guest_agent import GuestAgent
from agents.coach_agent import CoachAgent
from agents.report_agent import ReportAgent
from rag_system.retriever import RAGRetriever
from config.settings import AppConfig
from utils.session_manager import SessionManager
from utils.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Hotel Guest Service Training",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = SessionManager.generate_session_id()
    if "training_active" not in st.session_state:
        st.session_state.training_active = False
    if "agents_initialized" not in st.session_state:
        st.session_state.agents_initialized = False

def initialize_agents():
    """Initialize AI agents"""
    if not st.session_state.agents_initialized:
        try:
            config = AppConfig()

            # Initialize RAG system
            rag_retriever = RAGRetriever(config)

            # Initialize agents
            st.session_state.guest_agent = GuestAgent(config)
            st.session_state.coach_agent = CoachAgent(config, rag_retriever)
            st.session_state.report_agent = ReportAgent(config, rag_retriever)

            st.session_state.agents_initialized = True
            logger.info("Agents initialized successfully")

        except Exception as e:
            st.error(f"Failed to initialize agents: {str(e)}")
            logger.error(f"Agent initialization error: {e}")
            return False

    return True

def main():
    """Main application function"""

    # Initialize session state
    initialize_session_state()

    # Sidebar for configuration and coaching
    with st.sidebar:
        st.title("🏨 Training Control Panel")

        # Session information
        st.subheader("Session Info")
        st.write(f"Session ID: {st.session_state.session_id[:8]}...")
        st.write(f"Status: {'Active' if st.session_state.training_active else 'Inactive'}")

        # Training controls
        st.subheader("Training Controls")

        if not st.session_state.training_active:
            if st.button("Start Training Session", type="primary"):
                if initialize_agents():
                    st.session_state.training_active = True
                    st.session_state.messages = []

                    # Generate initial guest scenario
                    initial_scenario = st.session_state.guest_agent.generate_scenario()
                    st.session_state.messages.append({
                        "role": "guest",
                        "content": initial_scenario,
                        "timestamp": datetime.now()
                    })
                    st.rerun()
        else:
            if st.button("End Training Session", type="secondary"):
                st.session_state.training_active = False

                # Generate session report
                if len(st.session_state.messages) > 1:
                    with st.spinner("Generating session report..."):
                        report = st.session_state.report_agent.generate_report(
                            st.session_state.messages,
                            st.session_state.session_id
                        )
                        st.session_state.final_report = report
                st.rerun()

        # Real-time coaching panel (only visible during active training)
        if st.session_state.training_active and st.session_state.agents_initialized:
            st.subheader("💡 Real-time Coaching")
            coaching_placeholder = st.empty()

            # Display latest coaching if available
            if hasattr(st.session_state, 'latest_coaching'):
                with coaching_placeholder.container():
                    st.info("Coach Feedback:")
                    st.write(st.session_state.latest_coaching)

    # Main chat interface
    st.title("🏨 Hotel Guest Service Training")
    st.markdown("Practice your guest service skills with our AI-powered training system.")

    # Display final report if session ended
    if not st.session_state.training_active and hasattr(st.session_state, 'final_report'):
        st.subheader("📊 Training Session Report")
        st.markdown(st.session_state.final_report)

        if st.button("Start New Session"):
            del st.session_state.final_report
            st.session_state.session_id = SessionManager.generate_session_id()
            st.rerun()

    # Chat interface
    elif st.session_state.training_active:

        # Display chat messages
        for message in st.session_state.messages:
            role_emoji = "😟" if message["role"] == "guest" else "👨‍💼"
            role_name = "Hotel Guest" if message["role"] == "guest" else "Front Desk Agent"

            with st.chat_message(message["role"], avatar=role_emoji):
                st.write(f"**{role_name}:** {message['content']}")

        # Chat input for trainee responses
        if prompt := st.chat_input("Type your response as the front desk agent..."):

            # Add trainee message
            st.session_state.messages.append({
                "role": "agent",
                "content": prompt,
                "timestamp": datetime.now()
            })

            # Display trainee message immediately
            with st.chat_message("agent", avatar="👨‍💼"):
                st.write(f"**Front Desk Agent:** {prompt}")

            # Get coaching feedback (in sidebar)
            with st.spinner("Getting coaching feedback..."):
                coaching_feedback = st.session_state.coach_agent.provide_coaching(
                    st.session_state.messages,
                    prompt
                )
                st.session_state.latest_coaching = coaching_feedback

            # Generate guest response
            with st.spinner("Guest is responding..."):
                guest_response = st.session_state.guest_agent.respond_to_agent(
                    st.session_state.messages,
                    prompt
                )

                # Add guest response
                st.session_state.messages.append({
                    "role": "guest",
                    "content": guest_response,
                    "timestamp": datetime.now()
                })

            st.rerun()

    else:
        st.info("Click 'Start Training Session' in the sidebar to begin your training.")
        st.markdown("""
        ### How it works:
        1. **Start a training session** - The system will generate a guest scenario
        2. **Respond as a front desk agent** - Practice your customer service skills
        3. **Get real-time coaching** - Receive feedback based on training materials
        4. **Review your session** - Get a detailed report at the end

        The system uses three AI agents:
        - 🎭 **Guest Agent**: Simulates upset hotel guests with realistic scenarios
        - 💡 **Coach Agent**: Provides real-time feedback based on training materials
        - 📊 **Report Agent**: Generates comprehensive session summaries
        """)

if __name__ == "__main__":
    main()