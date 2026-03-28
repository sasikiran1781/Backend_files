from flask import Blueprint, request, jsonify, send_file
from database.db_connection import db
from database.models import HealthReport, Patient, MedicalMetric, FollowupComparison, User
from services.document_scanner_service import DocumentScannerService
from services.medical_data_processor import MedicalDataProcessor
from services.patient_service import PatientService
from services.recovery_service import RecoveryService
from services.pdf_service import PDFService
from utils.text_cleaner import clean_ocr_text
import os
import json
from werkzeug.utils import secure_filename

def ensure_dict(data):
    """Ensures that the input data is a Python dictionary."""
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, dict) else {}
        except:
            return {}
    return data if isinstance(data, dict) else {}

def ensure_list(data):
    """Ensures that the input data is a Python list."""
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, list) else []
        except:
            return []
    return data if isinstance(data, list) else []

def normalize_json_field(value, for_db_json_column=True):
    """
    Step 4: Normalization Helper for JSON storage.
    Ensures values are safe for SQLAlchemy db.JSON columns or TEXT columns.
    """
    if value is None:
        return {} if for_db_json_column else "{}"
    
    # Already a dict/list
    if isinstance(value, (dict, list)):
        return value if for_db_json_column else json.dumps(value)
    
    # If it's a string, try to parse it
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if for_db_json_column else value
        except:
            # If not valid JSON string, but column is JSON, return as key?: value
            return {} if for_db_json_column else "{}"
            
    return {} if for_db_json_column else "{}"

def safe_float(val, default=0.0):
    if val is None: return default
    try:
        return float(val)
    except:
        return default

def safe_int(val, default=0):
    if val is None: return default
    try:
        return int(float(val))
    except:
        return default

