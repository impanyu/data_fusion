import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
import json
from datetime import datetime
import uuid
from text_processor import process_text, process_file  # Import the new functions
from db_manager import DBManager

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize database manager (replaces previous ChromaDB initialization)
db_manager = DBManager(persist_dir="./vector_db")
data_collection = db_manager.get_collection("data_store")
frontend_tool_collection = db_manager.get_collection("frontend_tool")


# Set page config
st.set_page_config(
    page_title="Ag Data Fusion Agent",
    page_icon="🌾",
    layout="wide"
)

# Custom CSS for the chat input and page height
st.markdown("""
    <style>
    /* Reduce default page margins and add border */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        padding-left: 3rem;
        padding-right: 3rem;
       
 
    }
    
    /* Set chat message width */
    div[data-testid="stBottomBlockContainer"] {
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }
    
    div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: none !important;
    }
    
    .stTextInput>div>div>input {
        font-size: 1.2rem;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px solid #ccc;
    }
    .stTextInput>div>div>input:focus {
        border-color: #4CAF50;
        box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
    }
    
    /* Increase page height */
    .main {
        min-height: 100vh;
    }
    .stApp {
        min-height: 100vh;
    }
    section[data-testid="stSidebar"] {
        min-height: 100vh;
    }
    
    /* Chat input container styling */
    .chat-input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 1rem 3rem;
        border-top: 1px solid #e5e7eb;
    }
    
    /* Input box styling */
    .input-group {
        display: flex;
        align-items: center;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 1rem;
        padding: 0.5rem;
    }
    
    .action-buttons {
        display: flex;
        gap: 0.5rem;
        padding: 0.5rem;
    }
    
    .action-button {
        background: transparent;
        border: none;
        padding: 0.5rem;
        border-radius: 0.5rem;
        cursor: pointer;
    }
    
    .action-button:hover {
        background: #f3f4f6;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task" not in st.session_state:
    st.session_state.current_task = "Current Task"

# Create a placeholder for the summary bar
summary_placeholder = st.empty()

# Function to update summary bar
def update_summary_bar():
    summary_placeholder.markdown(
        f"""
        <style>
        .summary-bar {{
            background-color: #e8f1ff;  /* Light blue color */
            padding: 1rem;
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;  /* Smaller text size */
            font-family: 'Inter', sans-serif;
            font-weight: 600;  /* Semi-bold */
            letter-spacing: 0.02em;  /* Slight letter spacing */
            color: #1E293B;  /* Dark slate color */
            text-transform: uppercase;  /* Optional: makes it more title-like */
        }}
        </style>
        <div class="summary-bar">
        {st.session_state.current_task}</div>
        """,
        unsafe_allow_html=True
    )

# Initial display of summary bar
update_summary_bar()

# Create columns for the input area
col1, col2 = st.columns([1, 11])

with col1:
    st.button("➕", key="add_button")

with col2:
    if prompt := st.chat_input("Ask me anything..."):
        # Update current task and summary bar immediately
        st.session_state.current_task = prompt
        update_summary_bar()
        
        # Process and store the user's input
        process_text(data_collection, prompt, "chat")
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get relevant context from ChromaDB
        results = data_collection.query(
            query_texts=[prompt],
            n_results=5,
            include=["documents", "metadatas", "distances"]
        )
        
        # Prepare context for the LLM
        context_items = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            source = meta.get('source', 'Unknown')
            if source == 'file':
                context_items.append(f"From file '{meta.get('filename', 'Unknown')}': {doc}")
            else:
                context_items.append(f"From {source}: {doc}")
        
        context = "\n\n".join(context_items)
        
        # Generate response using OpenAI
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            for response in client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Use the following context to answer the user's question. If the context is not relevant, use your general knowledge."},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {prompt}"}
                ],
                stream=True,
            ):
                if response.choices[0].delta.content is not None:
                    full_response += response.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # Store the assistant's response
        #process_text(data_collection, full_response, "assistant_response")

# Handle file upload when + button is clicked
if st.session_state.get("add_button"):
    st.session_state.show_file_upload = True
    st.rerun()

# File upload section
uploaded_file = st.file_uploader("Upload a file", type=["txt", "image", "csv", "json", "pdf"])
if uploaded_file is not None:
    result = process_file(data_collection, uploaded_file)
    if isinstance(result, tuple):  # Error occurred
        st.error(f"Error processing file: {result[1]}")
    elif result:
        st.success("File processed and stored successfully!")