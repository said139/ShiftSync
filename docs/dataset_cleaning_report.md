# ShiftSync NLP Dataset Cleaning & Preprocessing Report
**Execution Date**: 2026-09-29 17:15:35  
**Source File**: `data/shiftsync_handover_nlp_dataset.csv`  
**Clean Benchmark File**: `data/shiftsync_handover_nlp_dataset_deduplicated.csv`  

---
## 1. Executive Summary & Quality Audit

To ensure that the machine learning models generalize to unseen clinical and industrial handover logs without data leakage or overfitting, a rigorous audit and deduplication pipeline was executed.
* **Total Synthetic Handover Records**: `1200`
* **Unique Handover Descriptions**: `513`
* **Exact Duplicate Descriptions**: `687` (repeated across shift schedules and operational domains)
* **Label Conflict Rate**: `0` conflicts (100% label concordance)
* **Missing / Null Values**: `0` across all fields

## 2. Class Distribution (Deduplicated Benchmark)

### 2.1 Operational Category Distribution
| Category | Count | Percentage |
| :--- | :---: | :---: |
| **Operations** | 158 | 30.8% |
| **Maintenance** | 131 | 25.5% |
| **Safety & Compliance** | 106 | 20.7% |
| **Equipment Check** | 87 | 17.0% |
| **Administration** | 31 | 6.0% |

### 2.2 Task Priority Distribution
| Priority | Count | Percentage |
| :--- | :---: | :---: |
| **Medium** | 188 | 36.6% |
| **Critical** | 157 | 30.6% |
| **High** | 128 | 25.0% |
| **Low** | 40 | 7.8% |

### 2.3 Industry Distribution
| Industry Domain | Count | Percentage |
| :--- | :---: | :---: |
| Healthcare | 110 | 21.4% |
| Energy & Utilities | 108 | 21.1% |
| Security & Facilities | 105 | 20.5% |
| Manufacturing | 101 | 19.7% |
| Logistics & Warehousing | 89 | 17.3% |

## 3. Text Length & Corpus Statistics

* **Mean Word Count**: `16.7` words per handover description
* **Median Word Count**: `16` words
* **Min Word Count**: `10` words
* **Max Word Count**: `25` words
* **Standard Deviation**: `3.0` words

## 4. Pipeline Implications for Machine Learning

1. **Data Leakage Elimination**: In earlier iterations, random train-test splitting on the 1,200 synthetic corpus allowed identical task descriptions to populate both training and test partitions, yielding artificial 100% accuracy scores.
2. **Strict Evaluation**: Training with stratified train-test splits on the 513 unique descriptions establishes an authentic benchmark where test samples represent strictly unseen operator notes.
3. **Balanced Class Weighting**: Applied `class_weight='balanced'` in multi-class Logistic Regression to ensure minority classes (*Administration*, *Safety & Compliance*, *Critical*) receive proportional penalization during loss minimization.