def map_analysis_to_swift(analysis, report_id=None):
    """Maps the raw AI analysis dictionary to the exact schema expected by the Swift app."""
    # 1. Normalize Medical Metrics (ensure confidence_score)
    raw_metrics = ensure_dict(analysis.get('medical_metrics', {}))
    normalized_metrics = {}
    for key, val in raw_metrics.items():
        if isinstance(val, dict):
            normalized_metrics[key] = {
                "value": str(val.get('value', 'Not Available')),
                "unit": str(val.get('unit', '')),
                "confidence_score": float(val.get('confidence_score') or val.get('confidence') or 0.0)
            }
        else:
            normalized_metrics[key] = {"value": str(val), "unit": "", "confidence_score": 0.0}

    # 2. Normalize Recommendations (ensure recovery_precautions and exercise)
    raw_recs = ensure_dict(analysis.get('recommendations', {}))
    normalized_recs = {
        "foods_to_eat": raw_recs.get("foods_to_eat", []),
        "foods_to_avoid": raw_recs.get("foods_to_avoid", []),
        "water_intake": raw_recs.get("water_intake", "Not Available"),
        "water_goal": raw_recs.get("water_intake", "Not Available"), # Alias
        "exercise": raw_recs.get("exercise") or raw_recs.get("exercise_guidelines") or "Not Available",
        "recovery_precautions": raw_recs.get("recovery_precautions") or raw_recs.get("precautions") or [],
        "diet_summary": raw_recs.get("diet_summary") or "Custom Recovery Diet",
        "calorie_goal": str(raw_recs.get("calorie_goal", "1800")),
        "protein_goal": str(raw_recs.get("protein_goal", "85g")),
        # Add camelCase aliases for Swift
        "foodsToEat": raw_recs.get("foods_to_eat", []),
        "foodsToAvoid": raw_recs.get("foods_to_avoid", []),
        "waterIntake": raw_recs.get("water_intake", "Not Available"),
        "waterGoal": raw_recs.get("water_intake", "Not Available"),
        "dietSummary": raw_recs.get("diet_summary") or "Custom Recovery Diet",
        "calorieGoal": str(raw_recs.get("calorie_goal", "1800")),
        "proteinGoal": str(raw_recs.get("protein_goal", "85g")),
        "recoveryPrecautions": raw_recs.get("recovery_precautions") or raw_recs.get("precautions") or []
    }

    # 3. Final Response Construction
    return {
        "id": report_id or analysis.get('id'),
        "status": "success",
        "stage": "analysis_complete",
        "report_type": analysis.get('report_type') or analysis.get('document_type', 'General Medical Report'),
        "patient_identity": ensure_dict(analysis.get('patient_identity', {})),
        "diagnosis": analysis.get('diagnosis') or analysis.get('risk_analysis', {}).get('summary'),
        "medical_metrics": normalized_metrics,
        "risk_analysis": {
            "primary_risk": analysis.get('risk_analysis', {}).get('primary_risk', 'None Detected'),
            "secondary_risks": analysis.get('risk_analysis', {}).get('secondary_risks', []),
            "severity_level": analysis.get('risk_analysis', {}).get('severity_level') or analysis.get('severity_level', 'Stable'),
            "summary": analysis.get('risk_analysis', {}).get('summary') or analysis.get('diagnosis', 'Analysis complete.')
        },
        "recovery_score": safe_int(analysis.get('recovery_score')),
        "activity_score": safe_int(analysis.get('activity_score')),
        "wellness_score": safe_int(analysis.get('wellness_score')),
        # Add camelCase score aliases
        "recoveryScore": safe_int(analysis.get('recovery_score')),
        "activityScore": safe_int(analysis.get('activity_score')),
        "wellnessScore": safe_int(analysis.get('wellness_score')),
        "recommendations": normalized_recs,
        "follow_up_analysis": {
            "is_follow_up": bool(analysis.get('follow_up_analysis', {}).get('is_follow_up', False)),
            "matched_patient": bool(analysis.get('follow_up_analysis', {}).get('matched_patient', True)),
            "improvement_percentage": safe_float(analysis.get('follow_up_analysis', {}).get('improvement_percentage')),
            "activity_improvement": safe_float(analysis.get('follow_up_analysis', {}).get('activity_improvement')),
            "wellness_improvement": safe_float(analysis.get('follow_up_analysis', {}).get('wellness_improvement')),
            "decline_percentage": safe_float(analysis.get('follow_up_analysis', {}).get('decline_percentage')),
            "health_trend": analysis.get('follow_up_analysis', {}).get('health_trend', 'Stable'),
            "comparisons": {
                k: {
                    "current": safe_float(v.get('current')) if isinstance(v, dict) else 0.0,
                    "previous": safe_float(v.get('previous')) if isinstance(v, dict) else 0.0,
                    "change_type": str(v.get('change_type', 'Stable')) if isinstance(v, dict) else 'Stable',
                    "change_percent": safe_float(v.get('change_percent')) if isinstance(v, dict) else 0.0
                } for k, v in ensure_dict(analysis.get('follow_up_analysis', {}).get('comparisons', {})).items()
            }
        },
        "improvement": ensure_dict(analysis.get('improvement', {})),
        "medications": ensure_list(analysis.get('medications', [])),
        "created_at": analysis.get('created_at', "")
    }

report_bp = Blueprint('report', __name__)
UPLOAD_FOLDER = 'uploads'
processor = MedicalDataProcessor()

