from flask import Flask, request, jsonify, render_template
from openai import OpenAI, OpenAIError
import os
import logging 

app = Flask(__name__)

api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

logging.basicConfig(level=logging.INFO)


@app.route("/")
def index():
    return render_template("fileSearch.html")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.form.get("user_input")
        # Use your assistant logic here to handle the user's input
        response = assistant.get_response(user_input)
        return jsonify({"response": response})
    except OpenAIError as e:
        logging.error(f"Error during API call: {str(e)}")
        return jsonify({"error": "An unexpected error occurred."}), 500


# Step 1: Create a new Assistant with File Search Enabled
assistant = client.beta.assistants.create(
    name="Financial Analyst Assistant",
    instructions="You are an expert financial analyst. Use your knowledge base to answer questions about audited financial statements.",
    model="gpt-4o",
    tools=[{"type": "file_search"}],
)

# Step 2: Upload files and add them to a Vector Store
vector_store = client.beta.vector_stores.create(name="Financial Statements")

logging.info(f"Current Working Directory: {os.getcwd()}")

# Ready the files for upload to OpenAI
file_paths = ["./static/files/aapl-10K.pdf", "./static/files/brka-10K.pdf"]
file_streams = [open(path, "rb") for path in file_paths]

try:
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )
finally:
    for stream in file_streams:
        stream.close()

# Step 3: Update the assistant to use the new Vector Store
assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# Step 4: Create a thread
message_file = client.files.create(
    file=open("filePath/aapl-10k.pdf", "rb"), purpose="assistants"
)

thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "How many shares of AAPL were outstanding at the end of October 2023?",
            "attachments": [{"file_id": message_file.id, "tools": [{"type": "file_search"}]}],
        }
    ]
)

# Step 5: Create a run and check the output
from typing_extensions import override
from openai import AssistantEventHandler, OpenAI

client = OpenAI()

class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    @override
    def on_message_done(self, message) -> None:
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        print(message_content.value)
        print("\n".join(citations))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
