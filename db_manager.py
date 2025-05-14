import os
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import time
import threading

class DBManager:
    def __init__(self, persist_dir="./vector_db", sync_interval=300):  # sync every 5 minutes by default
        self.persist_dir = persist_dir
        self.sync_interval = sync_interval
        
        # Create persist directory if it doesn't exist
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=persist_dir
        )
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-ada-002"
        )
        
        # Get or create collections
        self.data_store = self.client.get_or_create_collection(
            name="data_store",
            embedding_function=self.embedding_function
        )
        
        self.frontend_tool = self.client.get_or_create_collection(
            name="frontend_tool",
            embedding_function=self.embedding_function
        )
    
    def sync_to_disk(self):
        """Force a sync of the database to disk - no longer needed as ChromaDB handles this automatically"""
        pass 