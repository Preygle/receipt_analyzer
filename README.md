# Serverless Smart Receipt Analyzer & Expense Categorizer

## � Project Documentation
This repository contains the source code and detailed documentation for the Smart Receipt Analyzer. Please refer to the specific guides below for in-depth configuration and setup details:

### 🔹 [1. System Architecture & Network](docs/architecture.md)
*   Hybrid Cloud Design Flow
*   VPC Configuration (Subnets, Route Tables)
*   Security Setup (IAM Roles, Security Groups)

### 🔹 [2. Compute Setup (EC2)](docs/ec2_setup.md)
*   Instance provisioning parameters (t2.micro, AMI)
*   **Systemd Service** configuration for persistence
*   Environment setup and dependencies

### 🔹 [3. Data Storage (S3 & DynamoDB)](docs/data_storage.md)
*   S3 Bucket security and Pre-signed URL workflow
*   DynamoDB Table Schema and GSI Indexing for performance

### 🔹 [4. AI Services (Textract & Bedrock)](docs/ai_integration.md)
*   OCR workflow using Amazon Textract `AnalyzeExpense`
*   Generative AI Classification prompt engineering with Claude 3 (Bedrock)

### 🔹 [5. Notifications (SNS + Lambda)](docs/notifications_setup.md)
*   Daily account summary architecture
*   Setup guide for EventBridge Cron, Lambda, and Email alerts

---

## �📜 Project Abstract
The **Smart Receipt Analyzer** is a cloud-native web application designed to automate the expense tracking lifecycle. Hosted on a hybrid AWS architecture, it leverages **Amazon EC2** for the web interface and serverless AI services for backend processing.

Users upload receipt images via a mobile-friendly Flask web app. The system automatically:
1.  **Extracts Data**: Uses **Amazon Textract** (OCR) to read vendor names, dates, and totals.
2.  **Categorizes Expenses**: Uses **Amazon Bedrock** (LLM) to intelligently classify transactions (e.g., "Groceries", "Dining").
3.  **Stores Securely**: Saves images in a private **Amazon S3** bucket and metadata in **Amazon DynamoDB**.

## 🚀 Quick Start
To run this project locally or deploy it, please refer to the [Compute Setup Guide](docs/ec2_setup.md) for detailed installation instructions.

### Environment Config
Create a `.env` file with the following:
```bash
AWS_REGION=us-east-1
S3_BUCKET=your-bucket
DYNAMODB_TABLE=your-table
FLASK_SECRET_KEY=secret
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229
```

---

