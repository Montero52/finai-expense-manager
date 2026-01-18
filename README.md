# FinAI - Intelligent Expense Manager

> **Full-stack Personal Finance App powered by Google Gemini 2.0 & RAG**

## Introduction

**FinAI** is a smart personal finance management web application designed to simplify expense tracking using Artificial Intelligence. Unlike traditional apps that require tedious manual entry, FinAI integrates **Google Gemini 2.0 Flash** to automatically categorize transactions and provide real-time financial advice via an interactive chatbot.

### Project Status

> **Current Stage: MVP (Minimum Viable Product)**
> This project is currently under active development. While the core AI and transaction tracking modules are fully functional, several features (Budgeting, Advanced Admin Analytics) are in the prototyping phase. Please refer to the **Work in Progress** section below for details.

---

## Key Features (Implemented)

### 1. AI-Powered Features (Gemini 2.0)

* **Smart NLP Categorization:** Users can type natural descriptions (e.g., *"Dinner with friends 500k"*), and the AI automatically detects the category (Dining) and processes the amount without manual selection.
* **Context-Aware Chatbot (RAG):** A built-in assistant that answers questions based on actual wallet balances and transaction history (Retrieval Augmented Generation).
* **Spending Insights:** The AI analyzes transactions to provide warnings or advice directly within the chat interface.

### 2. Core Finance Management

* **Multi-Wallet System:** Manage multiple sources of funds including Cash, Bank Accounts, and Credit Cards.
* **Visual Reports:** Interactive charts (Pie, Bar, Line) powered by **Chart.js** to visualize cash flow over time.
* **Data Export:**
* Export transaction history to Excel (`.xlsx`) for offline analysis.
* Generate Print-friendly Reports (HTML/PDF view) for monthly reviews.



---

## Work in Progress (Incomplete Features)

The following modules are visible in the user interface but are currently partially implemented or under construction:

* **Budgeting Module:** The UI for setting monthly budget limits exists, but the backend logic for enforcing limits and alerts is currently **not connected**.
* **Foundations (Knowledge Hub):** A section designed for financial literacy articles. Currently serves as a placeholder for future content integration.
* **Admin Analytics:** The Admin Dashboard supports User Management (RBAC), but system-wide analytics charts are currently being developed.

---

## Tech Stack

| Component | Technology |
| --- | --- |
| **Backend** | Python 3.11, Flask (Web Framework) |
| **Database** | SQLAlchemy (ORM), SQLite (Default) |
| **AI & LLM** | Google Generative AI SDK (`gemini-2.0-flash`) |
| **Data Processing** | Pandas (Dataframes, Excel Export) |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js |
| **Utilities** | Flask-Mail (Notifications), Dotenv (Config) |

---

## Installation & Setup

**1. Clone the repository**

```bash
git clone https://github.com/Montero52/finai-expense-manager.git
cd finai-expense-manager
```

**2. Create a Virtual Environment**

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables**
Create a `.env` file in the root directory and add your keys (Database path is configured automatically in `config.py`):

```env
# Security Key
SECRET_KEY=your_secret_key_here

# Google Gemini AI Key (Required)
GEMINI_API_KEY=your_google_gemini_api_key_here

# Email Configuration (For Reset Password)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

**Important Notes:**

* **AI Key:** You need a valid Google AI Studio API Key to enable Chatbot & Categorization features.
* **Database:** No configuration needed. The SQLite database is automatically created at `instance/quanlychitieu.db` upon startup.


**5. Create Admin Account**
Run the setup script to initialize a superuser account for system management:

```bash
python create_admin.py
```

**Default Credentials:**

* **Email:** `admin@finance.com`
* **Password:** `admin123`

**6. Run the Application**

```bash
python run.py
```

Access the app at: `http://127.0.0.1:5000`

---

## Roadmap & Limitations

**Current Limitations:**

* **Fixed AI Categories:** Currently, the AI maps transactions to a fixed set of categories (e.g., Food, Transport). Future versions will support user-defined dynamic categories.
* **Mobile Responsiveness:** The dashboard is optimized for Desktop view.
* **AI Latency:** Response times depend on the Google Gemini API (approx. 2-5 seconds).

**Future Development:**

* [ ] Implement backend logic for Budgeting Module.
* [ ] Integrate OCR for receipt scanning.
* [ ] Deploy to cloud platforms (AWS/Render).

---

## Authors & Acknowledgments

**Lead Developer & Maintainer:**

* **Trần Nhật Quý** ([@Montero52](https://github.com/Montero52))
* **Role:** Full-stack Development, AI Integration (Gemini/RAG), System Architecture.
* **Contact:** [trannhatquy0@gmail.com](mailto:trannhatquy0@gmail.com) | [LinkedIn](https://www.linkedin.com/in/trannhatquy)

**Original Contributors (Capstone Project Team):**
*This project originated as a Graduation Thesis at Duy Tan University. Special thanks to the initial development team:*

* Hồ Hữu Quang Sang
* Phạm Văn Nhật Trường
* Võ Kiều Trang
* Nguyễn Phi Hùng
* Nguyễn Võ Gia Huy

---

> **Note:** This project is developed for educational and research purposes. The current repository serves as an extended version maintained by **Trần Nhật Quý** for personal portfolio and further AI research.
