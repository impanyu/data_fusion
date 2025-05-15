import uuid
from datetime import datetime
from system_prompt import *
import json
import os
import PyPDF2
from io import BytesIO


return_format_mapping = {
    "chat": "string",
    "file_upload": "string",
    "plot": "dict",
    "map": "dict",
    "dirs": "list"
}

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

def process_text(db_manager, prompt, client, files = [], depth=0):

    data_collection = db_manager.get_collection("data_store")
    prompt = prompt 

    # First check if the prompt can be answered directly from the data store
    results = data_collection.query(
        query_texts=[prompt],   
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )
    
    # Prepare context for the LLM
    context_items = []
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        
        context_items.append(f"From {meta.get('id', 'Unknown')}: {doc}")

    
    context = "\n\n".join(context_items)

    #read the files and add to context
    for file_path in files:
        # only read text, csv, json, pdf files
        if file_path.endswith(('.txt', '.csv', '.json')):
            with open(file_path, "r") as file:
                context += f"\n\nFile content: {file.read()}"
        elif file_path.endswith('.pdf'):
            # Read PDF content
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_content = []
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():  # Only add non-empty pages
                        pdf_content.append(f"Page {page_num + 1}:\n{text}")
                context += f"\n\nPDF content: {'\n\n'.join(pdf_content)}"
    
    
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": DATA_SEARCH_PROMPT},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {prompt}"}
        ],
        response_format={
            "type": "json_object",
            "restrict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "complete": {"type": "boolean"}
                },
                "required": ["result", "complete"]
            }
        },
        stream=False,
    )

    response_json = json.loads(response.choices[0].message.content)


    if response_json["complete"]:
        return {"result": response_json["result"], "UI": "chat"}
    else:
        context =  response_json["result"]
        return_format = return_format_mapping[response_json["UI"]]

        interpret_result = interpret_user_input(db_manager, prompt, client, context, return_format, depth, files)
        return {"result": interpret_result["result"], "UI": response_json["UI"]}

def interpret_user_input(db_manager, prompt, client, context, return_format, depth=0, files=[]):
    data_collection = db_manager.get_collection("backend_tool")

    # First check if the prompt can be answered directly from the data store
    results = data_collection.query(
        query_texts=[prompt],
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )
    
    # Prepare context for the LLM
    tools = []
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]): 
        #doc should be a json string compatible with the tool schema
        tools.append(json.loads(doc))
    
    
    tools += "\n\n".join(tools)

    #add file_upload tool
    tools += [{
        "type": "function",
        "function": {
            "name": "file_upload",
            "description": "Upload and process files to the system",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The files to be uploaded"
                    }
                },
                "required": ["description"]
            }
        }
    }]
    

    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": TOOL_SEARCH_PROMPT},
            {"role": "user", "content": f"Context: {context}\n\n Tools: {tools}\n\n Task: {prompt}\n\n input_files: {files}"}
        ],
        tools=tools,
        parallel_tool_calls=False,
        stream=False,
    )

    retrieved_tools = json.loads(response.choices[0].message.content)
    
    if retrieved_tools is not []:
        tool_result = invoke_tool(db_manager, retrieved_tools[0]["name"], retrieved_tools[0]["arguments"])
        transform_result = transform_result(tool_result, return_format, client)
        return {"result": transform_result}
    else:
        return {"result": "Sorry, I tried but can't find the answer to the question", "UI": "chat"}

def transform_result(tool_result, return_format, client):
    if type(tool_result) == return_format:
        return tool_result
    # first transform the tool result to string
    if type(tool_result) == "dict":
        tool_result = json.dumps(tool_result)
    elif type(tool_result) == "list":
        tool_result = json.dumps(tool_result)
    elif type(tool_result) == "float" or type(tool_result) == "int":
        tool_result = str(tool_result)

    # then use llm to transform the tool result to the return format
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": TRANSFORM_PROMPT}, {"role": "user", "content": f"Tool result: {tool_result}\n\n Return format: {return_format}"}],
        stream=False,
    )
    # parse the response to the return format
    return_result = json.loads(response.choices[0].message.content)
    
    return return_result

def invoke_tool(db_manager, name, arguments):
    
    if name == "file_upload":
        process_file(db_manager, arguments["description"])


def process_file(db_manager, file):
    """Process uploaded file and store in vector database and local directory"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "./uploaded_files"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Get base filename and extension
        original_name = file.name
        base_name, extension = os.path.splitext(original_name)
        
        # Find a unique filename
        counter = 0
        file_path = os.path.join(upload_dir, original_name)
        while os.path.exists(file_path):
            counter += 1
            new_name = f"{base_name}_{counter}{extension}"
            file_path = os.path.join(upload_dir, new_name)
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(file.getvalue())
            
        # Process content based on file type
        if file.type.startswith('text/') or file.name.endswith(('.txt', '.csv', '.json')):
            content = file.getvalue().decode("utf-8")
        elif file.name.endswith('.pdf'):
            # Read PDF content
            pdf_content = []
            pdf_file = BytesIO(file.getvalue())
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():  # Only add non-empty pages
                    pdf_content.append(f"Page {page_num + 1}:\n{text}")
            
            content = "\n\n".join(pdf_content)
            if not content.strip():  # If no text was extracted
                content = f"PDF file (no extractable text): {file.name}"
        elif file.type.startswith('image/'):
            content = f"Binary image file: {file.name}"
        else:
            content = f"Binary file: {file.name}"
        
        # Create metadata
        metadata = {
            "name": os.path.basename(file_path),  # Use the actual saved filename
            "file_type": file.type,
            "size": len(file.getvalue()),
            "source": "file_upload",
            "path": file_path  # Store the local file path
        }
        data_collection = db_manager.get_collection("data_store")
        # Store in vector database
        store_data(data_collection, content, "file", metadata)
        return file_path
    except Exception as e:
        return False, str(e) 