#!/usr/bin/env python
"""
Setup Script for Hotel Guest Service Training System

This script helps with initial setup and configuration.
"""

import os
import sys
from pathlib import Path
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "data",
        "data/vectorstore",
        "data/sessions",
        "logs"
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def setup_environment():
    """Setup environment file"""
    env_template = Path(".env.template")
    env_file = Path(".env")

    if not env_file.exists() and env_template.exists():
        shutil.copy(env_template, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your API credentials")
        return True
    elif env_file.exists():
        print("✅ .env file already exists")
        return True
    else:
        print("❌ .env.template not found")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_training_docs():
    """Check if training documents directory exists"""
    docs_path = Path("/Users/wbo7/Library/CloudStorage/Box-Box/INFO 5940 - Fall 2025/Final Project/Front Desk Training Docs")

    if docs_path.exists():
        doc_count = len(list(docs_path.glob("**/*.*")))
        print(f"✅ Training documents directory found with {doc_count} files")
        return True
    else:
        print("⚠️  Training documents directory not found")
        print(f"Expected location: {docs_path}")
        print("Please ensure training documents are in the correct location or update the path in config/settings.py")
        return False

def test_imports():
    """Test that key modules can be imported"""
    test_modules = [
        ("streamlit", "Streamlit web framework"),
        ("chromadb", "ChromaDB vector database"),
        ("requests", "HTTP requests library"),
        ("pandas", "Data processing library")
    ]

    all_good = True
    for module_name, description in test_modules:
        try:
            __import__(module_name)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - Not installed")
            all_good = False

    return all_good

def create_sample_config():
    """Create a sample configuration for testing"""
    sample_config = """
# Sample configuration for testing
# DO NOT use in production - replace with real API credentials

LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=your_api_key_here

FAST_MODEL=gpt-3.5-turbo
BALANCED_MODEL=gpt-4
SMART_MODEL=gpt-4
DEFAULT_MODEL=gpt-4

EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_API_URL=https://api.openai.com/v1/embeddings

DEBUG=true
LOG_LEVEL=INFO
"""

    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(sample_config.strip())
        print("✅ Created sample .env configuration")

def main():
    """Main setup function"""
    print("🏨 Hotel Guest Service Training System - Setup")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Create directories
    create_directories()

    # Setup environment file
    setup_environment()

    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)

    # Test imports
    print("\nTesting module imports...")
    if not test_imports():
        print("\n⚠️  Some modules failed to import. Please check the error messages above.")

    # Check training documents
    print("\nChecking training documents...")
    check_training_docs()

    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your API credentials")
    print("2. Ensure training documents are in the correct location")
    print("3. Run: streamlit run app.py")
    print("\nFor help, see README.md")

if __name__ == "__main__":
    main()