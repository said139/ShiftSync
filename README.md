# ShiftSync 🔄
> **Intelligent Shift Handover & Operational Task Management System**  
> *Developed for Strathmore University — School of Computing and Engineering Sciences (SCES)*

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Database-SQLite3](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Tests-13%20Passed-brightgreen](https://img.shields.io/badge/Tests-13%2F13%20Passed%20(100%25)-brightgreen.svg)](docs/test_results.md)
[![License-Academic](https://img.shields.io/badge/License-Academic%20Use-blue.svg)]()

---

## 📌 Executive Summary

Shift handover communication failures are a leading cause of operational downtime, safety oversights, and uncoordinated task execution across critical 24/7 industries (aviation, manufacturing, logistics, healthcare). **ShiftSync** bridges this gap by providing an end-to-end, digital shift handover management system integrated with an **AI/NLP classification engine**. 

ShiftSync enables outgoing operators to record unstructured shift logs, automatically segments composite handover entries into discrete tasks, and classifies their **operational category** and **urgency/priority** in real time using machine learning.

---

## 🌟 Key Features

1. **Intelligent Shift Handover Documentation**
   * Standardized structured forms for equipment status, safety observations, and additional remarks.
   * Free-text shift log analyzer powered by Natural Language Processing.
2. **Real-Time NLP Task Segmentation & Classification**
   * TF-IDF vectorization paired with calibrated machine learning classifiers.
   * Automated categorization: *Equipment Check*, *Safety & Compliance*, *Maintenance*, *Administration*.
   * Dynamic priority assignment: *Low*, *Medium*, *High*, *Critical*.
3. **Formal Digital Handover & Acknowledgment Workflow**
   * Multi-role accountability: Outgoing Operator submits -> Incoming Operator reviews and digitally signs/acknowledges with cryptographic-style timestamps and audit logs.
4. **Interactive Operational Dashboard**
   * Real-time metrics: pending handovers, incomplete operational tasks, active shifts, and safety alerts.
   * Interactive task checklist with instant state synchronization to SQLite backend.
5. **Robust System Verification**
   * 100% test coverage across NLP accuracy, REST API endpoints, and relational database integrity constraints.

---

## 🏗️ System Architecture & Tech Stack

```
┌────────────────────────────────────────────────────────┐
│                   ShiftSync UI (SPA)                   │
│   HTML5 / Modern Responsive CSS / Vanilla JavaScript   │
└───────────────────────────▲────────────────────────────┘
                            │ HTTP / JSON REST
┌───────────────────────────▼────────────────────────────┐
│                 Python REST Server                     │
│         (http.server + socketserver, Port 8000)        │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
              ▼                            ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│     SQLite Database      │  │    ShiftSync NLP Core    │
│  (Foreign Keys, Checks)  │  │ (TF-IDF + Scikit-Learn)  │
│    shiftsync.db          │  │ models/*.joblib          │
└──────────────────────────┘  └──────────────────────────┘
```

* **Backend:** Python 3.10+ (Standard Library `http.server` & `socketserver`)
* **Machine Learning / NLP:** `scikit-learn`, `numpy`, `pandas`, `joblib`
* **Database:** SQLite3 with strict relational constraints and auto-seeding
* **Frontend:** Modern Single Page Application (vanilla JS, CSS Grid/Flexbox)
* **Automated Testing:** Python `unittest` framework with automated Chapter 4 Markdown reporting

---

## 📂 Project Structure

```
SHIFTSYNC/
├── data/
│   ├── shiftsync.db                       # Relational SQLite database
│   └── shiftsync_handover_nlp_dataset.csv # Training corpus for NLP models
├── docs/
│   ├── Chapter_4_Implementation_and_Testing.md # Implementation & Verification Report
│   ├── test_results.md                    # Automated test execution output
│   └── screenshots/                       # System interface wireframes & captures
│       ├── 01_shiftsync_dashboard_overview.jpg
│       ├── 02_shiftsync_nlp_shift_log.jpg
│       ├── 03_shiftsync_formal_acknowledgment.jpg
│       ├── 04_shiftsync_create_handover_standard.jpg
│       └── 05_shiftsync_user_management_admin.jpg
├── models/
│   ├── category_model.joblib              # Serialized category classifier
│   ├── priority_model.joblib              # Serialized priority classifier
│   └── vectorizer.joblib                  # Serialized TF-IDF vectorizer
├── scripts/
│   ├── append_chapter_4_to_word.py        # Chapter 4 report compilation utility
│   ├── apply_theme.py                     # Visual theme generator
│   └── integrate_db_api.py                # Database API synchronization script
├── .gitignore                             # Git ignore rules
├── database.py                            # SQLite database schema, seeds & helpers
├── predict.py                             # ShiftSync NLP inference engine
├── requirements.txt                       # Project dependencies
├── server.py                              # Full-stack HTTP REST API server
├── shiftsync_core_system.html             # Core application frontend interface
├── shiftsync_mockup.html                  # Initial UI prototype
├── test_suite.py                          # Automated system verification suite
├── train_model.py                         # NLP model training pipeline
└── README.md                              # Repository documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10 or higher
* Git

### 2. Clone the Repository
```bash
git clone https://github.com/said139/ShiftSync.git
cd ShiftSync
```

### 3. Create & Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. (Optional) Retrain NLP Models
The pre-trained models are already included in `models/`. To retrain them on the dataset:
```bash
python train_model.py
```

### 6. Run the Application Server
```bash
python server.py
```
Open your browser and navigate to:
👉 **`http://localhost:8000`**

---

## 🧪 Automated Testing & Verification

ShiftSync includes an automated test harness covering:
* **NLP Model Accuracy & Task Segmentation** (TC-NLP-01 to TC-NLP-05)
* **REST API Endpoints & CRUD Operations** (TC-API-01 to TC-API-06)
* **Relational Database Integrity & Constraints** (TC-DB-01 to TC-DB-02)

To run the verification suite:
```bash
python test_suite.py
```

**Verification Results:**
```
Ran 13 tests in ~18s
Status: OK (13/13 Passed - 100% Pass Rate)
Exported to: docs/test_results.md
```

---

## 🌿 Git & GitHub Development Workflow

This repository adheres to the university version control guidelines:
* **`main`**: Production-ready, stable releases.
* **`develop`**: Integration branch for ongoing sprint deliverables.
* **`feature/*`**: Feature-specific branches (e.g. `feature/nlp-enhancements`, `feature/rest-api`).
* **Pull Requests & Code Reviews**: All feature branches are merged via reviewed Pull Requests.
* **Issues & Milestones**: Structured across project sprints to track development deliverables.

---

## 👤 Author & Academic Details

* **Author:** Bakari Said Marika
* **Student ID:** 166229
* **Institution:** Strathmore University
* **Course:** Bachelor of Science in Informatics and Computer Science (BICS) / Information Systems
* **Academic Year:** 2026
