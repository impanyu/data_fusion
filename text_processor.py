import uuid
from datetime import datetime

def store_data(collection, content, data_type, metadata=None):
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

def process_text(collection, text, source="chat"):
    """Process text input and store in vector database"""
    try:
        metadata = {
            "source": source,
            "content_type": "text"
        }
        
        # Store in vector database
        store_data(collection, text, "text", metadata)
        return True
    except Exception as e:
        return False, str(e)

def process_file(collection, file):
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
        store_data(collection, content, "file", metadata)
        return True
    except Exception as e:
        return False, str(e) 