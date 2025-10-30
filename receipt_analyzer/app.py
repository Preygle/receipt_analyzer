
import os
import tempfile
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import boto3
from datetime import datetime
import json
from extract_receipt import extract_receipt_data
from classifier import classify_transaction

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Hardcoded users
USERS = {
    "user1": "password",
    "user2": "password",
    "user3": "password"
}

import tempfile

DYNAMODB_TABLE = 'ReceiptsTable'  # Replace with your DynamoDB table name
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'receipt' not in request.files:
            return redirect(request.url)
        file = request.files['receipt']
        if file.filename == '':
            return redirect(request.url)
        if file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"receipt_{timestamp}.{file.filename.rsplit('.', 1)[1].lower()}"
            try:
                s3.upload_fileobj(file, S3_BUCKET, filename)
                
                s3_object = s3.get_object(Bucket=S3_BUCKET, Key=filename)
                image_bytes = s3_object['Body'].read()

                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_image_path = os.path.join(tmpdir, filename)
                    with open(tmp_image_path, "wb") as f:
                        f.write(image_bytes)

                    extracted_data = extract_receipt_data(tmp_image_path)

                if not extracted_data:
                    return "Could not extract data from receipt", 400

                classification = classify_transaction(extracted_data[0])

                receipt_id = filename.split('.')[0]
                user = session['user']
                date = extracted_data[0].get('date')
                category = classification.get('category')
                total = extracted_data[0].get('total')
                items = extracted_data[0].get('items')

                table.put_item(
                    Item={
                        'receipt_id': receipt_id,
                        'user': user,
                        'date': date,
                        'category': category,
                        'total': total,
                        'items': items
                    }
                )

            except Exception as e:
                # Handle S3 upload error
                print(f"Error: {e}")
                return f"Error: {e}", 500
            return redirect(url_for('dashboard'))

    return render_template('upload.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('upload'))
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)

@app.route('/')
def home():
    return redirect(url_for('login'))

from datetime import datetime, timedelta

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    period = request.args.get('period', '7')  # Default to last 7 days

    end_date = datetime.now()
    if period == '7':
        start_date = end_date - timedelta(days=7)
    elif period == '30':
        start_date = end_date - timedelta(days=30)
    elif period == 'month':
        start_date = end_date.replace(day=1)
    elif period == 'year':
        start_date = end_date.replace(month=1, day=1)
    else:
        start_date = end_date - timedelta(days=7)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    try:
        response = table.query(
            IndexName='user-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user').eq(user) & boto3.dynamodb.conditions.Key('date').between(start_date_str, end_date_str)
        )
        receipts = response.get('Items', [])
    except Exception as e:
        print(f"Error fetching from DynamoDB: {e}")
        # Fallback to querying only by user if date range query fails
        try:
            response = table.query(
                IndexName='user-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('user').eq(user)
            )
            receipts = response.get('Items', [])
        except Exception as e2:
            print(f"Error fetching from DynamoDB by user only: {e2}")
            receipts = []


    return render_template('dashboard.html', receipts=receipts)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
