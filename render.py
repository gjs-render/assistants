from flask import Flask, request, jsonify, render_template, redirect, url_for
from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# Configure logging
logging.basicConfig(level=logging.INFO)

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
        assistant_reply = response.choices[0].message['content']
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
