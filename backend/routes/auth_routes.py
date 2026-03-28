from flask import Blueprint, request, jsonify, current_app
from flask_mail import Message
from database.db_connection import db, mail
from database.models import User, Patient, HealthReport, FollowupComparison
from werkzeug.security import generate_password_hash, check_password_hash
import re


auth_bp = Blueprint('auth', __name__)



# Email regex
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

# Indian phone validation (10 digits, starts with 6-9)
PHONE_REGEX = r'^[6-9]\d{9}$'


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json

    email = data.get('email')
    password = data.get('password')
    name = data.get('full_name')
    phone = data.get('phone')

    # ✅ Check required fields
    if not email or not password or not name or not phone:
        return jsonify({"error": "All fields are required"}), 400

    # ✅ Email format validation
    if not re.match(EMAIL_REGEX, email):
        return jsonify({"error": "Invalid email format"}), 400

    # ✅ Phone validation
    if not re.match(PHONE_REGEX, phone):
        return jsonify({"error": "Invalid phone number (must be 10 digits, start with 6-9)"}), 400

    # ✅ Password validation (optional but recommended)
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # ✅ Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 400

    # ✅ Create new user
    new_user = User(
        full_name=name,
        email=email,
        phone=phone,
        password_hash=generate_password_hash(password),
        password=password # Save plain text for easy viewing in DB
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Signup successful",
        "id": new_user.id,
        "full_name": new_user.full_name,
        "email": new_user.email,
        "phone": new_user.phone
    }), 201
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone
        }
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.json
    user_id = data.get('user_id')
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all([user_id, current_password, new_password, confirm_password]):
        return jsonify({"status": "error", "stage": "change_password", "message": "Missing required fields"}), 400

    if new_password != confirm_password:
        return jsonify({"status": "error", "stage": "change_password", "message": "Passwords do not match"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "stage": "change_password", "message": "User not found"}), 404

    if not check_password_hash(user.password_hash, current_password):
        return jsonify({"status": "error", "stage": "change_password", "message": "Current password is incorrect"}), 401

    try:
        user.password_hash = generate_password_hash(new_password)
        user.password = new_password
        db.session.commit()
        return jsonify({"status": "success", "message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "stage": "change_password", "message": "Password update failed", "details": str(e)}), 500
@auth_bp.route('/send-otp', methods=['POST'])
@auth_bp.route('/send-otp/', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    import random
    from datetime import datetime, timedelta

    # Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    user.otp = otp_code
    user.otp_expiry = datetime.now() + timedelta(minutes=10)
    db.session.commit()

    # Check credentials are configured
    mail_user = current_app.config.get('MAIL_USERNAME')
    mail_pass = current_app.config.get('MAIL_PASSWORD')
    if not mail_user or not mail_pass or mail_user == 'your_gmail@gmail.com':
        print(f"⚠️ [EMAIL] Mail credentials not set in .env — OTP: {otp_code}")
        return jsonify({
            "message": "OTP generated (email not sent — mail credentials missing in .env)",
            "debug_otp": otp_code
        }), 200

    import threading

    def send_async_email(app, msg):
        with app.app_context():
            try:
                mail.send(msg)
                print(f"📧 [EMAIL] OTP sent successfully to {email}")
            except Exception as e:
                print(f"❌ [EMAIL] SMTP send failed: {str(e)}")

    try:
        msg = Message(
            "REVA Security Verification",
            recipients=[email],
            body=f"Your REVA verification code is: {otp_code}\n\nIt is valid for 10 minutes."
        )
        import typing
        thread = threading.Thread(
            target=send_async_email,
            args=(typing.cast(typing.Any, current_app)._get_current_object(), msg)
        )
        thread.start()

        return jsonify({
            "message": "OTP sent to your email",
            "debug_otp": otp_code   # Remove this line in production
        }), 200
    except Exception as e:
        print(f"❌ [EMAIL] Failed to create mail message: {str(e)}")
        return jsonify({"error": f"Mail send failed: {str(e)}", "debug_otp": otp_code}), 500


@auth_bp.route('/verify-otp', methods=['POST'])
@auth_bp.route('/verify-otp/', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    
    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400
        
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    from datetime import datetime
    
    if user.otp and user.otp == str(otp):
        # Check Expiry
        if user.otp_expiry and user.otp_expiry > datetime.now():
            user.otp = None  # Consume OTP
            user.otp_expiry = None
            db.session.commit()
            return jsonify({"message": "OTP verified successfully"}), 200
        else:
            return jsonify({"error": "OTP has expired"}), 400
            
    return jsonify({"error": "Invalid OTP"}), 400

@auth_bp.route('/reset-password', methods=['POST'])
@auth_bp.route('/reset-password/', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    new_password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    try:
        user.password_hash = generate_password_hash(new_password)
        user.password = new_password
        db.session.commit()
        return jsonify({"message": "Password reset successful"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/delete-account', methods=['POST'])
def delete_account():
    """
    Scrubs all items tied to a user: Patient profiles, Health Reports, 
    Medical Metrics, Follow-up comparisons, and disk files.
    Then deletes the User row.
    """
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"status": "error", "message": "Missing user ID"}), 400
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
        
    try:
        import os
        

        # 1. Fetch related tables to clear files on disk
        patients = Patient.query.filter_by(user_id=user_id).all()
        patient_ids = [p.id for p in patients]
        
        print(f"🧹 [SCRUB] Starting data purge for User {user_id}")
        
        if patient_ids:
            reports = HealthReport.query.filter(HealthReport.patient_id.in_(patient_ids)).all()
            UPLOAD_FOLDER = 'uploads'
            
            # 2. Disk Cleanup
            for r in reports:
                if r.report_file:
                    file_path = os.path.join(UPLOAD_FOLDER, r.report_file)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            print(f"🗑️ Deleted scan: {r.report_file}")
                        except Exception as e:
                            print(f"⚠️ Failed to delete file {r.report_file}: {e}")
                
                # PDF Delete
                pdf_path = os.path.join(UPLOAD_FOLDER, 'pdfs', f"REVA_Report_{r.id}.pdf")
                if os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                        print(f"🗑️ Deleted PDF for report {r.id}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete PDF {pdf_path}: {e}")
                        
            # 3. Database Purge
            # Delete followup comparisons linked to these patients
            FollowupComparison.query.filter(FollowupComparison.patient_id.in_(patient_ids)).delete(synchronize_session=False)
        
        # Delete user triggers cascading delete for Patient -> HealthReport -> MedicalMetric
        db.session.delete(user)
        db.session.commit()
        print(f"✅ [SCRUB] SCRUBBED User {user_id} completely.")
        return jsonify({"status": "success", "message": "User account and all health data deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ [SCRUB] FAILED: {str(e)}")
        return jsonify({"status": "error", "message": "Deletion scrub failed", "details": str(e)}), 500

@auth_bp.route('/update-profile', methods=['POST'])
def update_profile():
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if 'full_name' in data: user.full_name = data['full_name']
    if 'phone' in data: user.phone = data['phone']
    if 'location' in data: user.location = data['location']
    if 'height' in data: user.height = data['height']
    if 'weight' in data: user.weight = data['weight']
    if 'blood_type' in data: user.blood_type = data['blood_type']
    if 'allergies' in data: user.allergies = data['allergies']
    
    try:
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
