import os
import tempfile
import re
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
import boto3
from datetime import datetime, timedelta
import json
from decimal import Decimal
from extract_receipt import extract_receipt_data
from classifier import classify_transaction
from dotenv import load_dotenv

load_dotenv()

"""
Configuration is centralized via environment variables. Create a .env file locally
and export these values in production.

Required env vars (examples):
  AWS_REGION=us-east-1
  S3_BUCKET=your-receipts-bucket-name  # TODO: replace with your S3 bucket name
  DYNAMODB_TABLE=your-dynamodb-table-name  # TODO: replace with your DynamoDB table
  FLASK_SECRET_KEY=dev-secret
"""

# ------------------- CONFIG -------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# AWS Config
REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "your-receipts-bucket-name")  # TODO: set your bucket
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "your-dynamodb-table-name")  # TODO: set your table

# Initialize AWS clients
s3 = boto3.client("s3", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

# ------------------------------------------------


@app.route('/test_dynamo')
def test_dynamo():
    try:
        response = table.scan(Limit=1)
        return jsonify({"status": "success", "count": len(response.get('Items', []))})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        logging.info("--- Upload request received ---")
        if 'receipt' not in request.files:
            logging.warning("No file part in request")
            return redirect(request.url)
        file = request.files['receipt']
        if file.filename == '':
            logging.warning("No selected file")
            return redirect(request.url)
        if file:
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            logging.info(f"File received: {file.filename}")
            if file_ext not in ['jpg', 'jpeg', 'png', 'pdf']:
                logging.warning(f"Unsupported file format: {file_ext}")
                return "❌ Unsupported file format. Please upload a JPG, PNG, or PDF.", 400

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"receipt_{timestamp}.{file_ext}"

            try:
                # ✅ Upload to S3
                s3_key = f"receipts/{filename}"
                logging.info(f"Uploading to S3 bucket '{S3_BUCKET}' with key '{s3_key}'")
                s3.upload_fileobj(file, S3_BUCKET, s3_key)
                logging.info("S3 upload successful")

                # ✅ Read back from S3 for Textract
                logging.info("Reading file back from S3 for processing")
                s3_object = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
                image_bytes = s3_object['Body'].read()

                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_image_path = os.path.join(tmpdir, filename)
                    with open(tmp_image_path, "wb") as f:
                        f.write(image_bytes)

                    logging.info("Starting receipt data extraction with Textract")
                    extracted_data = extract_receipt_data(tmp_image_path)
                    logging.info(f"Extracted data: {json.dumps(extracted_data, indent=2)}")

                if not extracted_data:
                    logging.error("Could not extract data from receipt")
                    return "❌ Could not extract data from receipt", 400

                logging.info("Starting transaction classification with Bedrock")
                classification = classify_transaction(extracted_data[0])
                logging.info(f"Classification result: {json.dumps(classification, indent=2)}")

                receipt_id = filename.split('.')[0]
                user = "local_user" # Hardcoded user for local use
                date_str = extracted_data[0].get('date')
                try:
                    date = datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    date = datetime.now().strftime('%Y-%m-%d')

                category = classification.get('category')

                total_str = extracted_data[0].get('total', '0')
                total_cleaned = re.sub(r'[^\d.]', '', total_str)
                total = Decimal(total_cleaned) if total_cleaned else Decimal('0')

                items = extracted_data[0].get('items', [])
                for item in items:
                    price_str = item.get('price', '0')
                    price_cleaned = re.sub(r'[^\d.]', '', price_str)
                    item['price'] = Decimal(price_cleaned) if price_cleaned else Decimal('0')

                item_to_save = {
                    'receipt': receipt_id,
                    'user': user,
                    'date': date,
                    'category': category,
                    'total': total,
                    'items': items,
                    's3_key': s3_key
                }
                logging.info(f"Saving item to DynamoDB: {json.dumps(item_to_save, default=str, indent=2)}")

                table.put_item(Item=item_to_save)
                logging.info("Successfully saved item to DynamoDB")

            except Exception as e:
                logging.error(f"An error occurred: {e}", exc_info=True)
                return f"Error uploading or processing receipt: {e}", 500

            logging.info("--- Upload request finished ---Redirecting to dashboard.")
            return redirect(url_for('dashboard'))

    return render_template('upload.html')

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/receipts')
def api_receipts():
    user = "local_user" # Hardcoded user for local use

    try:
        # ✅ Scan DynamoDB for all receipts by user
        response = table.query(
            IndexName='user-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user').eq(user)
        )
        receipts = response.get('Items', [])
        logging.info(f"Receipts from DynamoDB: {json.dumps(receipts, default=str, indent=2)}")
    except Exception as e:
        print(f"Error fetching from DynamoDB: {e}")
        receipts = []

    # Convert Decimals to strings for JSON serialization and add pre-signed URLs
    for receipt in receipts:
        if 'total' in receipt:
            receipt['total'] = str(receipt['total'])
        if 'items' in receipt:
            for item in receipt['items']:
                if 'price' in item:
                    item['price'] = str(item['price'])
        if 's3_key' in receipt:
            receipt['s3_url'] = s3.generate_presigned_url('get_object',
                                                                  Params={'Bucket': S3_BUCKET,
                                                                          'Key': receipt['s3_key']},
                                                                  ExpiresIn=3600)

    return jsonify(receipts)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
