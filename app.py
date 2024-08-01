from flask import Flask, jsonify, render_template,render_template_string, make_response, request, redirect, url_for
import json
app = Flask(__name__)
from functools import wraps
from datetime import datetime, timedelta
import calendar as calendar
import decimal as Decimal
import time as time
from decimal import Decimal
from PIL import Image
import pytesseract
import re
import numpy as np
from collections import defaultdict
import os

UPLOAD_COUNTS = defaultdict(int)
ACTIVE_REQUESTS = int()


API_KEYS = {"test-key123"}

def load_counts():
    global UPLOAD_COUNTS
    if os.path.exists('upload_counts.json'):
        with open('upload_counts.json', 'r') as f:
            UPLOAD_COUNTS = defaultdict(int, json.load(f))

def save_counts():
    global UPLOAD_COUNTS
    today = datetime.now().date().isoformat()
    UPLOAD_COUNTS[today] += 1
    with open('upload_counts.json', 'w') as f:
        json.dump(dict(UPLOAD_COUNTS), f)




def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


def require_api_key(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        global ACTIVE_REQUESTS
        ACTIVE_REQUESTS += 1
        try:
            api_key = request.headers.get('x-api-key')
            if not api_key or api_key not in API_KEYS:
                return jsonify({"error": "Unauthorized"}), 401
            return func(*args, **kwargs)
        finally:
            ACTIVE_REQUESTS -= 1
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

#start session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

@app.route("/secret-api-counter")
def secret_api_counter():
    today = datetime.now().date().isoformat()
    today_count = UPLOAD_COUNTS.get(today, 0)
    return render_template("secretcounter.html", upload_count=str(today_count), active_requests=ACTIVE_REQUESTS)


@app.route('/upload', methods=['POST'])
@require_api_key
def upload_image():
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
        save_counts()  # Call save_counts() here
        return jsonify(ocr_text)
    print("Invalid file type")
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/get_status')
def get_status():
    today = datetime.now().date().isoformat()
    today_count = UPLOAD_COUNTS.get(today, 0)
    print(UPLOAD_COUNTS)
    return jsonify({
        'count': str(today_count),
        'active_requests': str(ACTIVE_REQUESTS)
    })





if __name__ == '__main__':
    load_counts()
    app.run(host='0.0.0.0', port=6969, debug=True)


    
