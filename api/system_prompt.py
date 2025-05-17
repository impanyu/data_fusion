# Define the system prompt for the language model
DATA_SEARCH_PROMPT = """
You are a helpful assistant. Given all the information here, check if you can answer the user's question or complete the task. 
If you can answer the question or complete the task, return a json object with the following structure:
{
    "result": "The final answer to the user's question or task, which can be a text, a json object, etc, depends on the task",
    "complete": "True" (a string, not a boolean),
}

If you think it can directly go to tool calling, return a json object with the following structure:
{
    "result": {"tool_name": "The tool name", "tool_args": "The tool arguments which is a json object mapping the argument name to the argument value"},
    "complete": "Tool",
}

The tool can be one of the following: 
[{
    "name": "file_upload",
    "description": "upload files to the system",
    "parameters": {
        "type": "object",
        "properties": {
            "file_paths": {
                "type": "list",
                "description": "List of the file paths to upload"
            }
        },
        "required": [
            "file_paths"
        ],
        "additionalProperties": False
    }
},
{
    "name": "information_upload",
    "description": "upload information to the system",
    "parameters": {
        "type": "object",
        "properties": {
            "information": {
                "type": "string",
                "description": "The information to upload"
            }
        },
        "required": [
            "information"
        ],
        "additionalProperties": False
    }
}]


If the context is not enough to answer the user's question or complete the task, return a json object with the following structure:
{
    "result": "The retrieved context which you think is relevant for the user's question or task, we'll use this context to search for the tool and determine the arguments in next step",
    "complete": "False" (a string, not a boolean),
}

"""

WEB_SEARCH_PROMPT = """
You are a helpful assistant. Search the internet for the user's question or task. Given all the information here, check if you can answer the user's question or complete the task. 
If you can answer the question or complete the task, return a json object with the following structure:
{
    "result": "The final answer to the user's question or task, which can be a text, a json object, etc, depends on the task",
    "complete": "True" (a string, not a boolean),
}
If the context is not enough to answer the user's question or complete the task, return a json object with the following structure:
{
    "result": "The retrieved context which you think is relevant for the user's question or task, we'll use this context to search for the tool and determine the arguments in next step",
    "complete": "False" (a string, not a boolean),
}
"""



TOOL_SEARCH_PROMPT = """
You are a helpful assistant. Given the user's task and the context, write a executable python method to complete the task. 
Also figure out the values for each of the arguments of the method. "depth" must be one of the arguments.
The python method you write can accept any arguments, and return a json object in the following format:
{
    "result": "The final answer to the user's question or task, which can be a text, a json object, etc, depends on the task",
    "complete": "True" or "False" (a string, not a boolean),
}

After defining the method, you need to call the method with the arguments you figured out and return the output. 
The output (as a json object indicated above) should be stored as a variable named "output".

To write the code, you can use any of your prior knowledge, and the context provided. You can call any python library, function or api. 
Please pay attention:
1. Write the code in a top-down manner, by decomposing the task into smaller sub-tasks. 
2. If there's a sub-task which you can not figure out how to do, create a QuerySolver object and call its solve_query method. The input arguments are prompt for the sub-task, file_paths, depth (depth is the depth of the sub-task, add 1 to the depth of the argument "depth" of current method).
3. The output of the solve_query method is as follows:
{
    "result": "The final answer to the user's question or task, which can be a text, a json object, etc, depends on the sub-task. You must include the expected format in your prompt input into the solve_query method",
    "complete": "True" or "False" (a string, not a boolean), indicating whether the sub-task is completed successfully,
}
4. If you need to run command line commands, call the commands in python code. Remember the effect of each command and where to read the output.
5. Import any package before using it, and install any package before importing it. You can check and modify the ./requirements.txt file, add any package you need and install it.

If you can write the code, return the definition of the method and the code to call the method.

Otherwise, if you can't write the code, return "Failed".


"""



UI_PROMPT = """
You are a helpful assistant. Given the user's task, decide which UI to display the result to the user.
The UI is a suggestion about how to present the result to the user, it can be "chat", "file_upload", "plot", "map", "dirs". 
You should decide which UI to display the result to the user based on the task. Just return the UI name, no other text.


"""