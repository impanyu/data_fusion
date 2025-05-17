import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from chromadb.utils import embedding_functions
import json
from datetime import datetime
import uuid
from text_processor import process_text, process_file  # Import the new functions
from db_manager import DBManager
from query_solver import query_solving

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    
    /* Style the + button */
    .stButton > button {
        margin-top: 0.5rem;
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

# Create a row for summary bar and + button
col1, col2 = st.columns([11, 1])

with col1:
    # Create a placeholder for the summary bar inside the first column
    summary_placeholder = st.empty()
    
    # Function to update summary bar
    def update_summary_bar():
        summary_placeholder.markdown(
            f"""
            <style>
            .summary-bar {{
                background-color: #e8f1ff;
                padding: 1rem;
                padding-top: 0.5rem;
                padding-bottom: 0.5rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                font-size: 0.9rem;
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                letter-spacing: 0.02em;
                color: #1E293B;
                text-transform: uppercase;
            }}
            </style>
            <div class="summary-bar">
            {st.session_state.current_task}</div>
            """,
            unsafe_allow_html=True
        )

    # Initial display of summary bar
    update_summary_bar()

with col2:
    if st.button("➕", key="add_button", help="Upload"):
        st.session_state.show_file_upload = not st.session_state.get("show_file_upload", False)
        if st.session_state.show_file_upload:
            st.session_state.current_task = "Uploading files"
            update_summary_bar()


file_paths = []

# File upload section
if st.session_state.get("show_file_upload", False):
    uploaded_files = st.file_uploader("", type=["txt", "image", "csv", "json", "pdf"], accept_multiple_files=True, label_visibility="collapsed")
    if uploaded_files:
        for file in uploaded_files:
            result = process_file(db_manager, file)
            if isinstance(result, tuple):
                st.error(f"Error processing file: {result[1]}")
            elif result:
                file_paths.append(result)
                st.success("File processed and stored successfully!")
    

# Chat input (this will automatically stay at the bottom)
if prompt := st.chat_input("Ask me anything..."):
    # Update current task and summary bar immediately
    st.session_state.current_task = prompt
    update_summary_bar()
    
    # Process and store the user's input
    #process_text(db_manager, prompt, client, file_paths)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    
    # Generate response using OpenAI
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Stream the response
        for response in client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Use the following context to answer the user's question. If the context is not relevant, use your general knowledge."},
                {"role": "user", "content": f"Question: {prompt}"}
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
