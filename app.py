import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
import json
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize ChromaDB
chroma_client = chromadb.Client()
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-ada-002"
)
collection = chroma_client.get_or_create_collection(
    name="data_store",
    embedding_function=openai_ef
)

frontend_tool_collection = chroma_client.get_or_create_collection(
    name="frontend_tool",
    embedding_function=openai_ef
)

# Set page config
st.set_page_config(
    page_title="Ag Data Fusion Agent",
    page_icon="🌾",
    layout="wide"
)

# Custom CSS for the chat input
st.markdown("""
    <style>
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
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

def store_data(content, data_type, metadata=None):
    """Store data in ChromaDB with metadata"""
    if metadata is None:
        metadata = {}
    
    # Add common metadata
    metadata.update({
        "timestamp": datetime.now().isoformat(),
        "data_type": data_type,
        "id": str(uuid.uuid4())
    })
    
    # Store in ChromaDB
    collection.add(
        documents=[content],
        metadatas=[metadata],
        ids=[metadata["id"]]
    )

def process_file(file):
    """Process uploaded file and store in vector database"""
    try:
        # Read file content
        content = file.getvalue().decode("utf-8")
        
        # Create metadata
        metadata = {
            "filename": file.name,
            "file_type": file.type,
            "file_size": len(content),
            "source": "file_upload"
        }
        
        # Store in vector database
        store_data(content, "file", metadata)
        return True
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return False

def process_text(text, source="chat"):
    """Process text input and store in vector database"""
    try:
        metadata = {
            "source": source,
            "content_type": "text"
        }
        
        # Store in vector database
        store_data(text, "text", metadata)
        return True
    except Exception as e:
        st.error(f"Error processing text: {str(e)}")
        return False

# File upload section
uploaded_file = st.file_uploader("Upload a file", type=["txt", "image", "csv", "json", "pdf"])
if uploaded_file is not None:
    if process_file(uploaded_file):
        st.success("File processed and stored successfully!")

# Chat input
if prompt := st.chat_input("Ask me anything...", key="chat_input"):
    # Process and store the user's input
    process_text(prompt, "chat")
    
    # Add user message to chat history (keep this)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get relevant context from ChromaDB
    results = collection.query(
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
    
    # Add assistant response to chat history (keep this)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Store the assistant's response
    process_text(full_response, "assistant_response") 