@report_bp.route('/upload-report', methods=['POST'])
def upload_report():
    """
    MASTER REVA PIPELINE: Metadata -> OCR -> Cleaning -> AI Pass 1 -> Identity Match -> Comparison Pass -> Storage
    """
    print("\n--- 📥 [PIPELINE START] ---")
    
    # STEP 1: RECEIVED
    try:
        print("STAGE 1: File upload received")
        if 'file' not in request.files:
            return jsonify({
                "status": "error", 
                "stage": "STAGE 1: File upload",
                "message": "Upload request missing 'file' key"
            }), 400
        
        user_id = request.form.get('user_id')
        file = request.files['file']
        
        if not file or file.filename == '':
            return jsonify({
                "status": "error", 
                "stage": "STAGE 1: File upload",
                "message": "Empty filename in request"
            }), 400

        if not file.filename:
            return jsonify({"status": "error", "message": "Invalid filename"}), 400
            
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            
        file.save(file_path)
        print(f"STAGE 1: File saved success: {filename}")
    except Exception as e:
        print(f"❌ STAGE 1 FAILED: {str(e)}")
        return jsonify({
            "status": "error", 
            "stage": "STAGE 1: File upload",
            "message": "System could not save your medical file"
        }), 500

    # STEP 2: DATA SCANNING
    try:
        print("STAGE 2: Document Scanner module started")
        raw_text = DocumentScannerService.extract_text(file_path)
    except Exception as e:
        print(f"❌ STAGE 2 FAILED: {str(e)}")
        return jsonify({
            "status": "error", 
            "stage": "STAGE 1: OCR Extraction",
            "message": "Failed to read the document scan"
        }), 500
    
    # STEP 3: DATA SANITIZATION
    try:
        print("STAGE 3: Text sanitization started")
        clean_text = clean_ocr_text(raw_text)
    except Exception as e:
        print(f"❌ STAGE 3 FAILED: {str(e)}")
        return jsonify({
            "status": "error", 
            "stage": "STAGE 2: OCR Cleaning",
            "message": "Failed to clean document noise"
        }), 500
    
    # STEP 4: MEDICAL VALIDATION
    try:
        print("STAGE 4: Medical validation bypass for multimodal support")
        # Proceed with file_path to Advanced Processing Engine
    except Exception as e:
        pass
        return jsonify({
            "status": "error", 
            "stage": "STAGE 4: Medical Metric Extraction",
            "message": "Validation process failed"
        }), 400

    # STEP 5: PRE-FETCH PATIENT CONTEXT
    try:
        print("STAGE 5: Building historical context for all user patients")
        patients = Patient.query.filter_by(user_id=user_id).all()
        user_patients_context = []
        for p in patients:
            # Get latest metrics for each patient to provide as context
            latest_metrics = RecoveryService.get_latest_metrics(p.id)
            user_patients_context.append({
                "patient_name": p.patient_name,
                "patient_id": p.patient_id,
                "age": p.age,
                "gender": p.gender,
                "latest_metrics": latest_metrics
            })
            
        # STEP 6: UNIFIED SYSTEM PROCESSING
        print(f"STAGE 6: Unified System Processing with {len(user_patients_context)} known patient profiles")
        
        analysis = processor.process_medical_report(
            document_text=clean_text, 
            file_path=file_path, 
            existing_patients=user_patients_context if user_patients_context else None
        )
        
        if analysis.get('status') == 'error':
            return jsonify(analysis), 400

        # STEP 7: PATIENT IDENTIFICATION (POST-ANALYSIS)
        print("STAGE 7: Verifying results and matching identity in database")
        extracted_identity = analysis.get('patient_identity', {})
        report_type = analysis.get('report_type', 'Medical Report')
        
        # Merge AI detection and User manual selection
        ai_follow_up = bool(analysis.get('follow_up_analysis', {}).get('is_follow_up', False))
        user_manual_follow_up = request.form.get('is_follow_up', 'false').lower() == 'true'
        
        is_follow_up_detected = user_manual_follow_up or ai_follow_up or \
                                "FOLLOW-UP" in report_type.upper() or "FOLLOW UP" in report_type.upper()

        patient, patient_status = PatientService.identify_or_create_patient(
            user_id, 
            extracted_identity, 
            is_follow_up_request=user_manual_follow_up # Respect user intent primarily
        )
        
        # SOFT MISMATCH: Instead of blocking with 400, we proceed but mark matched_patient=False
        # This allows the App to show the Verification screen.
        # Only block with error if the user explicitly requested a follow-up and it's a mismatch
        if user_manual_follow_up and patient_status == "mismatch":
            print(f"⚠️ IDENTITY MISMATCH: Blocking follow-up request for data integrity.")
            return jsonify({
                "status": "error",
                "stage": "identity_mismatch",
                "message": "Report identity mismatch. This file belongs to a different patient.",
                "details": f"Expected current patient but found: {extracted_identity.get('patient_name', 'Unknown')}"
            }), 400


        # Sync analysis flags
        if 'follow_up_analysis' not in analysis:
            analysis['follow_up_analysis'] = {}
        analysis['follow_up_analysis']['is_follow_up'] = is_follow_up_detected
        analysis['follow_up_analysis']['matched_patient'] = (patient_status != "mismatch")

    except Exception as e:
        print(f"❌ UNIFIED PIPELINE FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error", 
            "stage": "Unified Data Processing",
            "message": "Processing Engine failed within timeout",
            "details": str(e)
        }), 500

    # STEP 9: DATABASE SAVE
    try:
        # Validate Schema Before Store
        required_cols = ['patient_identity_json', 'medical_metrics_json', 'recommendations_json', 'recovery_score', 'risk_level', 'primary_risk', 'diagnosis']
        from sqlalchemy import inspect
        table_cols = [c.name for c in inspect(HealthReport).columns] # type: ignore
        missing = [rc for rc in required_cols if rc not in table_cols]
        if missing:
             return jsonify({
                 "status": "error",
                 "stage": "database_save",
                 "message": "Critical database schema mismatch",
                 "details": f"Missing columns in 'health_reports': {', '.join(missing)}"
             }), 500

        # APPLY NORMALIZATION & DEBUG LOGGING
        patient_identity = analysis.get('patient_identity', {})
        medical_metrics = analysis.get('medical_metrics', {})
        risk_analysis = analysis.get('risk_analysis', {})
        recommendations = analysis.get('recommendations', {})
        follow_up_analysis = analysis.get('follow_up_analysis', {})

        # Normalize for DB
        norm_metrics = normalize_json_field(medical_metrics)
        norm_identity = normalize_json_field(patient_identity)
        norm_recs = normalize_json_field(recommendations)
        norm_meds = normalize_json_field(analysis.get('medications', []))
        
        if not patient:
            return jsonify({"status": "error", "message": "Reference patient missing"}), 400

        new_report = HealthReport(
            patient_id=patient.id,
            report_type=analysis.get('report_type', 'General'),
            report_file=filename,
            medical_metrics_json=norm_metrics,
            patient_identity_json=norm_identity,
            recovery_score=analysis.get('recovery_score', 0),
            activity_score=analysis.get('activity_score', 0),
            wellness_score=analysis.get('wellness_score', 0),
            risk_level=risk_analysis.get('severity_level'),
            primary_risk=risk_analysis.get('primary_risk'),
            diagnosis=risk_analysis.get('summary') or analysis.get('diagnosis'),
            recommendations_json=norm_recs,
            medications_json=norm_meds
        )
        db.session.add(new_report)
        db.session.flush()
        
        # Save individual metrics
        for m_name, m_data in medical_metrics.items():
            if isinstance(m_data, dict):
                db.session.add(MedicalMetric(
                    report_id=new_report.id,
                    metric_name=m_name,
                    value=str(m_data.get('value', '')),
                    unit=m_data.get('unit', ''),
                    confidence=m_data.get('confidence', 0.0) if m_data.get('confidence') else m_data.get('confidence_score', 0.0)
                ))
            
        # Store Comparison ALWAYS if a previous report exists for the same patient
        p_id = getattr(patient, 'id', -1)
        nr_id = getattr(new_report, 'id', -1)
        last_report = HealthReport.query.filter(HealthReport.patient_id == p_id, HealthReport.id != nr_id).order_by(HealthReport.created_at.desc()).first()
        if last_report and patient:
            RecoveryService.store_comparison(p_id, last_report.id, nr_id, follow_up_analysis)
        
        db.session.commit()
        print(f"STEP 9: Database save success. Report ID: {new_report.id}")
    except Exception as e:
        db.session.rollback()
        print(f"❌ STEP 9 FAILED: {str(e)}")
        return jsonify({
            "status": "error", 
            "stage": "database_save",
            "message": "Failed to store analysis results in database",
            "details": str(e)
        }), 500

    # STEP 10: SUCCESS
    print("STEP 10: Final API response sent")
    
    # Map to Swift Schema
    analysis['created_at'] = new_report.created_at.strftime("%Y-%m-%d %H:%M:%S")
    final_response = map_analysis_to_swift(analysis, report_id=new_report.id)
    
    print("FINAL API RESPONSE (SCANNED):", json.dumps(final_response, indent=2))
    return jsonify(final_response), 200

