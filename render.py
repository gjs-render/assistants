from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
import logging

# Clear the environment variable
if 'OPENAI_API_KEY' in os.environ:
    del os.environ['OPENAI_API_KEY']

# Load environment variables
load_dotenv()

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

# Configure logging
#logging.basicConfig(level=logging.INFO)



# Step 1: Create a new Assistant with File Search Enabled
assistant = client.beta.assistants.create(
  name="Financial Analyst Assistant",
  instructions="You are an expert financial analyst. Use you knowledge base to answer questions about audited financial statements.",
  model="gpt-4o",
  tools=[{"type": "file_search"}],
)


'''
"name": "Web Development Assistant",
"instructions": "You are an expert web developer. You can search for files, read and analyze the contents of HTML and CSS files, and propose revisions.",
"model": "gpt-4o",
"tools": [
        {"type": "file_search"},  # Enables file search capabilities
        {"type": "file_analysis", "languages": ["HTML", "CSS"]},  # Enables reading and analyzing HTML and CSS files
        {"type": "code_suggestion", "languages": ["HTML", "CSS"]}  # Enables coding suggestions for HTML and CSS
        }
]
'''


# Step 2: Upload files and add them to a Vector Store
# Create a vector store caled "Financial Statements"
vector_store = client.beta.vector_stores.create(name="Financial Statements")
 
# Ready the files for upload to OpenAI
file_paths = ["filePath/aapl-10K.pdf", "filePath/brka-10k.pdf"]
file_streams = [open(path, "rb") for path in file_paths]
 
# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)
 
# You can print the status and the file counts of the batch to see the result of this operation.
# print(file_batch.status)
# print(file_batch.file_counts)



# Step 3: Update the assistant to use the new Vector Store
assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)



# 04 Step 4: Create a thread
# Upload the user provided file to OpenAI
message_file = client.files.create(
  file=open("filePath/aapl-10k.pdf", "rb"), purpose="assistants"
)
 
# Create a thread and attach the file to the message
thread = client.beta.threads.create(
  messages=[
    {
      "role": "user",
      "content": "How many shares of AAPL were outstanding at the end of of October 2023?",
      # Attach the new file to the message.
      "attachments": [
        { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
      ],
    }
  ]
)
 
# The thread now has a vector store with that file in its tool resources.
#print(thread.tool_resources.file_search)



# Step 5: Create a run and check the output
from typing_extensions import override
from openai import AssistantEventHandler, OpenAI
 

############################################

class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) → None:
        print(f"\nassistant > “, end=”", flush=True)

# Then, we use the stream SDK helper
# with the EventHandler class to create the Run
# and stream the response.run = None

with self.client.beta.threads.runs.stream(
        thread_id=thread_id,
        assistant_id=assistant_id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()
        run = stream.get_final_run()
 




