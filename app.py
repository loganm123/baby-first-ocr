from flask import Flask, jsonify, render_template,render_template_string, make_response, request, redirect, url_for
import json
app = Flask(__name__)
from functools import wraps
from datetime import datetime, timedelta
import calendar as calendar
import decimal as Decimal
import time as time
import datetime
from decimal import Decimal
from PIL import Image
import pytesseract
import re
import numpy as np
from collections import defaultdict
import os

UPLOAD_COUNTS = int()

API_KEYS = {"test-key123"}

def load_counts():
    global UPLOAD_COUNTS
    if os.path.exists('upload_counts.json'):
        with open('upload_counts.json', 'r') as f:
            UPLOAD_COUNTS = defaultdict(int, json.load(f))

def save_counts():
    global UPLOAD_COUNTS
    UPLOAD_COUNTS += 1


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


def require_api_key(func):
    def decorator(*args, **kwargs):
        # Get the API key from the request headers
        api_key = request.headers.get('x-api-key')
        
        # Check if the API key is present and valid
        if not api_key or api_key not in API_KEYS:
            # If the API key is missing or invalid, return a 401 Unauthorized response
            return jsonify({"error": "Unauthorized"}), 401
        
        # If the API key is valid, proceed with the original function
        return func(*args, **kwargs)
    
    # Set the name of the decorated function to the original function's name
    decorator.__name__ = func.__name__
    
    return decorator

def extract_price(line):
    pattern = r'\d+\.\d{2}'
    match = re.search(pattern, line)
    if match:
        return float(match.group())
    return None

def read_ocr(image_file):
    img = Image.open(image_file)
    img_np = np.array(img)
    text = pytesseract.image_to_string(img_np)
    lines = text.split('\n')
    receipt_data = []
    for index, line in enumerate(lines, start=1):
        if line.strip():
            receipt_data.append({
                "id": index,
                "line": line.strip(),
                "category": "unassigned",
                "price": extract_price(line)
            })
    receipt_data = [item for item in receipt_data if item['price'] is not None and not any(keyword in item['line'].upper() for keyword in ['AMOUNT', 'VISA', 'DISCOVER', 'AMEX', 'MASTERCARD','TAX','TOTAL'])]
    print(receipt_data)
    return receipt_data

"""
def process_receipt_data():
    receipt_data = session.get("receipt_data", [])
    
    for item in receipt_data:
        item['category'] = ai_categorize(item['line'])
    
    session["receipt_data"] = receipt_data
    return receipt_data
"""
#start session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

@app.route("/secret-api-counter")
def homepage():
    upload_count = str(UPLOAD_COUNTS)    
    return render_template("home.html", upload_count = upload_count)

@app.route('/upload', methods=['POST'])
@require_api_key
def upload_image():
    save_counts()
    if 'file' not in request.files:
        print("No file part'")
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        print("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        img = Image.open(file)
        img.show()
        ocr_text = read_ocr(file)
        #processed_data = process_receipt_data(
        return jsonify(ocr_text)
    print("Invalid file type")
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/get_count')
def get_count():
    return jsonify({'count': str(UPLOAD_COUNTS)})



#runs the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6969, debug=True)

    
