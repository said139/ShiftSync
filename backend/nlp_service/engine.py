import json
import os
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

import joblib
from django.conf import settings

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


def preprocess_task_text(text: Any) -> str:
    """Validates and normalizes raw natural language shift task descriptions."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    text = text.strip()
    if not text:
        return ""
    lowered = text.lower()
    for pattern, replacement in CONTRACTIONS.items():
        lowered = re.sub(pattern, replacement, lowered)
    lowered = re.sub(r"[^a-z0-9\s#\-\./]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def infer_task_status_heuristic(text: str) -> str:
    """Infers a suggested task status from verb tense and operational keywords."""
    text_lower = (text or "").lower()
    if any(
        w in text_lower
        for w in [
            "completed",
            "done",
            "finished",
            "cleared",
            "reconciled",
            "signed off",
            "evacuated",
            "rectified",
            "passed",
            "verified",
            "replaced",
        ]
    ):
        return "Completed"
    if any(
        w in text_lower
        for w in [
            "in progress",
            "underway",
            "rebuilding",
            "working on",
            "calibrating",
            "troubleshooting",
            "overhauling",
            "hunting",
            "rigging",
            "ongoing",
        ]
    ):
        return "In Progress"
    return "Pending"


class BaseNLPProvider(ABC):
    """Replaceable interface for ShiftSync NLP task classification providers."""

    provider_name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def predict(self, raw_text: str, cleaned_text: str) -> Dict[str, Any]:
        pass


class HuggingFaceTransformerProvider(BaseNLPProvider):
    """
    Fine-tuned Hugging Face Transformer (`AutoModelForSequenceClassification` + `AutoTokenizer`)
    for Task Categorisation and Priority Detection.
    """

    provider_name = "huggingface_transformer"

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.cat_dir = models_dir / "hf_category_model"
        self.prio_dir = models_dir / "hf_priority_model"
        self.metrics_path = models_dir / "hf_evaluation_metrics.json"
        self._loaded = False
        self._load_error = None
        self.tokenizer_cat = None
        self.model_cat = None
        self.tokenizer_prio = None
        self.model_prio = None

    def _ensure_loaded(self) -> bool:
        if self._loaded:
            return True
        if self._load_error is not None:
            return False
        if not (self.cat_dir.exists() and self.prio_dir.exists()):
            return False
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self.torch = torch
            self.tokenizer_cat = AutoTokenizer.from_pretrained(str(self.cat_dir))
            self.model_cat = AutoModelForSequenceClassification.from_pretrained(
                str(self.cat_dir)
            )
            self.model_cat.eval()

            self.tokenizer_prio = AutoTokenizer.from_pretrained(str(self.prio_dir))
            self.model_prio = AutoModelForSequenceClassification.from_pretrained(
                str(self.prio_dir)
            )
            self.model_prio.eval()
            self._loaded = True
            return True
        except Exception as exc:
            self._load_error = str(exc)
            return False

    def is_available(self) -> bool:
        return self._ensure_loaded()

    def predict(self, raw_text: str, cleaned_text: str) -> Dict[str, Any]:
        if not self._ensure_loaded():
            raise RuntimeError(
                f"Hugging Face Transformer model is not available: {self._load_error or 'models not found'}"
            )
        torch = self.torch
        with torch.no_grad():
            cat_inputs = self.tokenizer_cat(
                cleaned_text,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding=True,
            )
            cat_logits = self.model_cat(**cat_inputs).logits
            cat_probs = torch.softmax(cat_logits, dim=-1)[0].tolist()
            cat_idx = int(torch.argmax(cat_logits, dim=-1).item())
            cat_label = self.model_cat.config.id2label.get(
                cat_idx, self.model_cat.config.id2label.get(str(cat_idx), "Operations")
            )
            cat_conf = round(float(cat_probs[cat_idx]) * 100.0, 1)

            prio_inputs = self.tokenizer_prio(
                cleaned_text,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding=True,
            )
            prio_logits = self.model_prio(**prio_inputs).logits
            prio_probs = torch.softmax(prio_logits, dim=-1)[0].tolist()
            prio_idx = int(torch.argmax(prio_logits, dim=-1).item())
            prio_label = self.model_prio.config.id2label.get(
                prio_idx, self.model_prio.config.id2label.get(str(prio_idx), "Medium")
            )
            prio_conf = round(float(prio_probs[prio_idx]) * 100.0, 1)

        return {
            "category": cat_label,
            "category_confidence": cat_conf,
            "priority": prio_label,
            "priority_confidence": prio_conf,
            "provider": self.provider_name,
        }


class ScikitLearnPipelineProvider(BaseNLPProvider):
    """
    Calibrated Scikit-Learn TF-IDF + Balanced LogisticRegression classifier
    trained on the deduplicated ShiftSync dataset (`models/*.joblib`).
    """

    provider_name = "sklearn_calibrated_pipeline"

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self._loaded = False
        self._load_error = None
        self.cat_pipeline = None
        self.prio_pipeline = None

    def _ensure_loaded(self) -> bool:
        if self._loaded:
            return True
        if self._load_error is not None:
            return False
        cat_path = self.models_dir / "category_pipeline.joblib"
        prio_path = self.models_dir / "priority_pipeline.joblib"
        if not (cat_path.exists() and prio_path.exists()):
            return False
        try:
            self.cat_pipeline = joblib.load(str(cat_path))
            self.prio_pipeline = joblib.load(str(prio_path))
            self._loaded = True
            return True
        except Exception as exc:
            self._load_error = str(exc)
            return False

    def is_available(self) -> bool:
        return self._ensure_loaded()

    def predict(self, raw_text: str, cleaned_text: str) -> Dict[str, Any]:
        if not self._ensure_loaded():
            raise RuntimeError(
                f"Scikit-Learn pipeline is not available: {self._load_error or 'models not found'}"
            )
        cat_label = str(self.cat_pipeline.predict([cleaned_text])[0])
        cat_probs = self.cat_pipeline.predict_proba([cleaned_text])[0]
        cat_conf = round(float(max(cat_probs)) * 100.0, 1)

        prio_label = str(self.prio_pipeline.predict([cleaned_text])[0])
        prio_probs = self.prio_pipeline.predict_proba([cleaned_text])[0]
        prio_conf = round(float(max(prio_probs)) * 100.0, 1)

        return {
            "category": cat_label,
            "category_confidence": cat_conf,
            "priority": prio_label,
            "priority_confidence": prio_conf,
            "provider": self.provider_name,
        }


class ShiftSyncNLPService:
    """
    Unified NLP orchestration service with replaceable providers, low-confidence
    detection, and graceful degradation when models are unavailable.
    """

    def __init__(self, models_dir: Path = None, force_provider: str = None):
        self.models_dir = Path(models_dir or getattr(settings, "NLP_MODELS_DIR", "models"))
        self.force_provider = force_provider
        self.hf_provider = HuggingFaceTransformerProvider(self.models_dir)
        self.sklearn_provider = ScikitLearnPipelineProvider(self.models_dir)

    def get_active_provider(self, requested_provider: str = None):
        mode = (
            requested_provider
            or self.force_provider
            or getattr(settings, "NLP_PROVIDER", "auto")
        ).lower()

        if mode == "unavailable" or mode == "disabled":
            return None
        if mode == "huggingface" or mode == "transformer":
            return self.hf_provider if self.hf_provider.is_available() else None
        if mode == "sklearn" or mode == "baseline":
            return self.sklearn_provider if self.sklearn_provider.is_available() else None

        # Default "auto": prefer fine-tuned Hugging Face Transformer, fall back to Scikit-Learn pipeline
        if self.hf_provider.is_available():
            return self.hf_provider
        if self.sklearn_provider.is_available():
            return self.sklearn_provider
        return None

    def classify_task(
        self,
        description: Any,
        low_confidence_threshold: float = None,
        requested_provider: str = None,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        threshold = (
            low_confidence_threshold
            if low_confidence_threshold is not None
            else float(getattr(settings, "NLP_LOW_CONFIDENCE_THRESHOLD", 60.0))
        )

        if not isinstance(description, str) or not description.strip():
            raise ValueError("Task description cannot be empty.")

        cleaned = preprocess_task_text(description)
        if len(cleaned) < 3:
            raise ValueError(
                "Task description must contain meaningful text (at least 3 alphanumeric characters)."
            )

        provider = self.get_active_provider(requested_provider=requested_provider)
        suggested_status = infer_task_status_heuristic(description)

        if provider is None:
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return {
                "available": False,
                "task": description.strip(),
                "cleaned_text": cleaned,
                "category": "Operations",
                "priority": "Medium",
                "suggested_status": suggested_status,
                "category_confidence": 0.0,
                "priority_confidence": 0.0,
                "confidence_score": 0.0,
                "is_low_confidence": True,
                "provider": "manual_fallback",
                "latency_ms": elapsed_ms,
                "warning": (
                    "Automated NLP classification is currently unavailable. "
                    "Default values have been selected — please choose the appropriate "
                    "task category and priority manually."
                ),
            }

        try:
            pred = provider.predict(description, cleaned)
            cat_conf = float(pred["category_confidence"])
            prio_conf = float(pred["priority_confidence"])
            combined_conf = round((cat_conf + prio_conf) / 2.0, 1)

            # Flag very short or ambiguous inputs as low confidence
            word_count = len(cleaned.split())
            if word_count < 3:
                cat_conf = min(cat_conf, 48.0)
                prio_conf = min(prio_conf, 48.0)
                combined_conf = round((cat_conf + prio_conf) / 2.0, 1)

            is_low_conf = (
                cat_conf < threshold
                or prio_conf < threshold
                or combined_conf < threshold
            )
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            warning = None
            if is_low_conf:
                warning = (
                    f"Low model confidence ({combined_conf}%). Please review and confirm "
                    f"the suggested category and priority before saving."
                )

            return {
                "available": True,
                "task": description.strip(),
                "cleaned_text": cleaned,
                "category": pred["category"],
                "priority": pred["priority"],
                "suggested_status": suggested_status,
                "category_confidence": cat_conf,
                "priority_confidence": prio_conf,
                "confidence_score": combined_conf,
                "is_low_confidence": is_low_conf,
                "provider": pred["provider"],
                "latency_ms": elapsed_ms,
                "warning": warning,
            }
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return {
                "available": False,
                "task": description.strip(),
                "cleaned_text": cleaned,
                "category": "Operations",
                "priority": "Medium",
                "suggested_status": suggested_status,
                "category_confidence": 0.0,
                "priority_confidence": 0.0,
                "confidence_score": 0.0,
                "is_low_confidence": True,
                "provider": "manual_fallback",
                "latency_ms": elapsed_ms,
                "warning": (
                    f"NLP inference encountered an error ({exc}). "
                    "Please select the task category and priority manually."
                ),
            }

    def analyze_shift_narrative(
        self, shift_notes: str, low_confidence_threshold: float = None
    ) -> Dict[str, Any]:
        """Segments a multi-task shift log narrative into discrete tasks and classifies each."""
        if not isinstance(shift_notes, str) or not shift_notes.strip():
            raise ValueError("Shift narrative text cannot be empty.")

        raw_segments = re.split(
            r",\s*(?:and\s+)?|\band\s+|\.\s+|\n+|;\s*|(?<=\d\.)\s+|(?<=[•\-\*])\s+",
            shift_notes,
        )
        segments = [
            s.strip().lstrip("0123456789.-•*() ")
            for s in raw_segments
            if len(s.strip()) >= 6
        ]
        if not segments and len(shift_notes.strip()) >= 5:
            segments = [shift_notes.strip()]

        results: List[Dict[str, Any]] = []
        for seg in segments:
            results.append(
                self.classify_task(seg, low_confidence_threshold=low_confidence_threshold)
            )

        return {
            "input_notes": shift_notes,
            "tasks_detected_count": len(results),
            "tasks": results,
        }

    def get_status_metadata(self) -> Dict[str, Any]:
        hf_avail = self.hf_provider.is_available()
        sk_avail = self.sklearn_provider.is_available()
        active = self.get_active_provider()
        metrics = {}
        metrics_file = self.models_dir / "hf_evaluation_metrics.json"
        if metrics_file.exists():
            try:
                metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
            except Exception:
                metrics = {}
        return {
            "active_provider": active.provider_name if active else "manual_fallback",
            "huggingface_transformer_available": hf_avail,
            "sklearn_baseline_available": sk_avail,
            "low_confidence_threshold": float(
                getattr(settings, "NLP_LOW_CONFIDENCE_THRESHOLD", 60.0)
            ),
            "evaluation_metrics": metrics,
        }


# Singleton service instance
nlp_service_singleton = ShiftSyncNLPService()
