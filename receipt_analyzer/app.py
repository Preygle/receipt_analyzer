import os
import tempfile
import re
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import boto3
from datetime import datetime, timedelta
import json
from decimal import Decimal
from extract_receipt import extract_receipt_data
from classifier import classify_transaction
from authlib.integrations.flask_client import OAuth

# ------------------- CONFIG -------------------
app = Flask(__name__)
app.secret_key = os.urandom(24)

# AWS Config
REGION = "us-east-1"  # change if needed
S3_BUCKET = "app-static-assets-1746"  # ✅ your S3 bucket
DYNAMODB_TABLE = "receipt_data"       # ✅ your DynamoDB table

# Initialize AWS clients
s3 = boto3.client("s3", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

# Cognito Config
oauth = OAuth(app)
oauth.register(
  name='oidc',
  authority='https://cognito-idp.us-east-1.amazonaws.com/us-east-1_jDi7cPq3E',
  client_id='65ldrp82mmqi7ua22r1chl4jej',
  # 🚨 Replace with your client secret
  client_secret='1ld338p8jrge2dt7vimbk6ude3sum2maa3kf64p8l1qv7p9jq7eh',
  server_metadata_url='https://cognito-idp.us-east-1.amazonaws.com/us-east-1_jDi7cPq3E/.well-known/openid-configuration',
  client_kwargs={'scope': 'email openid phone'}
)
# ------------------------------------------------

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.oidc.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = oauth.oidc.authorize_access_token()
    user = token['userinfo']
    session['user'] = user
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    # Redirect to Cognito to log out from there as well
    logout_url = oauth.oidc.server_metadata['end_session_endpoint']
    # The user will be redirected back to the home page after logging out from Cognito
    return redirect(f"{logout_url}?client_id={oauth.oidc.client_id}&logout_uri={url_for('home', _external=True)}")

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
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"receipt_{timestamp}.{file_ext}"

            try:
                # ✅ Upload to S3
                s3.upload_fileobj(file, S3_BUCKET, filename)

                # ✅ Read back from S3 for Textract
                s3_object = s3.get_object(Bucket=S3_BUCKET, Key=filename)
                image_bytes = s3_object['Body'].read()

                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_image_path = os.path.join(tmpdir, filename)
                    with open(tmp_image_path, "wb") as f:
                        f.write(image_bytes)

                    extracted_data = extract_receipt_data(tmp_image_path)

                if not extracted_data:
                    return "❌ Could not extract data from receipt", 400

                classification = classify_transaction(extracted_data[0])

                receipt_id = filename.split('.')[0]
                user = session['user']['sub'] # Using the user's unique ID from Cognito
                date = extracted_data[0].get('date')
                category = classification.get('category')

                total_str = extracted_data[0].get('total', '0')
                total_cleaned = re.sub(r'[^\d.]', '', total_str)
                total = Decimal(total_cleaned) if total_cleaned else Decimal('0')

                items = extracted_data[0].get('items', [])
                for item in items:
                    price_str = item.get('price', '0')
                    price_cleaned = re.sub(r'[^\d.]', '', price_str)
                    item['price'] = Decimal(price_cleaned) if price_cleaned else Decimal('0')


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
                print(f"Error: {e}")
                return f"Error uploading or processing receipt: {e}", 500

            return redirect(url_for('dashboard'))

    return render_template('upload.html')

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']['sub'] # Using the user's unique ID from Cognito
    period = request.args.get('period', '7')  # Default: last 7 days

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
        # ✅ Query DynamoDB by user and date range
        response = table.query(
            IndexName='user-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user').eq(user) &
            boto3.dynamodb.conditions.Key('date').between(
                start_date_str, end_date_str)
        )
        receipts = response.get('Items', [])
    except Exception as e:
        print(f"Error fetching from DynamoDB: {e}")
        try:
            response = table.query(
                IndexName='user-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key(
                    'user').eq(user)
            )
            receipts = response.get('Items', [])
        except Exception as e2:
            print(f"Error fetching by user only: {e2}")
            receipts = []

    # Convert Decimals to strings for JSON serialization
    for receipt in receipts:
        if 'total' in receipt:
            receipt['total'] = str(receipt['total'])
        if 'items' in receipt:
            for item in receipt['items']:
                if 'price' in item:
                    item['price'] = str(item['price'])

    return render_template('dashboard.html', receipts=receipts)

if __name__ == '__main__':
    app.run(debug=True)