@report_bp.route('/patient-history/<int:user_id>', methods=['GET'])
def get_history(user_id):
    """
    Returns all reports for all patients under a user account in standard HealthAnalysis format.
    """
    patients = Patient.query.filter_by(user_id=user_id).all()
    history = []
    

    
    for p in patients:
        reports = HealthReport.query.filter_by(patient_id=p.id).order_by(HealthReport.created_at.desc()).all()
        for r in reports:
            comp = FollowupComparison.query.filter_by(current_report_id=r.id).first()
            
            # Construct analysis-like dict for mapping
            mock_analysis = {
                "report_type": r.report_type,
                "patient_identity": ensure_dict(r.patient_identity_json),
                "medical_metrics": ensure_dict(r.medical_metrics_json),
                "risk_analysis": {
                    "severity_level": r.risk_level,
                    "primary_risk": r.primary_risk,
                    "summary": r.diagnosis
                },
                "recovery_score": r.recovery_score,
                "activity_score": r.activity_score,
                "wellness_score": r.wellness_score,
                "recommendations": ensure_dict(r.recommendations_json),
                "medications": ensure_list(r.medications_json),
                "follow_up_analysis": {
                    "is_follow_up": comp is not None,
                    "improvement_percentage": comp.improvement_percentage if comp else 0.0,
                    "activity_improvement": comp.activity_improvement if comp else 0.0,
                    "wellness_improvement": comp.wellness_improvement if comp else 0.0,
                    "decline_percentage": comp.decline_percentage if comp else 0.0,
                    "health_trend": comp.health_trend if comp else "Stable",
                    "comparisons": ensure_dict(comp.comparisons_json) if comp else {}
                },
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            history.append(map_analysis_to_swift(mock_analysis, report_id=r.id))
            
    return jsonify(history), 200

@report_bp.route('/report-details/<int:report_id>', methods=['GET'])
def get_report_details(report_id):
    """
    Returns full details for a specific report ID in Swift-compatible format.
    """
    report = HealthReport.query.get(report_id)
    if not report:
        return jsonify({"status": "error", "message": "Report not found"}), 404
        

    comp = FollowupComparison.query.filter_by(current_report_id=report.id).first()
    
    mock_analysis = {
        "report_type": report.report_type,
        "patient_identity": ensure_dict(report.patient_identity_json),
        "medical_metrics": ensure_dict(report.medical_metrics_json),
        "risk_analysis": {
            "severity_level": report.risk_level,
            "primary_risk": report.primary_risk,
            "summary": report.diagnosis
        },
        "recovery_score": report.recovery_score or 0,
        "activity_score": report.activity_score or 0,
        "wellness_score": report.wellness_score or 0,
        "recommendations": ensure_dict(report.recommendations_json),
        "medications": ensure_list(report.medications_json),
        "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "follow_up_analysis": {
            "is_follow_up": comp is not None,
            "improvement_percentage": comp.improvement_percentage if comp else 0.0,
            "activity_improvement": comp.activity_improvement if comp else 0.0,
            "wellness_improvement": comp.wellness_improvement if comp else 0.0,
            "decline_percentage": comp.decline_percentage if comp else 0.0,
            "health_trend": comp.health_trend if comp else "Stable",
            "comparisons": ensure_dict(comp.comparisons_json) if comp else {}
        }
    }
    
    return jsonify(map_analysis_to_swift(mock_analysis, report_id=report.id)), 200

