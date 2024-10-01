from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
import logging

# Clear the environment variable for security
if 'OPENAI_API_KEY' in os.environ:
    del os.environ['OPENAI_API_KEY']

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Ensure the API key is provided
if not api_key:
    raise ValueError("API key is missing. Make sure it's set in the environment variables.")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Step 1: Create a new Assistant with File Search Enabled
assistant = client.beta.assistants.create(
    name="Physical Therapist",
    instructions="You are a highly-qualified and personable physical therapist. Use your knowledge to answer questions about audited financial statements.",
    model="gpt-4o",
    tools=[{"type": "file_search"}],
)

# Step 2: Create a vector store and upload files
vector_store = client.beta.vector_stores.create(name="backExercises")
file_paths = ["filePath/back.pdf"]
file_streams = [open(path, "rb") for path in file_paths]

file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id, files=file_streams
)

# Step 3: Update the assistant to use the new vector store
assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# Step 4: Create a thread and attach the file to the message
message_file = client.files.create(
    file=open("filePath/back.pdf", "rb"), purpose="assistants"
)

thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "Can you guide me through the cat cow exercise?",
            "attachments": [
                {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
            ],
        }
    ]
)

# Step 5: Create a run and stream the response
from openai import AssistantEventHandler

class EventHandler(AssistantEventHandler):
    def on_text_created(self, text):
        print(f"\nassistant > {text}", end="")

    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n")

    def on_message_done(self, message):
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        print(message_content.value)
        print("\n".join(citations))

with client.beta.threads.runs.stream(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Address the user as Jane Doe. Use simple language appropriate for an older user.",
    event_handler=EventHandler(),
) as stream:
    stream.until_done()

