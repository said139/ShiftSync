# ShiftSync NLP Machine Learning Pipeline Evaluation Report
**Evaluation Date**: 2026-10-13 11:52:06  
**Architecture**: Scikit-Learn `Pipeline` (TF-IDF Vectorizer -> Balanced Multi-class Logistic Regression)  
**Dataset Partitioning**: Stratified 80/20 Split on Deduplicated Ground Truth (506 samples, 0% Train-Test Contamination)  

---
## 1. Model Performance Overview

| Model Task | Test Accuracy (Unseen) | 5-Fold Stratified CV (Mean ± Std) | Status |
| :--- | :---: | :---: | :---: |
| **Task Categorisation** (5 classes) | **95.10%** | **96.64%** (±1.33%) | Validated |
| **Priority Detection** (4 classes) | **97.06%** | **96.64%** (±1.61%) | Validated |

## 2. Classification Metrics (Test Set Partition)

### 2.1 Task Categorisation Breakdown
| Category | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Administration** | 1.0000 | 1.0000 | 1.0000 | 13.0 |
| **Equipment Check** | 0.9583 | 0.9583 | 0.9583 | 24.0 |
| **Maintenance** | 0.8929 | 0.9615 | 0.9259 | 26.0 |
| **Operations** | 0.9444 | 0.9444 | 0.9444 | 18.0 |
| **Safety & Compliance** | 1.0000 | 0.9048 | 0.9500 | 21.0 |
| **Macro Average** | 0.9591 | 0.9538 | 0.9557 | 102.0 |
| **Weighted Average** | 0.9531 | 0.9510 | 0.9512 | 102.0 |

### 2.2 Priority Detection Breakdown
| Priority Level | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Critical** | 1.0000 | 0.9375 | 0.9677 | 16.0 |
| **High** | 0.9737 | 0.9487 | 0.9610 | 39.0 |
| **Low** | 1.0000 | 1.0000 | 1.0000 | 13.0 |
| **Medium** | 0.9444 | 1.0000 | 0.9714 | 34.0 |
| **Macro Average** | 0.9795 | 0.9716 | 0.9751 | 102.0 |
| **Weighted Average** | 0.9714 | 0.9706 | 0.9705 | 102.0 |

## 3. Real-World Wireframe Test Case Verification

| Test Input | Predicted Category (Conf.) | Predicted Priority (Conf.) | Latency | Result |
| :--- | :--- | :--- | :---: | :---: |
| `Checked Boeing 787 left engine oil and p...` | **Equipment Check** (66.0%) | **High** (68.9%) | 3.14ms | **PASS** |
| `Checked boiler pressure valve on Line 2,...` | **Equipment Check** (30.1%) | **High** (47.9%) | 2.55ms | **PASS** |
| `Major safety alert: jet fuel seepage det...` | **Safety & Compliance** (72.4%) | **Critical** (77.7%) | 2.60ms | **PASS** |
| `Major chemical spill reported in Warehou...` | **Safety & Compliance** (51.3%) | **Critical** (58.2%) | 2.72ms | **PASS** |
| `Rectified TechLog snag #4412: replaced f...` | **Maintenance** (66.0%) | **High** (70.5%) | 2.79ms | **PASS** |
| `Replaced faulty sensor and worn conveyor...` | **Maintenance** (53.7%) | **High** (61.4%) | 2.74ms | **PASS** |
| `Closed and archived Aircraft Technical L...` | **Administration** (86.1%) | **Low** (89.3%) | 2.49ms | **PASS** |
| `Updated shift logbook Section 4 and file...` | **Administration** (67.2%) | **Low** (73.5%) | 2.46ms | **PASS** |
| `Verified final flight plan fuel uplift o...` | **Operations** (65.6%) | **Medium** (66.1%) | 2.61ms | **PASS** |

* **Mean End-to-End Latency**: `2.68 ms` (Ultra-low latency suitable for real-time keystroke suggestions)