import json
import re
import boto3

# ---- Configuration ----
REGION = "us-east-1"
MODEL_ID = "amazon.titan-text-express-v1"

# Connect to Bedrock runtime
bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def classify_transaction(transaction):
    vendor = transaction.get("vendor", "")
    items = ", ".join([i.get("description", "")
                      for i in transaction.get("items", [])])
    total = transaction.get("total", "0")

    categories = ["Retail", "Groceries", "Restaurant",
                  "Cafe", "Public Transport", "Hotel", "Miscellaneous"]

    prompt = f"""
You are a transaction classifier. 
Choose ONE category that best fits the purchase details from the following list:
{categories}

Return only JSON in this exact format:
{{"predicted_category": "<chosen_category>"}}

If unsure, choose "Miscellaneous".
Transaction details:
Vendor: {vendor}
Items: {items}
Total: {total}
    """

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 150,
                "temperature": 0.2,
                "topP": 0.9
            }
        })
    )

    model_output = json.loads(response["body"].read())
    text_output = model_output["results"][0]["outputText"].strip()

    # Try to extract valid JSON if present
    match = re.search(r'\{.*\}', text_output, re.DOTALL)
    if match:
        text_output = match.group(0)

    # Try JSON parsing first
    try:
        result = json.loads(text_output)
        return result.get("predicted_category", "Unknown")
    except Exception:
        # If not JSON, maybe it’s just plain text like “Retail”
        cleaned = text_output.strip().strip('"')
        for cat in categories:
            if cat.lower() in cleaned.lower():
                return cat
        print("⚠️ Model output not valid JSON:", text_output)
        return "Unknown"


# ---- Main workflow ----
if __name__ == "__main__":
    with open("receipt_data.json", "r") as f:
        receipts = json.load(f)

    results = []
    for tx in receipts:
        category = classify_transaction(tx)
        results.append({"predicted_category": category})

    with open("classified_receipts.json", "w") as f:
        json.dump(results, f, indent=2)

    print("✅ Classification complete! Saved as classified_receipts.json")
