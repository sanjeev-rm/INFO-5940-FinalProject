#!/usr/bin/env python
"""
Validation Script for Hotel Guest Service Training System

This script validates that the project is set up correctly.
"""

import sys
import os
from pathlib import Path
import importlib

def check_file_structure():
    """Check that all required files exist"""
    required_files = [
        "app.py",
        "requirements.txt",
        ".env.template",
        "README.md",
        "setup.py",
        "run.py"
    ]

    required_dirs = [
        "agents",
        "rag_system",
        "document_processor",
        "config",
        "utils",
        "data",
        "logs"
    ]

    print("Checking file structure...")

    all_good = True
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ Missing: {file}")
            all_good = False

    for dir in required_dirs:
        if Path(dir).is_dir():
            print(f"✅ {dir}/")
        else:
            print(f"❌ Missing directory: {dir}")
            all_good = False

    return all_good

def check_python_modules():
    """Check that all Python modules can be imported"""
    modules_to_check = [
        ("agents", "agents/__init__.py"),
        ("agents.base_agent", "agents/base_agent.py"),
        ("agents.guest_agent", "agents/guest_agent.py"),
        ("agents.coach_agent", "agents/coach_agent.py"),
        ("agents.report_agent", "agents/report_agent.py"),
        ("config", "config/__init__.py"),
        ("config.settings", "config/settings.py"),
        ("rag_system", "rag_system/__init__.py"),
        ("rag_system.retriever", "rag_system/retriever.py"),
        ("rag_system.embeddings", "rag_system/embeddings.py"),
        ("rag_system.vector_store", "rag_system/vector_store.py"),
        ("document_processor", "document_processor/__init__.py"),
        ("document_processor.processor", "document_processor/processor.py"),
        ("document_processor.chunker", "document_processor/chunker.py"),
        ("document_processor.readers", "document_processor/readers.py"),
        ("utils", "utils/__init__.py"),
        ("utils.logger", "utils/logger.py"),
        ("utils.session_manager", "utils/session_manager.py")
    ]

    print("\nChecking Python module imports...")

    all_good = True
    for module_name, file_path in modules_to_check:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            all_good = False
        except Exception as e:
            print(f"⚠️  {module_name}: {e}")

    return all_good

def check_configuration():
    """Check configuration setup"""
    print("\nChecking configuration...")

    env_template_exists = Path(".env.template").exists()
    env_exists = Path(".env").exists()

    print(f"✅ .env.template exists: {env_template_exists}")
    print(f"{'✅' if env_exists else '⚠️ '} .env exists: {env_exists}")

    if not env_exists:
        print("   Run: cp .env.template .env")
        print("   Then edit .env with your API credentials")

    # Try to load configuration
    try:
        from config.settings import AppConfig
        config = AppConfig()
        print("✅ Configuration loads successfully")

        # Check training docs path
        if config.TRAINING_DOCS_PATH.exists():
            doc_count = len(list(config.TRAINING_DOCS_PATH.glob("**/*.*")))
            print(f"✅ Training documents directory found ({doc_count} files)")
        else:
            print(f"⚠️  Training documents not found at: {config.TRAINING_DOCS_PATH}")

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

    return True

def check_dependencies():
    """Check that required dependencies are available"""
    print("\nChecking dependencies...")

    # Core dependencies that should be importable
    core_deps = [
        "streamlit",
        "requests",
        "chromadb",
        "pandas",
        "pathlib"
    ]

    optional_deps = [
        ("PyPDF2", "PDF processing"),
        ("docx", "Word document processing"),
        ("openpyxl", "Excel file support"),
        ("textract", "Legacy document formats")
    ]

    all_good = True

    for dep in core_deps:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} (required)")
            all_good = False

    for dep, description in optional_deps:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep} ({description})")
        except ImportError:
            print(f"⚠️  {dep} ({description}) - optional")

    return all_good

def run_basic_functionality_test():
    """Run basic functionality tests"""
    print("\nRunning basic functionality tests...")

    try:
        # Test configuration
        from config.settings import AppConfig
        config = AppConfig()
        print("✅ Configuration initialization")

        # Test logging
        from utils.logger import setup_logger
        logger = setup_logger("test")
        logger.info("Test log message")
        print("✅ Logging system")

        # Test session manager
        from utils.session_manager import SessionManager
        session_manager = SessionManager(config)
        session_id = session_manager.create_session()
        print(f"✅ Session management (created session: {session_id[:8]}...)")

        # Test document processor (without processing files)
        from document_processor.processor import DocumentProcessor
        doc_processor = DocumentProcessor(config)
        print("✅ Document processor initialization")

        # Test text chunker
        from document_processor.chunker import TextChunker
        chunker = TextChunker(config)
        test_chunks = chunker.chunk_text("This is a test sentence. This is another test sentence.")
        print(f"✅ Text chunker (created {len(test_chunks)} chunks)")

        return True

    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def main():
    """Main validation function"""
    print("🔍 Hotel Guest Service Training System - Validation")
    print("=" * 55)

    checks = [
        ("File Structure", check_file_structure),
        ("Python Modules", check_python_modules),
        ("Configuration", check_configuration),
        ("Dependencies", check_dependencies),
        ("Basic Functionality", run_basic_functionality_test)
    ]

    all_passed = True

    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)

        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            all_passed = False

    print("\n" + "=" * 55)

    if all_passed:
        print("🎉 All validation checks passed!")
        print("\n✨ Your system is ready to run!")
        print("Next steps:")
        print("1. Edit .env with your API credentials (if not done)")
        print("2. Run: python run.py")
        print("3. Or run: streamlit run app.py")
    else:
        print("❌ Some validation checks failed")
        print("\n🔧 Please fix the issues above before running the application")
        print("💡 Try running: python setup.py")

if __name__ == "__main__":
    main()