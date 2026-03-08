# FinAI | Intelligent Expense Manager

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Gemini 2.0 Flash](https://img.shields.io/badge/AI-Gemini_2.0_Flash-8E44AD.svg)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Chart.js](https://img.shields.io/badge/Frontend-Chart.js-ff6384.svg)](https://www.chartjs.org/)

An intelligent personal finance solution that transforms natural language inputs into structured financial data, optimized with dynamic multi-currency handling and RAG-based AI assistance.

<!-- <div align="center">
  <img src="assets/images/finai-demo.gif" width="750" alt="FinAI Demo">
  <p><i>AI-powered expense tracking, auto-categorization, and real-time cash flow analytics</i></p>
</div> -->

---
## Project Overview
FinAI revolutionizes manual expense tracking by acting as a smart financial assistant. The system effectively mitigates tedious data entry by implementing **Natural Language Processing (NLP)** to extract transaction details automatically. Engineered for modern web experiences, it seamlessly blends traditional CRUD financial operations with advanced **Retrieval Augmented Generation (RAG)** capabilities.

## Key Technical Highlights
### 1. Global Multi-Currency Architecture
* **Base Currency System:** Maintains absolute data integrity by storing all financial records in a unified Base Currency (VND) within the SQLite database.
* **Dynamic Two-Way Conversion:** Seamlessly converts inputs and formats display values (USD/VND) in real-time across all dashboards, charts, and HTML input forms without altering raw DB values.

### 2. AI-Powered NLP & RAG Pipeline
* **Zero-Click Categorization:** Parses natural language (e.g., "Dinner with friends 500k") to automatically extract amounts, infer context, and assign custom categories.
* **Context-Aware Chatbot:** Interrogates actual wallet balances and historical transaction data using RAG to provide personalized financial advice and anomaly warnings.

### 3. Production-Grade Financial Engine
* **Dynamic Visualizations:** Integrates Chart.js for interactive Pie, Bar, and Line charts to track cash flow trends with localized currency formatting.
* **Budget Enforcement:** Real-time progress tracking, spatial logic for expense distribution, and deadline countdowns for strict budget management.
* **Batch Exporting:** Automated pipeline using Pandas to transcode historical data into native `.xlsx` or print-friendly PDF formats.

## Roadmap (Upcoming Features)

The core MVP is fully operational. The following modules are in the active development pipeline:

- [ ] **Admin Dashboard:** System-wide analytics, user management, and Role-Based Access Control (RBAC).
- [ ] **AI Quota Monitoring:** A dashboard to track Gemini API usage limits and prevent rate-limiting.
- [ ] **Advanced Budget Alerts:** Automated email/Telegram notifications when a user reaches 80% or 100% of their budget.
- [ ] **Database Migration:** Upgrading from SQLite to PostgreSQL for production readiness.

## Tech Stack
* **Core AI:** Google Gemini 2.0 Flash, RAG Architecture.
* **Backend:** Python, Flask, SQLAlchemy ORM.
* **Processing:** Pandas, Global JS `Intl.NumberFormat` implementations.
* **Storage:** SQLite (Transactional DB).
* **Frontend:** HTML5, CSS3, Vanilla JS, Bootstrap 5, Chart.js.

## Project Structure
```text
finai-expense-manager/
├── app/
│   ├── models.py        # SQLAlchemy Database Schemas
│   ├── routes/          # Flask Blueprints (Auth, Dashboard, API)
│   ├── static/          # Frontend assets (CSS, JS logic, Icons)
│   └── templates/       # Jinja2 Web UI templates (HTML)
├── assets/images/       # Project demonstrations (GIFs/Images)
├── data/                # Local SQLite database
├── .env.example         # Environment variables template
├── app.py               # Main entry point & Flask initialization
├── create_admin.py      # Utility script for DB initialization
└── requirements.txt     # Project dependencies
```

## Quick Start

### 1. Prerequisites

* **Python 3.11+**
* **Google Gemini API Key** (Required for NLP Categorization and Chatbot features)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/Montero52/finai-expense-manager.git
cd finai-expense-manager

# Setup Virtual Environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory and add your credentials:

```env
SECRET_KEY=your_secure_secret_key
GEMINI_API_KEY=your_google_ai_studio_api_key
```

### 4. Database Setup & Launch

```bash
# Initialize the database and create default roles
python create_admin.py

# Launch the Dashboard
python app.py
```

*The application will be available at `http://127.0.0.1:5000`.*

<!-- ## License

This project is licensed under the **MIT License**. It is free to use for academic and personal purposes. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for the full license text. -->

## Author

**Trần Nhật Quý** *Lead Developer & Maintainer* | [LinkedIn](https://www.linkedin.com/in/trannhatquy) | [GitHub](https://github.com/Montero52) | [trannhatquy0@gmail.com]()

* **Personal Extensions (v2.0+):** Independently developed and integrated the **Gemini 2.0 Flash AI**, designed the **Global Multi-Currency Architecture**, built the **RAG Chatbot**, and fully refactored the UI/UX & codebase from the original foundation.

**Original Capstone Team (v1.0):**
* FinAI originated as a Graduation Thesis at Duy Tan University. Special thanks to the initial development team for building the core foundation: *Hồ Hữu Quang Sang, Phạm Văn Nhật Trường, Võ Kiều Trang, Nguyễn Phi Hùng, Nguyễn Võ Gia Huy*.