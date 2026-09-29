import os
import re
import json
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

CONTRACTIONS = {
    r"\bwon't\b": "will not",
    r"\bcan't\b": "cannot",
    r"\bdon't\b": "do not",
    r"\bdoesn't\b": "does not",
    r"\bisn't\b": "is not",
    r"\baren't\b": "are not",
    r"\bwasn't\b": "was not",
    r"\bweren't\b": "were not",
    r"\bhaven't\b": "have not",
    r"\bhasn't\b": "has not",
    r"\bhadn't\b": "had not",
    r"\bit's\b": "it is",
    r"\bthat's\b": "that is"
}

def clean_text(text):
    """Normalize and clean operational text."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    text = text.lower()
    for pattern, replacement in CONTRACTIONS.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"[^a-z0-9\s#\-\./]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_text_batch(texts):
    """Batch transformer for Scikit-Learn Pipeline compatibility."""
    return [clean_text(t) for t in texts]

class ShiftSyncNLP:
    """Production NLP Inference Engine utilizing trained Scikit-Learn Pipelines."""
    def __init__(self):
        cat_pipe_path = os.path.join(MODELS_DIR, "category_pipeline.joblib")
        prio_pipe_path = os.path.join(MODELS_DIR, "priority_pipeline.joblib")
        vec_path = os.path.join(MODELS_DIR, "vectorizer.joblib")
        cat_path = os.path.join(MODELS_DIR, "category_model.joblib")
        prio_path = os.path.join(MODELS_DIR, "priority_model.joblib")

        self.use_pipeline = os.path.exists(cat_pipe_path) and os.path.exists(prio_pipe_path)

        if self.use_pipeline:
            self.category_pipeline = joblib.load(cat_pipe_path)
            self.priority_pipeline = joblib.load(prio_pipe_path)
            # Standalone fallbacks for backward compatibility
            self.vectorizer = self.category_pipeline.named_steps.get("tfidf")
            self.category_model = self.category_pipeline.named_steps.get("classifier")
            self.priority_model = self.priority_pipeline.named_steps.get("classifier")
        elif os.path.exists(vec_path) and os.path.exists(cat_path) and os.path.exists(prio_path):
            self.vectorizer = joblib.load(vec_path)
            self.category_model = joblib.load(cat_path)
            self.priority_model = joblib.load(prio_path)
        else:
            raise FileNotFoundError("Trained models not found. Please execute train_model.py first.")

    def analyze_task(self, text):
        """Classify a single operational task into Category and Priority with confidence."""
        if not text or not str(text).strip():
            return {
                "task": "",
                "category": "Operations",
                "category_confidence": "0.0%",
                "priority": "Low",
                "priority_confidence": "0.0%",
                "status": "Pending"
            }

        cleaned = clean_text(text)

        if self.use_pipeline:
            category = self.category_pipeline.predict([cleaned])[0]
            priority = self.priority_pipeline.predict([cleaned])[0]
            cat_probs = self.category_pipeline.predict_proba([cleaned])[0]
            prio_probs = self.priority_pipeline.predict_proba([cleaned])[0]
        else:
            vec = self.vectorizer.transform([cleaned])
            category = self.category_model.predict(vec)[0]
            priority = self.priority_model.predict(vec)[0]
            cat_probs = self.category_model.predict_proba(vec)[0]
            prio_probs = self.priority_model.predict_proba(vec)[0]

        cat_conf = round(float(max(cat_probs)) * 100, 1)
        prio_conf = round(float(max(prio_probs)) * 100, 1)

        # Operational status heuristic based on tense and keywords
        text_lower = text.lower()
        if any(w in text_lower for w in ["completed", "done", "finished", "cleared", "reconciled", "signed off", "evacuated"]):
            status = "Completed"
        elif any(w in text_lower for w in ["in progress", "underway", "rebuilding", "working on", "mixing", "sorting", "calibrating"]):
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
        """Splits composite multi-task log narratives and classifies each discrete item."""
        if not shift_notes or not str(shift_notes).strip():
            return {
                "input_notes": "",
                "tasks_detected_count": 0,
                "tasks": []
            }

        # Multi-task sentence segmentation (handles commas, conjunctions, periods, lists, and linebreaks)
        raw_tasks = re.split(r",\s*(?:and\s+)?|\band\s+|\.\s+|\n+|;\s*|(?<=\d\.)\s+|(?<=[•\-\*])\s+", shift_notes)
        tasks = [t.strip().lstrip("0123456789.-•*() ") for t in raw_tasks if len(t.strip()) > 8]

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
