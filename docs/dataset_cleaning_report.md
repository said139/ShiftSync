# ShiftSync NLP Dataset Cleaning & Preprocessing Report
**Execution Date**: 2026-10-13 11:51:20  
**Source File**: `data/shiftsync_handover_nlp_dataset.csv`  
**Clean Benchmark File**: `data/shiftsync_handover_nlp_dataset_deduplicated.csv`  

---
## 1. Executive Summary & Quality Audit

To ensure that the machine learning models generalize to unseen clinical and industrial handover logs without data leakage or overfitting, a rigorous audit and deduplication pipeline was executed.
* **Total Synthetic Handover Records**: `1200`
* **Unique Handover Descriptions**: `506`
* **Exact Duplicate Descriptions**: `694` (repeated across shift schedules and operational domains)
* **Label Conflict Rate**: `0` conflicts (100% label concordance)
* **Missing / Null Values**: `0` across all fields

## 2. Class Distribution (Deduplicated Benchmark)

### 2.1 Operational Category Distribution
| Category | Count | Percentage |
| :--- | :---: | :---: |
| **Maintenance** | 126 | 24.9% |
| **Equipment Check** | 120 | 23.7% |
| **Safety & Compliance** | 106 | 20.9% |
| **Operations** | 90 | 17.8% |
| **Administration** | 64 | 12.6% |

### 2.2 Task Priority Distribution
| Priority | Count | Percentage |
| :--- | :---: | :---: |
| **High** | 180 | 35.6% |
| **Medium** | 178 | 35.2% |
| **Critical** | 82 | 16.2% |
| **Low** | 66 | 13.0% |

### 2.3 Industry Distribution
| Industry Domain | Count | Percentage |
| :--- | :---: | :---: |
| Fleet Airworthiness & CAMO Compliance | 130 | 25.7% |
| Flight Operations (Cockpit & Pilots) | 124 | 24.5% |
| Airframe & Powerplant Engineering | 101 | 20.0% |
| Aeronautical Line Maintenance | 97 | 19.2% |
| Avionics & Flight Control Systems | 54 | 10.7% |

## 3. Text Length & Corpus Statistics

* **Mean Word Count**: `17.9` words per handover description
* **Median Word Count**: `18` words
* **Min Word Count**: `10` words
* **Max Word Count**: `23` words
* **Standard Deviation**: `2.5` words

## 4. Pipeline Implications for Machine Learning

1. **Data Leakage Elimination**: In earlier iterations, random train-test splitting on the 1,200 synthetic corpus allowed identical task descriptions to populate both training and test partitions, yielding artificial 100% accuracy scores.
2. **Strict Evaluation**: Training with stratified train-test splits on the 513 unique descriptions establishes an authentic benchmark where test samples represent strictly unseen operator notes.
3. **Balanced Class Weighting**: Applied `class_weight='balanced'` in multi-class Logistic Regression to ensure minority classes (*Administration*, *Safety & Compliance*, *Critical*) receive proportional penalization during loss minimization.