# Hotel Guest Service Training System

A comprehensive AI-powered training system designed to help hotel front desk staff improve their guest service skills through realistic simulations and intelligent coaching.

## Overview

This system uses three specialized AI agents to create an immersive training environment:

- **🎭 Guest Agent**: Simulates realistic hotel guest scenarios and interactions
- **💡 Coach Agent**: Provides real-time feedback based on training materials using RAG (Retrieval-Augmented Generation)
- **📊 Report Agent**: Generates detailed training reports and performance analytics

The system processes your existing training documents (PDF, Word, Excel, Text files) and uses them as the knowledge base for coaching and feedback, ensuring consistency with your established training standards.

## Features

### Core Functionality
- **Real-time Chat Interface**: Streamlit-based web interface for natural conversation flow
- **Intelligent Document Processing**: Automatically processes and vectorizes training materials
- **RAG-Powered Coaching**: Provides feedback based on your actual training documents
- **Performance Analytics**: Detailed session reports and progress tracking
- **Multi-format Support**: Handles .pdf, .docx, .doc, .xlsx, .xls, and .txt files
- **Gap Identification**: Identifies areas where training materials may need enhancement

### Training Features
- **Scenario Variety**: Multiple guest service scenarios (billing disputes, room issues, complaints, etc.)
- **Adaptive Difficulty**: Scenarios adjust based on agent performance
- **Real-time Feedback**: Coaching appears in sidebar during conversations
- **Session Management**: Persistent sessions with full conversation history
- **Training Reports**: Comprehensive reports for trainees and managers

## Project Structure

```
hotel-training-system/
├── app.py                          # Main Streamlit application
├── agents/                         # AI agents module
│   ├── __init__.py
│   ├── base_agent.py              # Base class for all agents
│   ├── guest_agent.py             # Guest simulation agent
│   ├── coach_agent.py             # Real-time coaching agent
│   └── report_agent.py            # Report generation agent
├── rag_system/                     # RAG and vector search
│   ├── __init__.py
│   ├── retriever.py               # Main RAG interface
│   ├── embeddings.py              # Embedding generation
│   └── vector_store.py            # ChromaDB vector storage
├── document_processor/             # Document processing pipeline
│   ├── __init__.py
│   ├── processor.py               # Main document processor
│   ├── chunker.py                 # Text chunking strategies
│   └── readers.py                 # Multi-format document readers
├── config/                        # Configuration management
│   ├── __init__.py
│   └── settings.py                # Application settings
├── utils/                         # Utility functions
│   ├── __init__.py
│   ├── logger.py                  # Logging configuration
│   └── session_manager.py         # Session management
├── data/                          # Data storage
│   ├── vectorstore/               # ChromaDB vector database
│   └── sessions/                  # Session data
├── logs/                          # Application logs
├── requirements.txt               # Python dependencies
├── .env                          # Environment configuration
├── .env.template                 # Environment template
└── README.md                     # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Access to an LLM API (OpenAI, Anthropic, or enterprise endpoint)
- Training documents in supported formats

### Step 1: Clone and Setup

```bash
# Navigate to the project directory
cd /path/to/hotel-training-system

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

Required configuration:
```env
# Your LLM API configuration
LLM_API_URL=https://your-api-endpoint.com/v1/chat/completions
LLM_API_KEY=your_api_key_here

# Model configuration (adjust based on available models)
FAST_MODEL=gpt-3.5-turbo
BALANCED_MODEL=gpt-4
SMART_MODEL=gpt-4
DEFAULT_MODEL=gpt-4

# Embedding configuration
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_API_URL=https://api.openai.com/v1/embeddings
```

### Step 3: Prepare Training Documents

Ensure your training documents are located at:
```
/Users/wbo7/Library/CloudStorage/Box-Box/INFO 5940 - Fall 2025/Final Project/Front Desk Training Docs
```

Or update the path in `config/settings.py`:
```python
self.TRAINING_DOCS_PATH = Path("/your/training/documents/path")
```

Supported formats:
- PDF files (.pdf)
- Word documents (.doc, .docx)
- Excel spreadsheets (.xlsx, .xls)
- Text files (.txt)

## Usage

### Starting the Application

```bash
# Make sure you're in the project directory
cd /path/to/hotel-training-system

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the Streamlit application
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Training Workflow

1. **Start Training Session**
   - Click "Start Training Session" in the sidebar
   - The system will load training documents and initialize AI agents
   - A guest scenario will be automatically generated

2. **Interact with Guest**
   - Respond to the simulated guest as you would at the front desk
   - Use professional, empathetic language
   - Focus on problem-solving and service recovery

3. **Receive Real-time Coaching**
   - Coaching feedback appears in the sidebar after each response
   - Feedback is based on your training materials
   - Suggestions include specific improvements and best practices

4. **Complete Session**
   - Click "End Training Session" when finished
   - Review the comprehensive session report
   - Use insights for continued learning and development

### Advanced Features

#### Document Management
The system automatically processes training documents when first started. To refresh the document database:

```python
from rag_system.retriever import RAGRetriever
from config.settings import AppConfig

