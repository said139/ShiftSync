import os
import re
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "shiftsync_handover_nlp_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

print("=" * 70)
print("ShiftSync NLP: Automated Task Categorisation & Priority Detection")
print("=" * 70)

# 1. Load Dataset
print(f"Loading dataset from: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
print(f"Total records loaded: {len(df)}")
print(f"Categories distribution:\n{df['category'].value_counts()}\n")
print(f"Priority distribution:\n{df['priority'].value_counts()}\n")

# 2. Text Preprocessing
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s#\-\.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df["clean_description"] = df["task_description"].apply(clean_text)

# 3. Train-Test Split (80% Train, 20% Test)
X_train, X_test, y_cat_train, y_cat_test, y_prio_train, y_prio_test = train_test_split(
    df["clean_description"],
    df["category"],
    df["priority"],
    test_size=0.20,
    random_state=42,
    stratify=df["category"]
)

# 4. Feature Extraction: TF-IDF Vectorizer
print("\nFitting TF-IDF Vectorizer...")
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=3000, sublinear_tf=True)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# 5. Model 1: Task Categorisation
print("\n" + "-" * 50)
print("Training Model 1: Task Categorisation (Multi-class Logistic Regression)")
print("-" * 50)
cat_model = LogisticRegression(max_iter=1000, C=1.5, class_weight="balanced")
cat_model.fit(X_train_vec, y_cat_train)
cat_preds = cat_model.predict(X_test_vec)

print(f"Categorisation Accuracy: {accuracy_score(y_cat_test, cat_preds) * 100:.2f}%\n")
print("Classification Report (Categorisation):")
print(classification_report(y_cat_test, cat_preds, digits=4))

# 6. Model 2: Priority Detection
print("\n" + "-" * 50)
print("Training Model 2: Priority Detection (Multi-class Logistic Regression)")
print("-" * 50)
prio_model = LogisticRegression(max_iter=1000, C=1.5, class_weight="balanced")
prio_model.fit(X_train_vec, y_prio_train)
prio_preds = prio_model.predict(X_test_vec)

print(f"Priority Detection Accuracy: {accuracy_score(y_prio_test, prio_preds) * 100:.2f}%\n")
print("Classification Report (Priority Detection):")
print(classification_report(y_prio_test, prio_preds, digits=4))

# 7. Save Models and Vectorizer
print("\nSaving trained models to disk...")
joblib.dump(vectorizer, os.path.join(MODELS_DIR, "vectorizer.joblib"))
joblib.dump(cat_model, os.path.join(MODELS_DIR, "category_model.joblib"))
joblib.dump(prio_model, os.path.join(MODELS_DIR, "priority_model.joblib"))
print("All models successfully saved in /models directory.")

# 8. Test on the exact prompt from your UI Wireframe (Fig 02_shiftsync_nlp_shift_log.jpg)!
print("\n" + "=" * 70)
print("TEST RUN: Real-world Shift Log Inference (From UI Wireframe)")
print("=" * 70)

test_samples = [
    "Checked boiler pressure on Line 2, fluctuating readings observed.",
    "Replaced faulty sensor on conveyor B after tracking failure.",
    "Initiated safety drill log for night crew and checked emergency exits.",
    "Major chemical spill reported in Warehouse Sector B, evacuated personnel.",
    "Completed routine inventory reconciliation in bin rack R-44.",
    "Updated shift logbook Section 4 and handed over keys to incoming lead."
]

for sample in test_samples:
    cleaned = clean_text(sample)
    vec = vectorizer.transform([cleaned])
    pred_cat = cat_model.predict(vec)[0]
    pred_prio = prio_model.predict(vec)[0]
    print(f"Input : \"{sample}\"")
    print(f" -> Predicted Category : [{pred_cat}]")
    print(f" -> Predicted Priority : [{pred_prio}]")
    print("-" * 70)
