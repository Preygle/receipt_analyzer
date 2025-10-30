import boto3
import json

# ---------- CONFIGURATION ----------
REGION = "us-east-1"  # Change if needed
MODEL_ID = "anthropic.claude-v2" # Titan Text G1 - Express
# ----------------------------------

# Initialize the Bedrock client
bedrock = boto3.client("bedrock-runtime", region_name=REGION)

def classify_transaction(transaction_data):
    """Classify a transaction into a category using Amazon Bedrock."""

    # Create a prompt for the model
    prompt = f"""Human: Based on the following JSON data from a receipt, please classify this transaction into one of these categories: Restaurant, Groceries, Transportation, Shopping, Utilities, Entertainment, or Other.

    <transaction_data>
    {json.dumps(transaction_data, indent=2)}
    </transaction_data>

    Assistant: The category is:"""

    # Prepare the request body
    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": 100,
        "temperature": 0.1,
        "top_p": 0.9,
    })

    print("🤖 Sending data to Bedrock for classification...")

    # Invoke the model
    response = bedrock.invoke_model(
        body=body,
        modelId=MODEL_ID,
        accept="application/json",
        contentType="application/json",
    )

    # Parse the response
    response_body = json.loads(response.get("body").read())
    completion = response_body.get("completion", "").strip()

    # Extract the category (this is a simple example, you might need more robust parsing)
    category = completion.split("The category is:")[-1].strip()

    return {"category": category}


if __name__ == "__main__":
    # Example usage with a sample receipt
    sample_receipt = [
        {
            "vendor": "THE CORNER STORE",
            "date": "2023-10-26",
            "total": "$12.34",
            "items": [
                {"description": "SANDWICH", "price": "$8.50"},
                {"description": "COFFEE", "price": "$3.84"},
            ],
        }
    ]

    classification = classify_transaction(sample_receipt)

    print(f"✅ Transaction classified as: {classification['category']}")
    print(json.dumps(classification, indent=2))
