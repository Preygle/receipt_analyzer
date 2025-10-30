# # train_model.py
# import joblib
# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.naive_bayes import MultinomialNB
# from sklearn.pipeline import Pipeline
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import classification_report, accuracy_score

# # Example labelled data (extend this with real samples)
# texts = [
#     "starbucks coffee latte", "costa cappuccino", "barista espresso",
#     "burger king meal", "dominos pizza order", "olive garden dinner",
#     "hilton hotel stay", "marriott room charge",
#     "zara dress purchase", "nike shoes", "h&m trousers",
#     "walmart grocery milk eggs", "wholefoods fresh produce",
#     "uber trip fare", "ola cab ride", "metro train ticket", "bus fare"
# ]
# labels = [
#     "Cafe", "Cafe", "Cafe",
#     "Restaurant", "Restaurant", "Restaurant",
#     "Hotel", "Hotel",
#     "Retail", "Retail", "Retail",
#     "Groceries", "Groceries",
#     "Public Transport", "Public Transport", "Public Transport", "Public Transport"
# ]

# # Train / Test split
# X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)

# # Pipeline: CountVectorizer + Naive Bayes (small & fast)
# pipeline = Pipeline([
#     ("vect", CountVectorizer(ngram_range=(1,2), min_df=1)),
#     ("clf", MultinomialNB())
# ])

# pipeline.fit(X_train, y_train)

# # Evaluate
# y_pred = pipeline.predict(X_test)
# print("Accuracy:", accuracy_score(y_test, y_pred))
# print(classification_report(y_test, y_pred))

# # Save model
# joblib.dump(pipeline, "expense_classifier.joblib")
# print("Saved model to expense_classifier.joblib")


# train_model.py
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Example labelled data (you can expand this later)
texts = [
    "starbucks coffee latte", "costa cappuccino", "barista espresso",
    "burger king meal", "dominos pizza order", "olive garden dinner",
    "hilton hotel stay", "marriott room charge",
    "zara dress purchase", "nike shoes", "h&m trousers",
    "walmart grocery milk eggs", "wholefoods fresh produce",
    "uber trip fare", "ola cab ride", "metro train ticket", "bus fare"
]
labels = [
    "Cafe", "Cafe", "Cafe",
    "Restaurant", "Restaurant", "Restaurant",
    "Hotel", "Hotel",
    "Retail", "Retail", "Retail",
    "Groceries", "Groceries",
    "Public Transport", "Public Transport", "Public Transport", "Public Transport"
]

# Split data for validation
X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)

# Create a pipeline (text → features → Naive Bayes classifier)
pipeline = Pipeline([
    ("vect", CountVectorizer(ngram_range=(1, 2), min_df=1)),
    ("clf", MultinomialNB())
])

# Train model
pipeline.fit(X_train, y_train)

# Evaluate performance
y_pred = pipeline.predict(X_test)
print("✅ Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Save trained model
joblib.dump(pipeline, "expense_classifier.joblib")
print("💾 Saved model to expense_classifier.joblib")
