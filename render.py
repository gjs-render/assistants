from flask import Flask, request, jsonify, render_template
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
    return render_template('templates/assistants-render-100124.html')  # Render the HTML file

# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form.get('user_input')  # Get input from form
    logging.info(f"User input: {user_input}")
    # Process the input (for example, call OpenAI API here)
    return redirect(url_for('home'))  # Redirect back to home after submission

if __name__ == '__main__':
    app.run(debug=True)
