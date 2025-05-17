import os
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import time
import threading
from datetime import datetime
import uuid

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

        
    def create_collection(self, name):
        """Create a new collection"""
        try:
            return self.client.create_collection(
                name=name,
                embedding_function=self.embedding_function
            )
        except Exception as e:
            print(f"Error creating collection {name}: {str(e)}")
            return None
    
    def get_collection(self, name):
        """Get a collection by name or create it if it doesn't exist"""
        try:
            return self.client.get_or_create_collection(
                name=name,
                embedding_function=self.embedding_function
            )
        except Exception as e:
            print(f"Error getting or creating collection {name}: {str(e)}")
            return None
    
    def list_collections(self):
        """List all collections"""
        try:
            return self.client.list_collections()
        except Exception as e:
            print(f"Error listing collections: {str(e)}")
            return []
    
    def sync_to_disk(self):
        """Force a sync of the database to disk - no longer needed as ChromaDB handles this automatically"""
        pass 


    def store_data(self,collection_name, content, metadata= {}):
        collection = self.get_collection(collection_name)

        # Add common metadata
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        })
        
        # Store in ChromaDB
        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[metadata["id"]]
        )

    def query_data(self, collection_name, query, n_results=5):
        collection = self.get_collection(collection_name)
        return collection.query(query_texts=[query], n_results=n_results, include=["documents", "metadatas", "distances"])
    
    def delete_data(self, collection_name, id):
        collection = self.get_collection(collection_name)
        collection.delete(ids=[id])