@report_bp.route('/latest-analysis/<int:user_id>', methods=['GET'])
def get_latest_analysis(user_id):
    """
    Returns the absolute latest report analysis in standard Swift-compatible format.
    Refined logic: Prioritizes the user's primary patient profile.
    """

    user = User.query.get(user_id)
    patients = Patient.query.filter_by(user_id=user_id).all()
    
    if not patients:
        return jsonify({"status": "error", "message": "No patients found"}), 404
        
    # Get absolute latest report for this user across all their patient profiles
    patient_ids = [p.id for p in patients]
    latest_report = HealthReport.query.filter(
        HealthReport.patient_id.in_(patient_ids)
    ).order_by(HealthReport.created_at.desc()).first()
    
    if not latest_report:
        return jsonify({"status": "error", "message": "No medical reports found"}), 404


    comp = FollowupComparison.query.filter_by(current_report_id=latest_report.id).first()
    
    mock_analysis = {
        "report_type": latest_report.report_type,
        "patient_identity": ensure_dict(latest_report.patient_identity_json),
        "medical_metrics": ensure_dict(latest_report.medical_metrics_json),
        "risk_analysis": {
            "severity_level": latest_report.risk_level or "Stable",
            "primary_risk": latest_report.primary_risk or "None Detected",
            "summary": latest_report.diagnosis or "No summary available"
        },
        "recovery_score": latest_report.recovery_score or 0,
        "activity_score": latest_report.activity_score or 0,
        "wellness_score": latest_report.wellness_score or 0,
        "recommendations": ensure_dict(latest_report.recommendations_json),
        "medications": ensure_list(latest_report.medications_json),
        "created_at": latest_report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "follow_up_analysis": {
            "is_follow_up": comp is not None,
            "improvement_percentage": comp.improvement_percentage if comp else 0.0,
            "activity_improvement": comp.activity_improvement if comp else 0.0,
            "wellness_improvement": comp.wellness_improvement if comp else 0.0,
            "decline_percentage": comp.decline_percentage if comp else 0.0,
            "health_trend": comp.health_trend if comp else "Stable",
            "matched_patient": True,
            "comparisons": ensure_dict(comp.comparisons_json) if comp else {}
        }
    }
    
    return jsonify(map_analysis_to_swift(mock_analysis, report_id=latest_report.id)), 200

