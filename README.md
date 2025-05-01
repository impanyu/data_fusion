# Data Fusion Agent

A Streamlit-based chat application that allows users to interact with an AI agent powered by OpenAI's GPT-4.

## Features

- Modern chat interface with browser-like input box
- Real-time streaming responses
- Conversation history persistence
- Vector-based context retrieval using ChromaDB
- Powered by OpenAI's GPT-4

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to the `.env` file

4. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Open your browser to the URL shown in the terminal (typically http://localhost:8501)
2. Type your questions in the chat input box at the top of the page
3. View the responses in the chat history below
4. The conversation history is automatically saved and can be used for context in future queries

## Architecture

- Frontend: Streamlit
- LLM: OpenAI GPT-4
- Vector Store: ChromaDB
- Embeddings: OpenAI's text-embedding-ada-002
