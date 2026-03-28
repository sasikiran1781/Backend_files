-- REVA Advanced Medical Database (MySQL / XAMPP Compatible)
-- Final Modular Structure

CREATE DATABASE IF NOT EXISTS reva_db;
USE reva_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    otp VARCHAR(10),
    otp_expiry DATETIME,
    location VARCHAR(100),
    height VARCHAR(20),
    weight VARCHAR(20),
    blood_type VARCHAR(20),
    allergies TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Patients Table (Handles multiple profiles per user account)
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    patient_name VARCHAR(100),
    patient_id VARCHAR(100), -- Internal Doc ID (e.g., PT-123)
    age VARCHAR(20),
    gender VARCHAR(20),
    hospital VARCHAR(200),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Health Reports Table
CREATE TABLE IF NOT EXISTS health_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    report_type VARCHAR(100) DEFAULT 'General',
    report_file VARCHAR(255),
    medical_metrics_json LONGTEXT, -- Stores value, unit, confidence
    recovery_score INT,
    activity_score INT,
    wellness_score INT,
    risk_level VARCHAR(50), -- severity_level
    primary_risk VARCHAR(255),
    diagnosis TEXT,
    recommendations_json LONGTEXT, -- Stores foods, exercise, precautions
    medications_json LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- 4. Followup Comparisons Table
CREATE TABLE IF NOT EXISTS followup_comparisons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    previous_report_id INT,
    current_report_id INT NOT NULL,
    improvement_percentage FLOAT DEFAULT 0.0,
    activity_improvement FLOAT DEFAULT 0.0,
    wellness_improvement FLOAT DEFAULT 0.0,
    health_trend VARCHAR(50), -- Improving, Stable, Deteriorating
    comparisons_json LONGTEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (previous_report_id) REFERENCES health_reports(id) ON DELETE SET NULL,
    FOREIGN KEY (current_report_id) REFERENCES health_reports(id) ON DELETE CASCADE
);
