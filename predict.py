import os
import re
import json
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s#\-\.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

class ShiftSyncNLP:
    def __init__(self):
        vec_path = os.path.join(MODELS_DIR, "vectorizer.joblib")
        cat_path = os.path.join(MODELS_DIR, "category_model.joblib")
        prio_path = os.path.join(MODELS_DIR, "priority_model.joblib")

        if not (os.path.exists(vec_path) and os.path.exists(cat_path) and os.path.exists(prio_path)):
            raise FileNotFoundError("Models not trained yet. Run train_model.py first.")

        self.vectorizer = joblib.load(vec_path)
        self.category_model = joblib.load(cat_path)
        self.priority_model = joblib.load(prio_path)

    def analyze_task(self, text):
        cleaned = clean_text(text)
        vec = self.vectorizer.transform([cleaned])
        
        category = self.category_model.predict(vec)[0]
        priority = self.priority_model.predict(vec)[0]
        
        # Calculate confidence scores if available
        cat_probs = self.category_model.predict_proba(vec)[0]
        prio_probs = self.priority_model.predict_proba(vec)[0]
        
        cat_conf = round(float(max(cat_probs)) * 100, 1)
        prio_conf = round(float(max(prio_probs)) * 100, 1)

        # Heuristic for status based on past vs future wording
        text_lower = text.lower()
        if any(w in text_lower for w in ["completed", "done", "finished", "cleared", "reconciled", "signed off"]):
            status = "Completed"
        elif any(w in text_lower for w in ["in progress", "underway", "rebuilding", "working on", "mixing", "sorting"]):
            status = "In Progress"
        else:
            status = "Pending"

        return {
            "task": text.strip(),
            "category": category,
            "category_confidence": f"{cat_conf}%",
            "priority": priority,
            "priority_confidence": f"{prio_conf}%",
            "status": status
        }

    def analyze_shift_log(self, shift_notes):
        """Splits multi-task sentences (joined by 'and', commas, or periods) and classifies each."""
        # Simple task boundary detection
        raw_tasks = re.split(r",\s*(?:and\s+)?|\band\s+|\.\s+", shift_notes)
        tasks = [t.strip() for t in raw_tasks if len(t.strip()) > 8]

        results = [self.analyze_task(t) for t in tasks]
        return {
            "input_notes": shift_notes,
            "tasks_detected_count": len(results),
            "tasks": results
        }

if __name__ == "__main__":
    nlp = ShiftSyncNLP()
    sample = "Checked boiler pressure on Line 2, replaced faulty sensor on conveyor B, and initiated safety drill log for night crew."
    output = nlp.analyze_shift_log(sample)
    print(json.dumps(output, indent=2))
