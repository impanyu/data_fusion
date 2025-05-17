import uuid
from datetime import datetime
from system_prompt import UI_PROMPT, TOOL_SEARCH_PROMPT, DATA_SEARCH_PROMPT, WEB_SEARCH_PROMPT
import json
import os
import PyPDF2
from io import BytesIO

from openai import OpenAI
from db_manager import DBManager
from dotenv import load_dotenv
from native_tools import invoke_native_tool
from search_api import SearchAPI
import traceback

# Load environment variables
load_dotenv()

class QuerySolver:
    def __init__(self):
        """
        Initialize QuerySolver 
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Initialize database manager (replaces previous ChromaDB initialization)
        self.db_manager = DBManager(persist_dir="./vector_db")
        self.data_collection = self.db_manager.get_collection("data_store")
        self.search_api = SearchAPI(api_key=os.getenv("SEARCH_API_KEY"))



    def solve_query(self, prompt, file_paths=[], depth = 0):
        """Process query with optional file context"""

        
        # Query the data store
        results = self.db_manager.query_data("data_store", prompt, 5)
        
        # Prepare context
        context_items = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            context_items.append(f"From {meta.get('id', 'Unknown')}: {doc}")
        
        context = "\n\n".join(context_items)


        # Get response from OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": DATA_SEARCH_PROMPT},
                {"role": "user", "content": f"Context: {context}\n\nQuery: {prompt}\n\nFiles: {file_paths}"}
            ]
      
        )

        response_json = json.loads(response.choices[0].message.content)

        if response_json["complete"] == "True":
            pass
        elif response_json["complete"] == "Tool":
            tool_result = invoke_native_tool(response_json["result"]["tool_name"], response_json["result"]["tool_args"], self.db_manager)
            response_json["result"] = tool_result
            response_json["complete"] = "True"
        else:
            # Query the internet using search API
            try:
                search_results = self.search_api.search(prompt, max_results=5)
                search_context = "\n".join([
                    f"From {result['title']} ({result['url']}):\n{result['content']}"
                    for result in search_results
                ])
                
                # Combine with existing context
                context = f"{context}\n\nWeb Search Results:\n{search_context}"
                
                # Get new response with search results
                new_response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": WEB_SEARCH_PROMPT},
                        {"role": "user", "content": f"Context: {context}\n\nQuery: {prompt}"}
                    ]
    
                )
                
                response_json = json.loads(new_response.choices[0].message.content)
                
            except Exception as e:
                print(f"Search API error: {str(e)}")
                # Continue with original response if search fails
                pass

        if response_json["complete"] == "False":
            # go to interpret_query
            response_json = self.interpret_query(prompt, context, file_paths,depth)

        if not response_json["complete"] == "False":
            if not depth == 0:
                return response_json
            else:
                ui = self.determine_ui(response_json["result"])
                response_json["UI"] = ui
                return response_json
            
    

    def determine_ui(self, result):
        #use LLM to determine the UI
        result_string = json.dumps(result)[:500]
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": UI_PROMPT},
                       {"role": "user", "content": f"Context: {result_string}"}]
        )
        return response.choices[0].message.content

    

    def interpret_query(self, prompt, context, files=[]):
        """Interpret query and return appropriate response"""
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": TOOL_SEARCH_PROMPT},
                {"role": "user", "content": f"Context: {context}Task: {prompt}\n\nInput files: {files}"}
            ]
        )
        code = json.loads(response.choices[0].message.content)
        if not code == "Failed":
            # Create a namespace dictionary to store variables
            namespace = {}
            
            
            # Execute the code in the namespace
            try:
                exec(code, namespace)
                # Get the result from the namespace
                result = namespace.get('result')
                if result is None:
                    return {"result": "Error: Code execution did not produce a result", "error": True}
                
                return result
            except Exception as e:
                error_message = f"Error executing code:\n{traceback.format_exc()}"
                print(error_message)  # For logging
                return {"result": error_message, "error": True}
        else:
            return {"result": "Failed", "complete": "False"}

 



    