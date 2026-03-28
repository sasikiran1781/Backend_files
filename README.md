# REVA Modular Backend Engine

Advanced Medical AI Backend for the **REVA Health Management Interface**. This engine handles the core processing pipeline from medical report ingestion to AI-driven insights.

## 🚀 Overview

The REVA Backend is designed to transform complex medical documents into actionable health data. It integrates state-of-the-art OCR and Large Language Models (LLMs) to provide an automated, longitudinal health monitoring experience.

## ✨ Key Features

- **Master Upload Pipeline**: Seamlessly processes images (JPG, PNG) and PDF reports.
- **Master AI Engine**: Powered by **Google Gemini 2.5 Flash/Lite**, featuring multimodal analysis.
- **Longitudinal Tracking**: Automatically compares current results with previous patient data to detect trends.
- **Patient Profile Management**: Intelligent patient identification to maintain consistent records.
- **Modular Routing**: Cleanly separated logic for Authentication and Report processing.
- **Simulation Suite**: Includes a advanced data simulator for generating realistic medical datasets.

## 🛠 Tech Stack

- **Framework**: Python / Flask
- **Database**: MySQL (via XAMPP/Local)
- **ORM/Modeling**: SQLAlchemy & Marshmallow
- **AI/Vision**: Google Gemini API, EasyOCR
- **Security**: Werkzeug Password Hashing

## 📋 Prerequisites

- Python 3.10+
- XAMPP (for MySQL)
- Google Gemini API Key

## ⚙️ Setup & Installation

1. **Clone & Navigate**:
   ```bash
   cd reva_backend
   ```

2. **Environment Setup**:
   Ensure you have a `.env` file with the following:
   ```env
   DATABASE_URL=mysql+pymysql://root:@127.0.0.1/reva_db
   SECRET_KEY=your-secret-key
   GEMINI_API_KEY=your-api-key
   MAIL_USERNAME=your-email
   MAIL_PASSWORD=your-app-password
   ```

3. **Install Dependencies**:
   ```bash
   chmod +x v_env.sh
   ./v_env.sh
   ```

4. **Run the Server**:
   ```bash
   source env/bin/activate
   python app.py
   ```
   *The server runs on `http://0.0.0.0:8000` by default.*

## 📡 API Endpoints

### Authentication
- `POST /signup`: Create a new user account.
- `POST /login`: Authenticate and receive user profile.

### Medical Reports
- `POST /upload-report`: Master pipeline (Upload -> OCR -> AI -> DB).
- `GET /patient-history/<user_id>`: Fetch all historical health records.
- `GET /latest-analysis/<user_id>`: Get the most recent medical summary.

## 🧪 Simulation
You can generate a synthetic medical dataset for testing using:
```bash
python simulate_data.py
```

---
*Developed for REVA - Premium Health Management Interface.*
