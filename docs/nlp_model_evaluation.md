# ShiftSync NLP Machine Learning Pipeline Evaluation Report
**Evaluation Date**: 2026-10-01 10:23:09  
**Architecture**: Scikit-Learn `Pipeline` (TF-IDF Vectorizer -> Balanced Multi-class Logistic Regression)  
**Dataset Partitioning**: Stratified 80/20 Split on Deduplicated Ground Truth (513 samples, 0% Train-Test Contamination)  

---
## 1. Model Performance Overview

| Model Task | Test Accuracy (Unseen) | 5-Fold Stratified CV (Mean ± Std) | Status |
| :--- | :---: | :---: | :---: |
| **Task Categorisation** (5 classes) | **99.03%** | **98.83%** (±1.14%) | Validated |
| **Priority Detection** (4 classes) | **100.00%** | **98.44%** (±1.59%) | Validated |

## 2. Classification Metrics (Test Set Partition)

### 2.1 Task Categorisation Breakdown
| Category | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Administration** | 1.0000 | 0.8333 | 0.9091 | 6.0 |
| **Equipment Check** | 1.0000 | 1.0000 | 1.0000 | 18.0 |
| **Maintenance** | 1.0000 | 1.0000 | 1.0000 | 26.0 |
| **Operations** | 1.0000 | 1.0000 | 1.0000 | 32.0 |
| **Safety & Compliance** | 0.9545 | 1.0000 | 0.9767 | 21.0 |
| **Macro Average** | 0.9909 | 0.9667 | 0.9772 | 103.0 |
| **Weighted Average** | 0.9907 | 0.9903 | 0.9900 | 103.0 |

### 2.2 Priority Detection Breakdown
| Priority Level | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Critical** | 1.0000 | 1.0000 | 1.0000 | 29.0 |
| **High** | 1.0000 | 1.0000 | 1.0000 | 33.0 |
| **Low** | 1.0000 | 1.0000 | 1.0000 | 9.0 |
| **Medium** | 1.0000 | 1.0000 | 1.0000 | 32.0 |
| **Macro Average** | 1.0000 | 1.0000 | 1.0000 | 103.0 |
| **Weighted Average** | 1.0000 | 1.0000 | 1.0000 | 103.0 |

## 3. Real-World Wireframe Test Case Verification

| Test Input | Predicted Category (Conf.) | Predicted Priority (Conf.) | Latency | Result |
| :--- | :--- | :--- | :---: | :---: |
| `Checked boiler pressure valve on Line 2,...` | **Equipment Check** (46.6%) | **High** (49.7%) | 3.43ms | **PASS** |
| `Major chemical spill reported in Warehou...` | **Safety & Compliance** (67.1%) | **Critical** (61.2%) | 2.61ms | **PASS** |
| `Replaced faulty sensor and worn conveyor...` | **Maintenance** (29.7%) | **High** (40.8%) | 2.83ms | **PASS** |
| `Updated shift logbook Section 4 and file...` | **Administration** (87.1%) | **Low** (89.2%) | 2.37ms | **PASS** |
| `Completed routine inventory reconciliati...` | **Operations** (61.0%) | **Medium** (63.8%) | 2.18ms | **PASS** |

* **Mean End-to-End Latency**: `2.68 ms` (Ultra-low latency suitable for real-time keystroke suggestions)