from .db_connection import db
from datetime import datetime, timezone

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=True) # Plain text for manual viewing as requested
    phone = db.Column(db.String(20), nullable=True)
    otp = db.Column(db.String(10), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Profile & Medical Stats
    location = db.Column(db.String(100), nullable=True)
    height = db.Column(db.String(20), nullable=True)
    weight = db.Column(db.String(20), nullable=True)
    blood_type = db.Column(db.String(20), nullable=True)
    allergies = db.Column(db.Text, nullable=True)

    patients = db.relationship("Patient", backref="owner", lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    patient_name = db.Column(db.String(100), nullable=True)
    patient_id = db.Column(db.String(100), nullable=True) # External Hospital/Patient ID
    age = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    hospital = db.Column(db.String(200), nullable=True)

    reports = db.relationship("HealthReport", backref="patient", lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super(Patient, self).__init__(**kwargs)

class MedicalMetric(db.Model):
    __tablename__ = "medical_metrics_data"
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("health_reports.id"), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(50), nullable=True) # Stored as string to handle ranges/decimal
    unit = db.Column(db.String(50), nullable=True)
    confidence = db.Column(db.Float, default=0.0)

    def __init__(self, **kwargs):
        super(MedicalMetric, self).__init__(**kwargs)

class HealthReport(db.Model):
    __tablename__ = "health_reports"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    report_type = db.Column(db.String(100), nullable=False, default="General")
    report_file = db.Column(db.String(255), nullable=True)
    
    # Core Data
    medical_metrics_json = db.Column(db.JSON, nullable=True)
    patient_identity_json = db.Column(db.JSON, nullable=True)
    
    # Analysis results
    recovery_score = db.Column(db.Integer, nullable=True)
    activity_score = db.Column(db.Integer, nullable=True)
    wellness_score = db.Column(db.Integer, nullable=True)
    risk_level = db.Column(db.String(50), nullable=True) # excellent, good, moderate, poor, critical
    primary_risk = db.Column(db.String(255), nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    
    # Structured recommendations
    recommendations_json = db.Column(db.JSON, nullable=True)
    medications_json = db.Column(db.JSON, nullable=True)
    
    metrics_list = db.relationship("MedicalMetric", backref="report", lazy=True, cascade="all, delete-orphan")
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super(HealthReport, self).__init__(**kwargs)

class FollowupComparison(db.Model):
    __tablename__ = "followup_comparisons"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    previous_report_id = db.Column(db.Integer, db.ForeignKey("health_reports.id"), nullable=True)
    current_report_id = db.Column(db.Integer, db.ForeignKey("health_reports.id"), nullable=False)
    improvement_percentage = db.Column(db.Float, default=0.0)
    activity_improvement = db.Column(db.Float, default=0.0)
    wellness_improvement = db.Column(db.Float, default=0.0)
    decline_percentage = db.Column(db.Float, default=0.0)
    health_trend = db.Column(db.String(50), nullable=True) # improving, stable, deteriorating
    comparison_summary = db.Column(db.Text, nullable=True)
    comparisons_json = db.Column(db.JSON, nullable=True)

    def __init__(self, **kwargs):
        super(FollowupComparison, self).__init__(**kwargs)
