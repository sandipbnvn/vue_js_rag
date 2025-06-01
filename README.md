# RAG Chatbot with Web Search

A modern, full-stack RAG (Retrieval-Augmented Generation) chatbot that combines document knowledge with real-time web search capabilities.

## ✨ Features

- **PDF Document Processing**: Upload and process multiple PDF documents
- **Intelligent Document Search**: Vector-based similarity search through your documents
- **AI-Powered Conversations**: GPT-powered responses with source attribution
- **Web Search Integration**: Fallback to web search when documents don't contain sufficient information
- **User Permission System**: Always asks before searching the web
- **Modern UI**: Beautiful Vue.js interface with typewriter effects
- **Conversation History**: Track and manage your chat sessions
- **Source Attribution**: Clear citations for both document and web sources

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))
- Tavily API Key ([Get one here](https://tavily.com)) - Optional for web search

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ragbot
```

### 2. Set Up Environment Variables

Copy the example environment file and add your API keys:

```bash
cp env.example .env
```

Edit the `.env` file with your API keys:

```bash
# Required - OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Optional - Tavily Web Search API Key (for web search functionality)
TAVILY_API_KEY=your_tavily_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./ragbot.db

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=False
```

**Important**: 
- **OPENAI_API_KEY** is required for the chatbot to work
- **TAVILY_API_KEY** is optional - if not provided, web search will be disabled
- Never commit your `.env` file with real API keys to version control

### 3. Backend Setup

```bash
# Create virtual environment
python -m venv env

# Activate virtual environment
# Windows:
env\Scripts\activate
# macOS/Linux:
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
cd backend
python main.py
```

The backend will start at `http://localhost:8000`

### 4. Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
npm run serve
```

The frontend will start at `http://localhost:8080`

## 🔧 Configuration

### API Keys Setup

#### OpenAI API Key (Required)
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add it to your `.env` file as `OPENAI_API_KEY=your_key_here`

#### Tavily API Key (Optional - for Web Search)
1. Go to [Tavily](https://tavily.com)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add it to your `.env` file as `TAVILY_API_KEY=your_key_here`

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | OpenAI API key for GPT responses |
| `TAVILY_API_KEY` | ❌ No | - | Tavily API key for web search |
| `DATABASE_URL` | ❌ No | `sqlite:///./ragbot.db` | Database connection string |
| `APP_HOST` | ❌ No | `0.0.0.0` | Backend server host |
| `APP_PORT` | ❌ No | `8000` | Backend server port |

## 🎯 How It Works

1. **Upload Documents**: Upload PDF files through the web interface
2. **Ask Questions**: Type questions about your documents
3. **Smart Responses**: The AI searches your documents first
4. **Web Search Fallback**: If documents don't contain enough info, AI asks permission to search the web
5. **User Control**: You decide whether to allow web search for each query
6. **Comprehensive Answers**: Get responses combining both document and web sources

## 🛠️ Technical Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **OpenAI GPT**: Language model for intelligent responses
- **FAISS**: Vector database for document similarity search
- **Tavily**: Web search API integration
- **SQLite**: Conversation history storage
- **PyPDF2**: PDF text extraction

### Frontend
- **Vue.js 3**: Progressive JavaScript framework
- **Bootstrap 5**: Modern UI components
- **Axios**: HTTP client for API communication

## 🔍 Troubleshooting

### Backend Won't Start

**Error**: `ValueError: OPENAI_API_KEY environment variable is required`

**Solution**: 
1. Make sure you have a `.env` file in the root directory
2. Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`
3. Restart the backend server

### Web Search Not Working

**Issue**: Web search option doesn't appear

**Solution**: 
1. Add Tavily API key to `.env`: `TAVILY_API_KEY=your_key_here`
2. Restart the backend server
3. Check the health endpoint: `http://localhost:8000/health`

### PDF Upload Issues

**Issue**: PDF processing fails

**Solutions**:
1. Ensure PDF contains extractable text (not just images)
2. Check file size (limit: 50MB)
3. Try with a different PDF file

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Security Note

- Never commit your `.env` file with real API keys
- Use environment variables for all sensitive configuration
- Consider using API key rotation for production deployments
- Restrict API key permissions to minimum required scope 