config = AppConfig()
rag = RAGRetriever(config)
rag.refresh_vector_store()
```

#### Custom Scenarios
You can influence scenario generation by adding specific scenario documents to your training materials folder.

#### Performance Analytics
Session reports include:
- Performance metrics (1-5 scale ratings)
- Specific examples from the conversation
- Training recommendations
- Identified knowledge gaps

## Configuration Options

### Model Configuration
Optimize costs by using different models for different agents:

```env
# Fast model for quick guest responses
FAST_MODEL=gpt-3.5-turbo

# Balanced model for guest interactions
BALANCED_MODEL=gpt-4

# Smart model for coaching and reports
SMART_MODEL=gpt-4
```

### RAG Configuration
Adjust retrieval settings:

```env
# Number of documents to retrieve for context
RAG_TOP_K=5

# Minimum similarity score for relevance
RAG_SIMILARITY_THRESHOLD=0.7

# Text chunking parameters
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Application Settings
```env
# Debug mode (detailed logging)
DEBUG=true

# Session timeout (minutes)
SESSION_TIMEOUT_MINUTES=60

# Maximum messages per session
MAX_MESSAGE_HISTORY=50
```

## Troubleshooting

### Common Issues

**No training documents found:**
- Check the `TRAINING_DOCS_PATH` in `config/settings.py`
- Ensure documents are in supported formats
- Check file permissions

**API connection errors:**
- Verify `LLM_API_URL` and `LLM_API_KEY` in `.env`
- Test API connectivity independently
- Check network firewall settings

**Slow performance:**
- Use faster models for guest agent (`FAST_MODEL=gpt-3.5-turbo`)
- Reduce `RAG_TOP_K` for fewer document retrievals
- Optimize `CHUNK_SIZE` for your documents

**Memory issues:**
- Reduce `MAX_MESSAGE_HISTORY`
- Use smaller `CHUNK_SIZE`
- Clear vector store and reinitialize: `rag.refresh_vector_store()`

### Logging

Logs are stored in the `logs/` directory:
- `hotel_training_YYYYMMDD.log`: General application logs
- `hotel_training_errors_YYYYMMDD.log`: Error-specific logs

Increase logging detail:
```env
LOG_LEVEL=DEBUG
```

### Document Processing Issues

**Large file errors:**
```env
# Increase maximum file size (MB)
MAX_DOCUMENT_SIZE_MB=20
```

**Encoding problems:**
The system tries multiple encodings automatically. For persistent issues, convert files to UTF-8.

**Unsupported formats:**
Add format support in `document_processor/readers.py` or convert files to supported formats.

## Development

### Adding New Features

1. **New Agent Types**: Extend `BaseAgent` class in `agents/`
2. **Document Formats**: Add readers in `document_processor/readers.py`
3. **Chunking Strategies**: Implement in `document_processor/chunker.py`
4. **Vector Stores**: Add new stores in `rag_system/vector_store.py`

### Testing

```bash
# Run basic functionality test
python -c "from config.settings import AppConfig; print('Configuration loaded successfully')"

# Test document processing
python -c "from document_processor.processor import DocumentProcessor; print('Document processor ready')"

# Test RAG system
python -c "from rag_system.retriever import RAGRetriever; print('RAG system ready')"
```

### Performance Optimization

- **Caching**: Implement response caching for repeated queries
- **Batch Processing**: Process multiple documents simultaneously
- **Model Selection**: Use appropriate model sizes for different tasks
- **Vector Store Optimization**: Tune ChromaDB settings for your data size

## Security Considerations

- Store API keys securely (never commit `.env` files)
- Implement rate limiting for production deployment
- Use HTTPS for production deployments
- Regularly update dependencies for security patches
- Consider data privacy regulations for training session storage

## Support and Contributing

### Getting Help
- Check the troubleshooting section above
- Review logs in `logs/` directory
- Ensure all dependencies are installed correctly

### Contributing
1. Fork the repository
2. Create feature branches
3. Follow existing code style
4. Add tests for new functionality
5. Submit pull requests with clear descriptions

## License

This project is developed for educational purposes as part of INFO 5940 - Fall 2025.

## Acknowledgments

- Built with Streamlit for the web interface
- Uses ChromaDB for vector storage
- Integrates with various LLM providers
- Supports multiple document formats through specialized libraries

---

For questions or support, please refer to the troubleshooting section or check the application logs for detailed error information.