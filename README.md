## Receipt Analyzer - AWS Configuration Notes

Update your AWS resources to match the application settings. Replace placeholders in environment variables with your actual values.

### Required environment variables

Create a `.env` with the following keys (examples shown):

```
AWS_REGION=us-east-1
S3_BUCKET=your-receipts-bucket-name
DYNAMODB_TABLE=your-dynamodb-table-name

COGNITO_USER_POOL_ID=us-east-1_example
COGNITO_CLIENT_ID=your-client-id
COGNITO_CLIENT_SECRET=your-client-secret
COGNITO_DOMAIN=https://your-domain.auth.us-east-1.amazoncognito.com
COGNITO_REDIRECT_URI=http://127.0.0.1:5000/authorize
COGNITO_LOGOUT_REDIRECT_URI=http://127.0.0.1:5000/

FLASK_SECRET_KEY=dev-secret
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229
```

### Cognito Hosted UI setup
1. In Amazon Cognito → User Pools → Your Pool → App client settings:
   - Allowed callback URLs: include `http://127.0.0.1:5000/authorize` and/or your deployed domain `https://YOUR_DOMAIN/authorize`.
   - Allowed sign-out URLs: include `http://127.0.0.1:5000/` and/or your deployed domain root.
   - Enable OAuth flows used by the app (Authorization code) and scopes: `openid`, `email`, `phone`.
2. In Domain name, set the Hosted UI domain and ensure it matches `COGNITO_DOMAIN`.

### S3
- Create bucket named by `S3_BUCKET` in `AWS_REGION`.
- Objects are stored under prefix `user/{sub}/receipts/{filename}`. Ensure IAM allows `s3:PutObject`, `s3:GetObject`, and `s3:ListBucket` for the bucket and `/*`.

### DynamoDB
- Table name must match `DYNAMODB_TABLE`.
- Attributes saved: `receipt_id` (PK if using simple table), `user`, `date`, `category`, `total`, `items`.
- The app queries `IndexName='user-index'` on partition key `user` and (optionally) sort key `date`. Create a GSI named `user-index` with `user` as partition key and `date` as sort key (String/String).

### Bedrock and Textract permissions
Attach these permissions to the role running Flask (expand with your ARNs):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::your-receipts-bucket-name",
        "arn:aws:s3:::your-receipts-bucket-name/*"
      ]
    },
    {
      "Sid": "DynamoAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:YOUR_ACCOUNT_ID:table/your-dynamodb-table-name"
    },
    {
      "Sid": "TextractAccess",
      "Effect": "Allow",
      "Action": [
        "textract:AnalyzeDocument",
        "textract:StartDocumentAnalysis",
        "textract:GetDocumentAnalysis"
      ],
      "Resource": "*"
    },
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "*"
    }
  ]
}
```


