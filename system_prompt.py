# Define the system prompt for the language model
DATA_SEARCH_PROMPT = """
You are a helpful assistant. Check if the following context is enough to answer the user's question or complete the task. 
If the context is not relevant or not enough, or the user just tell you something or upload something, return a json object with the following structure:
{
    "result": "The retrieved context which you think is relevant for the user's question or task, we'll use this context to search for the tool and determine the arguments",
    "complete": False,
    "UI": "The UI to display the result to the user"
}
The UI can be "chat", "file_upload", "plot", "map", "dirs", you should decide which UI to display the result to the user based on the task.
If the context is relevant and enough, return a json object with the following structure:
{
    "result": "The final answer to the user's question or task",
    "complete": True,
    "UI": "chat"
}
"""

TOOL_SEARCH_PROMPT = """
You are a helpful assistant. Find which of the tools can be invoked to complete the task. Also extract the arguments for the tool, based on the context and user's task.

"""

TRANSFORM_PROMPT = """
You are a helpful assistant. Transform the tool result to the return format, which should be a json string.
"""