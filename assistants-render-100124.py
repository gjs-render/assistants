from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')  # Render the HTML file

# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form.get('user_input')  # Get input from form
    logging.info(f"User input: {user_input}")
    # Process the input (for example, call OpenAI API here)
    return redirect(url_for('home'))  # Redirect back to home after submission

if __name__ == '__main__':
    app.run(debug=True)
