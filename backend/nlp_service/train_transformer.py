import json
import os
import re
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BertConfig,
    BertForSequenceClassification,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data"
MODELS_DIR = REPO_ROOT / "models"
DOCS_DIR = REPO_ROOT / "docs"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

PRETRAINED_MODEL_NAME = "prajjwal1/bert-tiny"
PRETRAINED_TOKENIZER_NAME = "google-bert/bert-base-uncased"

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
    r"\bthat's\b": "that is",
}


def clean_text(text):
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    text = text.lower()
    for pattern, replacement in CONTRACTIONS.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"[^a-z0-9\s#\-\./]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class TextClassificationDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=96):
        self.encodings = tokenizer(
            list(texts),
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="pt",
        )
        self.labels = torch.tensor(list(labels), dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item


def fine_tune_transformer_task(
    task_name: str,
    X_train,
    y_train_str,
    X_val,
    y_val_str,
    X_test,
    y_test_str,
    save_dir: Path,
    epochs: int = 22,
    batch_size: int = 16,
    lr: float = 2.5e-4,
):
    torch.manual_seed(42)
    np.random.seed(42)

    classes = sorted(list(set(y_train_str)))
    label2id = {label: i for i, label in enumerate(classes)}
    id2label = {i: label for i, label in enumerate(classes)}

    y_train = [label2id[c] for c in y_train_str]
    y_val = [label2id[c] for c in y_val_str]
    y_test = [label2id[c] for c in y_test_str]

    print(f"\n[{task_name}] Loading pre-trained transformer: {PRETRAINED_MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_TOKENIZER_NAME)
    config = BertConfig.from_pretrained(
        PRETRAINED_MODEL_NAME,
        num_labels=len(classes),
        id2label=id2label,
        label2id=label2id,
    )
    model = BertForSequenceClassification.from_pretrained(
        PRETRAINED_MODEL_NAME,
        config=config,
    )

    train_dataset = TextClassificationDataset(X_train, y_train, tokenizer)
    val_dataset = TextClassificationDataset(X_val, y_val, tokenizer)
    test_dataset = TextClassificationDataset(X_test, y_test, tokenizer)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # Compute balanced class weights to handle class distribution
    counts = np.bincount(y_train, minlength=len(classes)).astype(np.float32)
    weights = len(y_train) / (len(classes) * np.maximum(counts, 1.0))
    criterion = torch.nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float))

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)

    best_val_f1 = -1.0
    best_state = None

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            labels = batch.pop("labels")
            outputs = model(**batch)
            loss = criterion(outputs.logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())

        model.eval()
        val_preds, val_targets = [], []
        with torch.no_grad():
            for batch in val_loader:
                labels = batch.pop("labels")
                logits = model(**batch).logits
                preds = torch.argmax(logits, dim=-1)
                val_preds.extend(preds.tolist())
                val_targets.extend(labels.tolist())

        val_f1 = f1_score(val_targets, val_preds, average="macro", zero_division=0)
        val_acc = accuracy_score(val_targets, val_preds)
        if val_f1 >= best_val_f1:
            best_val_f1 = val_f1
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if epoch in (1, epochs // 2, epochs):
            print(
                f"  Epoch {epoch:02d}/{epochs:02d} | Train Loss: {total_loss / len(train_loader):.4f} "
                f"| Val Acc: {val_acc * 100:.2f}% | Val Macro-F1: {val_f1:.4f}"
            )

    if best_state is not None:
        model.load_state_dict(best_state)

    save_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(save_dir))
    tokenizer.save_pretrained(str(save_dir))
    print(f"  Saved fine-tuned model & tokenizer to: {save_dir}")

    # Evaluate on unseen Test set
    model.eval()
    test_preds_idx = []
    with torch.no_grad():
        for batch in test_loader:
            batch.pop("labels")
            logits = model(**batch).logits
            preds = torch.argmax(logits, dim=-1)
            test_preds_idx.extend(preds.tolist())

    test_preds_str = [id2label[idx] for idx in test_preds_idx]
    test_acc = accuracy_score(y_test_str, test_preds_str)
    report_dict = classification_report(
        y_test_str, test_preds_str, output_dict=True, zero_division=0
    )
    report_str = classification_report(
        y_test_str, test_preds_str, digits=4, zero_division=0
    )
    print(f"\n[{task_name}] Unseen Test Set Accuracy: {test_acc * 100:.2f}%")
    print(report_str)

    return {
        "classes": classes,
        "test_accuracy": round(float(test_acc), 4),
        "val_best_macro_f1": round(float(best_val_f1), 4),
        "classification_report": report_dict,
    }


