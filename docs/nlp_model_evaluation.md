# ShiftSync NLP Service & Transformer Model Evaluation Report

## 1. Architecture & Academic Alignment

The ShiftSync NLP service (`backend/nlp_service/`) implements automated **Task Categorisation** and **Priority Detection** with a modular, replaceable provider architecture:

1. **Primary Provider (`HuggingFaceTransformerProvider`)**:
   - Pre-trained Transformer backbone: `prajjwal1/bert-tiny` (`BertForSequenceClassification`, 2-layer Transformer encoder) paired with `AutoTokenizer` (`google-bert/bert-base-uncased`).
   - Fine-tuned on the deduplicated ShiftSync dataset (`data/shiftsync_handover_nlp_dataset_deduplicated.csv`, **506 unique shift task descriptions**) using a strict, leak-free **70% Train (354) / 15% Validation (76) / 15% Unseen Test (76)** stratified split.
   - Serialized reproducibly via `save_pretrained()` to `models/hf_category_model/` and `models/hf_priority_model/`.
2. **Secondary Fallback Provider (`ScikitLearnPipelineProvider`)**:
   - Calibrated TF-IDF (`ngram_range=(1, 2)`) + Balanced Multi-Class Logistic Regression pipeline (`models/category_pipeline.joblib` and `models/priority_pipeline.joblib`) trained on the same dataset partition.
3. **Graceful Offline / Unavailable Fallback (`manual_fallback`)**:
   - If models are disabled or unavailable, `ShiftSyncNLPService` returns `available: false` with a clear warning banner so workers can always categorise and prioritise tasks manually without blocking handover operations.

---

## 2. Unseen Test Set Evaluation Results (0% Data Leakage)

Evaluated on the **76 unseen Test set records** (`models/hf_evaluation_metrics.json`):

### 2.1 Fine-Tuned Hugging Face Transformer (`prajjwal1/bert-tiny`) — Task Categorisation

| Category | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Administration** | 1.0000 | 1.0000 | 1.0000 | 10 |
| **Equipment Check** | 1.0000 | 0.9444 | 0.9714 | 18 |
| **Maintenance** | 0.9500 | 1.0000 | 0.9744 | 19 |
| **Operations** | 0.9286 | 1.0000 | 0.9630 | 13 |
| **Safety & Compliance** | 1.0000 | 0.9375 | 0.9677 | 16 |
| **Unseen Test Accuracy** | — | — | **97.37%** | **76** |
| **Macro Average** | **0.9757** | **0.9764** | **0.9753** | **76** |

### 2.2 Fine-Tuned Hugging Face Transformer (`prajjwal1/bert-tiny`) — Priority Detection

| Priority Level | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Critical** | 1.0000 | 1.0000 | 1.0000 | 12 |
| **High** | 0.9231 | 0.9600 | 0.9412 | 25 |
| **Medium** | 0.9643 | 0.9310 | 0.9474 | 29 |
| **Low** | 1.0000 | 1.0000 | 1.0000 | 10 |
| **Unseen Test Accuracy** | — | — | **96.05%** | **76** |
| **Macro Average** | **0.9718** | **0.9728** | **0.9721** | **76** |

---

## 3. Low-Confidence Handling & Worker Override Provenance

- Predictions below the organisation's configurable threshold (default `60.0%`) or generated from very short/ambiguous inputs (`< 3 words`) set `is_low_confidence: true` and display an explicit warning banner in the UI.
- Every `Task` record in PostgreSQL stores both the model's initial suggestion (`model_suggested_category`, `model_suggested_priority`, `confidence_score`) and the worker's final decision (`confirmed_category`, `confirmed_priority`, `was_overridden`), ensuring human-in-the-loop accountability.
