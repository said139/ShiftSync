# ShiftSync ✈️🔄
> **Intelligent Shift Handover & Operational Task Management System for Pilots & Aeronautical Engineers**  
> *Developed for Strathmore University — School of Computing and Engineering Sciences (SCES)*

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Database-SQLite3](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Tests-19%20Passed-brightgreen](https://img.shields.io/badge/Tests-19%2F19%20Passed%20(100%25)-brightgreen.svg)](docs/test_results.md)
[![Aviation-SMS-Compliant](https://img.shields.io/badge/Aviation-ICAO%20Annex%206%20%2F%20KCAA%20SMS-emerald.svg)]()
[![License-Academic](https://img.shields.io/badge/License-Academic%20Use-blue.svg)]()

---

## 📌 Executive Summary & Project Scope

In commercial aviation, miscommunication during shift turnover between **Flight Crew (Pilots)** and **Aircraft Maintenance Engineers (AMEs)** represents a critical safety risk that can lead to flight delays, Aircraft on Ground (AOG) situations, Minimum Equipment List (MEL) non-compliance, and airworthiness hazards.

**ShiftSync** is an intelligent, specialized shift handover management system designed exclusively for:
1. **Pilots (Captains & First Officers)**: Documenting flight deck observations, cockpit snags, turnaround fuel/oil uplifts, weather radar/avionics checks, and sector turnover.
2. **Licensed Aeronautical Engineers (AMEs & Avionics Engineers)**: Logging transit and line maintenance rectifications, clearing snags in the Aircraft Technical Log (TechLog), tracking deferred defects against the Minimum Equipment List (MEL), and issuing Certificates of Release to Service (CRS).
3. **CAMO & Flight Operations Supervisors**: Overseeing airworthiness status, pending aircraft sign-offs, and critical AOG alerts.

ShiftSync integrates a calibrated **Natural Language Processing (NLP)** engine that parses unstructured free-text handover narratives into discrete actionable tasks, classifying their **operational category** and **urgency/priority** in real time (<3ms latency) under ICAO Annex 6 and Kenya Civil Aviation Authority (KCAA) Safety Management System (SMS) guidelines.

---

## 🌟 Key Features

1. **Aviation-Specific Handover Workflows**
   * Pre-structured fields for **Aircraft Tail Number** (e.g., `5Y-KZE`, `5Y-KZG`), **Flight Sector** (e.g., `KQ 102 NBO → LHR`), **Technical Log Page Reference** (e.g., `TL-2026-088`), **Handover Mode** (*Engineer-to-Engineer*, *Pilot-to-Engineer*, *Pilot-to-Pilot*), and **MEL Dispatch Status** (*Nil Active MEL*, *MEL Cat C 21-31-01*).
2. **Aviation NLP Engine (Task Segmentation & Multi-Model Inference)**
   * TF-IDF vectorization paired with calibrated machine learning classifiers retrained on 506 clean, deduplicated aviation operational logs.
   * **Task Categorisation Model**: **95.10%** test accuracy (5-fold CV: **96.64% ± 1.33%**) across *Pre-Flight Inspection / Equipment Check*, *Maintenance*, *Operations*, *Safety & Compliance*, and *Administration*.
   * **Priority Detection Model**: **97.06%** test accuracy (5-fold CV: **96.64% ± 1.61%**) detecting *Critical* (AOG, uncontained leaks, flight control defects), *High* (techlog snags, MEL deferrals), *Medium*, and *Low* tasks.
   * Average inference execution speed: **2.68 ms per task**.
3. **Formal Digital Handover & Legal Custody Transfer**
   * Multi-role accountability: Outgoing Pilot/AME submits -> Incoming Pilot/AME reviews aircraft technical status and digitally confirms sign-off.
   * Generates an immutable audit trail with millisecond timestamps and authorized personnel signatures.
4. **Real-Time Operational Cockpit Dashboard**
   * Real-time metrics: pending handovers, outstanding airworthiness tasks, active sector rotations, and critical AOG notifications.
   * Dual-panel task and report sync between browser UI and SQLite database.
5. **Role-Based Access Control (RBAC)**
   * Built-in persona profiles: Capt. John Doe (Pilot), Eng. Michael Chang (AME), Sarah Jenkins (CAMO Supervisor), Emily Watson (Administrator).

---

## 🏗️ System Architecture & Tech Stack

```
┌────────────────────────────────────────────────────────┐
│                   ShiftSync UI (SPA)                   │
│   HTML5 / Tailwind CSS (Kenya Airways Theme) / JS      │
│   Flight Deck & Line Maintenance Workflows             │
└───────────────────────────▲────────────────────────────┘
                            │ HTTP / JSON REST
┌───────────────────────────▼────────────────────────────┐
│                 Python REST Server                     │
│         (http.server + socketserver, Port 8000)        │
│   Aviation Handover Endpoints & RBAC Validation        │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
              ▼                            ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│     SQLite Database      │  │   Aviation NLP Core      │
│  (Foreign Keys, Checks)  │  │ (TF-IDF + Scikit-Learn)  │
│  Aviation Schema         │  │ models/*.joblib          │
└──────────────────────────┘  └──────────────────────────┘
```

* **Backend:** Python 3.10+ (Standard Library `http.server` & `socketserver`)
* **Machine Learning / NLP:** `scikit-learn`, `numpy`, `pandas`, `joblib`
* **Database:** SQLite3 with strict relational constraints, aviation role checks, and auto-seeding
* **Frontend:** Responsive Single Page Application (vanilla JS, Tailwind CSS, Kenya Airways palette)
* **Automated Testing:** Python `unittest` suite (19 technical & ML verification tests)

---

## 📂 Project Structure

```
SHIFTSYNC/
├── data/
│   ├── shiftsync.db                                 # Relational SQLite database with aviation schema
│   ├── shiftsync_handover_nlp_dataset.csv           # 1,200 synthetic aviation logs
│   └── shiftsync_handover_nlp_dataset_deduplicated.csv # 506 clean, deduplicated aviation samples
├── docs/
│   ├── Chapter_4_Implementation_and_Testing.md      # Academic Report: Implementation & Testing
│   ├── dataset_cleaning_report.md                   # Dataset preparation & deduplication audit
│   ├── nlp_model_evaluation.md                      # Cross-validation & confusion matrix report
│   ├── test_results.md                              # Automated test execution report (19 tests)
│   └── screenshots/                                 # UI wireframes & interface captures
├── models/
│   ├── category_model.joblib                        # Retrained aviation category classifier
│   ├── priority_model.joblib                        # Retrained aviation priority classifier
│   └── vectorizer.joblib                            # Retrained TF-IDF vectorizer (max_features=2500)
├── scripts/
│   ├── append_chapter_4_to_word.py                  # Chapter 4 report compilation utility
│   ├── apply_theme.py                               # Visual theme generator
│   ├── build_aviation_nlp_dataset.py                # Aviation dataset synthesis & cleaning pipeline
│   └── integrate_db_api.py                          # Database API synchronization script
├── .gitignore                                       # Git ignore rules
├── database.py                                      # SQLite schema, aviation roles, seeds & helpers
├── predict.py                                       # Aviation NLP inference & keyword engine
├── requirements.txt                                 # Project dependencies
├── server.py                                        # Full-stack HTTP REST API server
├── shiftsync_core_system.html                       # Flight Deck & AME frontend interface
├── test_suite.py                                    # Automated 19-test verification suite
├── train_model.py                                   # NLP model training pipeline with 5-fold CV
└── README.md                                        # Repository documentation
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

### 5. Retrain Aviation NLP Models (Optional)
The pre-trained aviation models are included in `models/`. To retrain them:
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

ShiftSync includes an automated 19-test verification harness:
* **NLP Model Accuracy & Aviation Domain Tests** (`TC-NLP-01` to `TC-NLP-10`):
  * Pre-flight walkaround, APU checks, critical AOG grounding, TechLog snag rectification, MEL deferrals, and multi-clause sentence segmentation.
* **REST API Endpoints & CRUD Operations** (`TC-API-00` to `TC-API-06`):
  * Health check, telemetry KPI calculation, shift list, task persistence, lifecycle status toggle, aviation handover creation, and custody sign-off.
* **Relational Database Integrity & Constraints** (`TC-DB-01` to `TC-DB-02`):
  * Foreign key referential joins and role `CHECK` constraints rejecting invalid permissions.

To execute the verification suite:
```bash
python test_suite.py
```

**Verification Output:**
```
Ran 19 tests in ~20s
Status: OK (19/19 Passed - 100% Pass Rate)
Exported to: docs/test_results.md
```

---

## 👤 Author & Academic Details

* **Author:** Bakari Said Marika
* **Student ID:** 166229
* **Institution:** Strathmore University
* **Faculty:** School of Computing and Engineering Sciences (SCES)
* **Degree:** Bachelor of Science in Informatics and Computer Science (BICS) / Information Systems
* **Academic Year:** 2026