def main():
    t0 = time.time()
    dataset_path = DATA_DIR / "shiftsync_handover_nlp_dataset_deduplicated.csv"
    if not dataset_path.exists():
        dataset_path = DATA_DIR / "shiftsync_handover_nlp_dataset.csv"

    print("=" * 80)
    print("ShiftSync NLP: Hugging Face Transformer Fine-Tuning & Baseline Evaluation")
    print("=" * 80)
    df = pd.read_csv(dataset_path)
    df = df.dropna(subset=["task_description", "category", "priority"])
    df = df.drop_duplicates(subset=["task_description"]).reset_index(drop=True)
    df["clean_text"] = df["task_description"].apply(clean_text)

    print(f"Loaded {len(df)} deduplicated shift task records (0% duplicate leakage).")

    # Strict 70% Train / 15% Validation / 15% Test Stratified Split
    X = df["clean_text"].values
    y_cat = df["category"].values
    y_prio = df["priority"].values

    X_train, X_temp, y_cat_train, y_cat_temp, y_prio_train, y_prio_temp = (
        train_test_split(
            X, y_cat, y_prio, test_size=0.30, random_state=42, stratify=y_cat
        )
    )
    X_val, X_test, y_cat_val, y_cat_test, y_prio_val, y_prio_test = train_test_split(
        X_temp,
        y_cat_temp,
        y_prio_temp,
        test_size=0.50,
        random_state=42,
        stratify=y_cat_temp,
    )

    print(
        f"Partition sizes -> Train: {len(X_train)} | Validation: {len(X_val)} | Unseen Test: {len(X_test)}"
    )

    # 1. Fine-Tune Hugging Face Transformer Models
    hf_cat_metrics = fine_tune_transformer_task(
        task_name="HuggingFace Transformer - Task Categorisation",
        X_train=X_train,
        y_train_str=y_cat_train,
        X_val=X_val,
        y_val_str=y_cat_val,
        X_test=X_test,
        y_test_str=y_cat_test,
        save_dir=MODELS_DIR / "hf_category_model",
        epochs=22,
    )

    hf_prio_metrics = fine_tune_transformer_task(
        task_name="HuggingFace Transformer - Priority Detection",
        X_train=X_train,
        y_train_str=y_prio_train,
        X_val=X_val,
        y_val_str=y_prio_val,
        X_test=X_test,
        y_test_str=y_prio_test,
        save_dir=MODELS_DIR / "hf_priority_model",
        epochs=22,
    )

    # 2. Train & Evaluate Calibrated Scikit-Learn Pipeline on the exact same split
    cat_pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(ngram_range=(1, 2), max_features=3500, sublinear_tf=True),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=2.0, max_iter=1000, class_weight="balanced", random_state=42
                ),
            ),
        ]
    )
    cat_pipeline.fit(np.concatenate([X_train, X_val]), np.concatenate([y_cat_train, y_cat_val]))
    sk_cat_preds = cat_pipeline.predict(X_test)
    sk_cat_acc = accuracy_score(y_cat_test, sk_cat_preds)
    sk_cat_report = classification_report(
        y_cat_test, sk_cat_preds, output_dict=True, zero_division=0
    )

    prio_pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(ngram_range=(1, 2), max_features=3500, sublinear_tf=True),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=2.0, max_iter=1000, class_weight="balanced", random_state=42
                ),
            ),
        ]
    )
    prio_pipeline.fit(
        np.concatenate([X_train, X_val]), np.concatenate([y_prio_train, y_prio_val])
    )
    sk_prio_preds = prio_pipeline.predict(X_test)
    sk_prio_acc = accuracy_score(y_prio_test, sk_prio_preds)
    sk_prio_report = classification_report(
        y_prio_test, sk_prio_preds, output_dict=True, zero_division=0
    )

    joblib.dump(cat_pipeline, MODELS_DIR / "category_pipeline.joblib")
    joblib.dump(prio_pipeline, MODELS_DIR / "priority_pipeline.joblib")
    joblib.dump(cat_pipeline.named_steps["tfidf"], MODELS_DIR / "vectorizer.joblib")
    joblib.dump(
        cat_pipeline.named_steps["classifier"], MODELS_DIR / "category_model.joblib"
    )
    joblib.dump(
        prio_pipeline.named_steps["classifier"], MODELS_DIR / "priority_model.joblib"
    )

    elapsed = round(time.time() - t0, 2)
    metrics_payload = {
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_records": int(len(df)),
        "split_sizes": {
            "train": int(len(X_train)),
            "validation": int(len(X_val)),
            "test": int(len(X_test)),
        },
        "pretrained_backbone": PRETRAINED_MODEL_NAME,
        "training_duration_seconds": elapsed,
        "huggingface_transformer": {
            "category": hf_cat_metrics,
            "priority": hf_prio_metrics,
        },
        "sklearn_baseline": {
            "category": {
                "test_accuracy": round(float(sk_cat_acc), 4),
                "classification_report": sk_cat_report,
            },
            "priority": {
                "test_accuracy": round(float(sk_prio_acc), 4),
                "classification_report": sk_prio_report,
            },
        },
    }

    metrics_file = MODELS_DIR / "hf_evaluation_metrics.json"
    metrics_file.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")
    print(f"\nSaved comprehensive evaluation metrics JSON to: {metrics_file}")


if __name__ == "__main__":
    main()
