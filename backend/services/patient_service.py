from database.models import Patient, HealthReport, User, db
import json
import difflib
import re

class PatientService:
    @staticmethod
    def normalize_name(name):
        """Standardizes names by removing titles and extra whitespace."""
        if not name: return ""
        # Remove common titles
        text = str(name).strip().lower()
        text = re.sub(r'^(mr|mrs|ms|dr|md|prof|master)\.?\s+', '', text)
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def identify_or_create_patient(user_id, identity, is_follow_up_request=False):
        """
        Confidence-based matching logic:
        - High weight on name match with User's registered name
        - Confidence score based on name, age, gender, hospital
        - Strict mismatch detection for follow-ups
        """
        extracted_name = str(identity.get('patient_name', '')).strip()
        extracted_id = identity.get('patient_id') or identity.get('uhid') or identity.get('id')
        extracted_age = str(identity.get('age', ''))
        extracted_gender = identity.get('gender')
        extracted_hospital = identity.get('hospital_name')

        norm_extracted_name = PatientService.normalize_name(extracted_name)

        print(f"\n🔍 [MATCHING] Attempting to match: '{extracted_name}' (ID: {extracted_id})")

        user = User.query.get(user_id)
        patients = Patient.query.filter_by(user_id=user_id).all()
        
        def is_valid_id(val):
            if not val:
                return False
            text = str(val).strip().lower()
            noise = ["", "none", "null", "not available", "undefined", "unknown", "n/a", "pending", "patient id", "uhid", "reg no"]
            return text not in noise and len(text) > 2

        best_match = None
        highest_score = 0

        for p in patients:
            score = 0
            
            # 1. CORE ID MATCH (Highest Weight)
            if is_valid_id(extracted_id) and is_valid_id(p.patient_id):
                if str(extracted_id).strip().lower() == str(p.patient_id).strip().lower():
                    score += 85 # Boosted
            
            # 2. NAME MATCHING
            p_name_norm = PatientService.normalize_name(p.patient_name)
            
            if p_name_norm and norm_extracted_name:
                # Exact match
                if p_name_norm == norm_extracted_name:
                    score += 60 # Boosted
                # Partial match (strong indicator)
                elif str(norm_extracted_name) in str(p_name_norm) or str(p_name_norm) in str(norm_extracted_name):
                    score += 45 # Boosted to meet threshold if names relate
                else:
                    similarity = difflib.SequenceMatcher(None, p_name_norm, norm_extracted_name).ratio()
                    if similarity < 0.35:
                        score -= 60 
                    elif similarity > 0.75:
                        score += 25
            
            # 3. AGE/GENDER/HOSPITAL MATCHING
            if extracted_age and p.age and str(extracted_age).strip() == str(p.age).strip():
                score += 15
            if extracted_gender and p.gender and str(extracted_gender).strip().lower() == str(p.gender).strip().lower():
                score += 5
            if extracted_hospital and p.hospital and str(extracted_hospital).strip().lower() in str(p.hospital).strip().lower():
                score += 10

            print(f"   - Testing against '{p.patient_name}': Calculated Score: {score}")
            
            if score > highest_score:
                highest_score = score
                best_match = p

        best_match_name = getattr(best_match, 'patient_name', 'None')
        print(f"📊 [MATCHING] Best match: '{best_match_name}' (Score {highest_score})")
        
        # Threshold Logic
        if is_follow_up_request:
            if highest_score >= 40: 
                return best_match, "existing_patient"
            else:
                # If mismatch during follow-up, we still allow proceeding but as a 'mismatch'
                # which current backend handles by flagged creation or UI verification.
                # However, user wants "If patient is different, create a separate record".
                print(f"⚠️ [MATCHING] Mismatch detected for follow-up. Creating NEW record as requested.")
                return None, "mismatch"

        if highest_score >= 40: 
            return best_match, "existing_patient"

        # Create new patient profile
        print(f"🆕 [MATCHING] Creating new patient profile for '{extracted_name}'")
        new_patient = Patient(
            user_id=user_id,
            patient_name=extracted_name,
            patient_id=extracted_id,
            age=extracted_age,
            gender=extracted_gender,
            hospital=extracted_hospital
        )
        db.session.add(new_patient)
        db.session.commit()
        return new_patient, "new_patient"

    @staticmethod
    def get_patient_history(patient_id):
        return HealthReport.query.filter_by(patient_id=patient_id).order_by(HealthReport.created_at.desc()).all()


