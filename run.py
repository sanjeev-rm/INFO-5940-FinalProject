#!/usr/bin/env python
"""
Run Script for Hotel Guest Service Training System

Simple script to start the Streamlit application with proper configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check if environment is properly configured"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please run: python setup.py")
        return False

    # Check if API key is configured
    try:
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("LLM_API_KEY")
        if not api_key or api_key == "your_api_key_here":
            print("⚠️  API key not configured in .env file")
            print("Please edit .env file with your actual API credentials")
    except ImportError:
        print("⚠️  python-dotenv not installed, cannot check API configuration")

    return True

def start_streamlit():
    """Start the Streamlit application"""
    try:
        print("🏨 Starting Hotel Guest Service Training System...")
        print("🌐 The application will open in your web browser")
        print("📍 URL: http://localhost:8501")
        print("🛑 Press Ctrl+C to stop the server")
        print("-" * 50)

        # Start Streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install dependencies:")
        print("pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

def main():
    """Main function"""
    print("🏨 Hotel Guest Service Training System")
    print("=" * 40)

    if not check_environment():
        sys.exit(1)

    start_streamlit()

if __name__ == "__main__":
    main()