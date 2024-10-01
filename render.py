from flask import Flask, request, jsonify, render_template, redirect, url_for
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

# Initialize Flask app
app = Flask(__name__)

# Configure logging
#logging.basicConfig(level=logging.INFO)



# Step 1: Create a new Assistant with File Search Enabled
assistant = client.beta.assistants.create(
  name="Physical Therapist",
  instructions="You are a Highly-Qualified and Personable Physical Therapist. Use you knowledge base to answer questions about audited financial statements.",
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
vector_store = client.beta.vector_stores.create(name="backExercises")
 
# Ready the files for upload to OpenAI
file_paths = ["filePath/back.pdf"]
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
  file=open("filePath/back.pdf", "rb"), purpose="assistants"
)
 
# Create a thread and attach the file to the message
thread = client.beta.threads.create(
  messages=[
    {
      "role": "user",
      "content": "you offered to guide me through the cat cow exercise",
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
        # print a citation to the file searched
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


# Then, we use the stream SDK helper
# with the EventHandler class to create the Run
# and stream the response.

with client.beta.threads.runs.stream(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Please address the user as Jane Doe. The user has a premium account and she is a bit older. Please explain to here in very simple language.",
    event_handler=EventHandler(),
) as stream:
    stream.until_done()

# Route for the home page
@app.route('/')
def home():
    return render_template('assistants-render-100124.html')  # Render the HTML file

# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form.get('user_input')  # Get input from form
    logging.info(f"User input: {user_input}")
    
    try:
        # Process the input by calling the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or any other model you are using
            messages=[
                {"role": "user", "content": user_input}
            ]
        )
        # Extract the response content
        assistant_reply = response.choices[0].message.content
        logging.info(f"Assistant response: {assistant_reply}")
        
        # You can choose to render the response on the home page or redirect with a success message
        return redirect(url_for('home'))  # Redirect back to home after submission
    except OpenAIError as e:
        logging.error(f"OpenAI API Error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")  # Log the full error message
        logging.error("Full traceback:", exc_info=True)  # Log the traceback
        return jsonify({"error": "An unexpected error occurred."}), 500


if __name__ == '__main__':
    app.run(debug=True)