@report_bp.route('/report-pdf/<int:report_id>', methods=['GET'])
def get_report_pdf(report_id):
    """
    Generates and returns a PDF for a specific medical report.
    """
    print(f"\n--- 📄 [PDF GENERATION START] Report ID: {report_id} ---")
    report = HealthReport.query.get(report_id)
    if not report:
        return jsonify({"status": "error", "message": "Report not found"}), 404
        

    comp = FollowupComparison.query.filter_by(current_report_id=report.id).first()
    
    # Construct analysis-like dict for PDF generator
    report_data = {
        "report_type": report.report_type,
        "patient_identity": ensure_dict(report.patient_identity_json),
        "medical_metrics": ensure_dict(report.medical_metrics_json),
        "risk_analysis": {
            "severity_level": report.risk_level,
            "primary_risk": report.primary_risk,
            "summary": report.diagnosis
        },
        "recovery_score": report.recovery_score,
        "recommendations": ensure_dict(report.recommendations_json),
        "medications": ensure_list(report.medications_json),
        "follow_up_analysis": {
            "is_follow_up": comp is not None,
            "improvement_percentage": comp.improvement_percentage if comp else 0.0,
            "decline_percentage": comp.decline_percentage if comp else 0.0,
            "health_trend": comp.health_trend if comp else "Stable",
            "comparisons": ensure_dict(comp.comparisons_json) if comp else {}
        }
    }
    
    # Generate PDF
    pdf_service = PDFService()
    temp_filename = f"REVA_Report_{report_id}.pdf"
    
    # Ensure PDF directory exists
    pdf_dir = os.path.join(UPLOAD_FOLDER, 'pdfs')
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
        
    temp_path = os.path.join(pdf_dir, temp_filename)
    
    try:
        pdf_service.generate_report_pdf(report_data, temp_path)
        print(f"✅ PDF Generated: {temp_path}")
        return send_file(
            temp_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=temp_filename
        )
    except Exception as e:
        print(f"❌ PDF GENERATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": "Failed to generate PDF",
            "details": str(e)
        }), 500
