# test_ml_categorization.py
import json
from extract_receipt import categorize_expense

example_receipt = {
    "vendor": "Starbucks Coffee",
    "items": [
        {"description": "Latte", "price": "3.75"},
        {"description": "Tax", "price": "0.75"}
    ],
    "total": "4.50"
}

category = categorize_expense(example_receipt["vendor"], example_receipt["items"])
example_receipt["category"] = category

print(json.dumps(example_receipt, indent=2))
