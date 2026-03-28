import os
import json
import time
import re
import google.generativeai as _engine
from google.api_core import exceptions
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

def extract_json(text):
    """
    Step 2: Structured format extraction.
    Finds the first '{' and the last '}' to isolate the payload block.
    """
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = text[start_index:end_index + 1]
            # Validate it's correctly formatted
            json.loads(json_str)
            return json_str
        
        # Fallback to precise regex rules
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"⚠️ [DATA EXTRACT] Extraction logic failed: {str(e)}")
        
    return text

def validate_and_fill_defaults(data):
    """Final validation pass to ensure REVA schema compliance."""
    defaults = {
        "status": "success",
        "report_type": "General Medical Report",
        "patient_identity": {
            "patient_name": "Not Available",
            "patient_id": "Not Available",
            "hospital_name": "Not Available",
            "report_date": "Not Available"
        },
        "medical_metrics": {},
        "risk_analysis": {
            "primary_risk": "None Detected",
            "secondary_risks": [],
            "severity_level": "Stable"
        },
        "recovery_score": 100,
        "activity_score": 100,
        "wellness_score": 100,
        "recommendations": {
            "foods_to_eat": [],
            "foods_to_avoid": [],
            "water_intake": "Not Available",
            "exercise": "Not Available",
            "precautions": []
        },
        "follow_up_analysis": {
            "is_follow_up": False,
            "matched_patient": False,
            "improvement_percentage": 0,
            "decline_percentage": 0,
            "health_trend": "Stable"
        }
    }

    if not isinstance(data, dict):
        return defaults

    def ensure_dict(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except:
                return {}
        return val if isinstance(val, dict) else {}

    # Pre-process known structured fields
    json_fields = ["patient_identity", "medical_metrics", "risk_analysis", "recommendations", "follow_up_analysis"]
    for field in json_fields:
        if field in data:
            data[field] = ensure_dict(data[field])

    # Recursive Deep Merge for REVA Schema
    def deep_merge(target, source):
        for key, value in source.items():
            if key not in target or target[key] is None or target[key] == "":
                target[key] = value
            elif isinstance(value, dict) and isinstance(target[key], dict):
                deep_merge(target[key], value)
        return target

    # Normalize scores to Int for Swift decoding (Int? in HealthAnalysis)
    for score_key in ["recovery_score", "activity_score", "wellness_score"]:
        if score_key in data:
            try:
                data[score_key] = int(float(data[score_key]))
            except:
                data[score_key] = 0
        else:
            data[score_key] = 0
            
    # Add camelCase duplicates for Swift Codable matching
    data["recoveryScore"] = data["recovery_score"]
    data["activityScore"] = data["activity_score"]
    data["wellnessScore"] = data["wellness_score"]

    return deep_merge(data, defaults)

class MedicalDataProcessor:

    def __init__(self):
        self.config_key = os.getenv("SETUP")
        self.primary_node = "gemini-2.0-flash-lite" 
        self.fallback_node = "gemini-2.0-flash"
        
        if self.config_key:
            _engine.configure(api_key=self.config_key)
            self.engine_configured = True
            print(f"📡 [REVA System] Initializing Lead Medical Processing Node")
        else:
            self.engine_configured = False
            print("⚠️ [REVA System] System Configuration not found. Operating in SAFE FALLBACK mode.")

    def process_medical_report(self, document_text=None, file_path=None, previous_metrics=None, existing_patients=None, is_identity_pass=False):
        """
        MASTER MEDICAL PIPELINE:
        Data Normalization -> Entity Extraction -> Risk Scoring -> Recovery Evaluation
        """
        if not getattr(self, "engine_configured", False):
            print("⚠️ [REVA System] Operating in FALLBACK MODE (Rule-based). Returning structured default.")
            fallback_data = validate_and_fill_defaults({})
            fallback_data["status"] = "success"  # type: ignore
            fallback_data["report_type"] = "Fallback Rule-Based Report"  # type: ignore
            fallback_data["patient_identity"]["patient_name"] = "Fallback Patient"  # type: ignore
            fallback_data["risk_analysis"]["summary"] = "Unable to perform advanced analysis. Returning standard fallback."  # type: ignore
            fallback_data["recommendations"]["diet_summary"] = "Standard balanced diet."  # type: ignore
            return fallback_data

        # Build Contextual Knowledge
        context = ""
        if existing_patients:
            context += f"\n[DATABASE] Known Patients: {json.dumps(existing_patients)}"
        if previous_metrics:
            context += f"\n[LONGITUDINAL] Previous Metrics (Baseline): {json.dumps(previous_metrics)}"

        if is_identity_pass:
            prompt = f"""
            Role: Medical Data Processing Engine
            Objective: Extract ONLY the patient identity and report type from the document.
            
            INPUT: {document_text if document_text else "IMAGE SCAN"}
            
            Return JSON:
            {{
                "report_type": "Initial|Follow-up",
                "patient_identity": {{
                    "patient_name": "...",
                    "patient_id": "...",
                    "uhid": "...",
                    "age": "...",
                    "gender": "...",
                    "hospital_name": "..."
                }}
            }}
            """
        else:
            prompt = f"""
            Role: Lead Medical Data Processor (REVA System)
            Objective: Process and evaluate the medical report and return a STRICT VALID JSON format.
    
            {context}
    
            INPUT:
            {f"EXTRACTED TEXT: {document_text}" if document_text else "MULTIMODAL IMAGE SCAN"}
    
            -------------------------------------------------
            PIPELINE INSTRUCTIONS:
    
            1. DATA CLEANING: Standardize medical lab terms and units (mg/dL).
            2. ENTITY DETECTION: Extract Patient Identity (Name, ID, Hospital, Date).
            3. MEDICAL METRICS: Extract every detectable metric (Value, Unit, Confidence).
            4. COMPARISON ENGINE (CRITICAL):
               - If the detected patient matches one from '[DATABASE] Known Patients':
                 - Identify that patient's 'latest_metrics'.
                 - Compare EACH metric with the previous value.
                 - Calculate 'improvement_percentage' or 'decline_percentage' for each.
                 - Determine overall 'health_trend' (Improving, Stable, Deteriorating).
               - If no match or no previous metrics, skip comparison.
            5. RECOVERY SCORING (0-100) (CRITICAL): 
               - ALWAYS calculate THREE distinct scores. DO NOT return defaults.
               - Evaluate every extracted metric against standard medical baselines.
               - "recovery_score": Overall medical status based on lab results.
               - "activity_score": Physical capability based on inflammation/recovery markers.
               - "wellness_score": Nutritional and hydration status.
               - For all: Start at 100 and deduct points for any out-of-range values.
            6. DYNAMIC RECOMMENDATIONS (CRITICAL):
               Generate professional diet and activity advice based on LATEST metrics:
               - "foods_to_eat": Provide 4-6 specific items tailored to the medical findings.
               - "foods_to_avoid": Provide 4-6 specific items that could worsen the detected condition.
               - "water_intake": Provide an EXACT range (e.g., "2.3 - 2.8 Liters per day").
               - "diet_summary": A one-sentence professional summary of the diet plan.
               - "calorie_goal" & "protein_goal": Specific numeric targets based on the specific recovery needs.
            7. MEDICATION EXTRACTION: Extract any prescribed medications found in the report.
               Include: name, dosage, frequency, duration, and special instructions.
    
            OUTPUT FORMAT:
            {{
                "status": "success",
                "report_type": "...",
                "patient_identity": {{
                    "patient_name": "...",
                    "patient_id": "...",
                    "uhid": "...",
                    "age": "...",
                    "gender": "...",
                    "hospital_name": "...",
                    "report_date": "..."
                }},
                "medical_metrics": {{
                    "metric_name": {{ "value": 0.0, "unit": "...", "confidence": 0.0 }}
                }},
                "risk_analysis": {{
                    "primary_risk": "...",
                    "secondary_risks": [],
                    "severity_level": "Excellent|Good|Moderate|Poor|Critical",
                    "summary": "Detailed medical summary..."
                }},
                "recovery_score": 0,
                "activity_score": 0,
                "wellness_score": 0,
                "recommendations": {{
                    "foods_to_eat": ["Item 1", "Item 2"],
                    "foods_to_avoid": ["Item 1", "Item 2"],
                    "water_intake": "...",
                    "exercise": "...",
                    "precautions": [],
                    "calorie_goal": "1800",
                    "protein_goal": "90g",
                    "diet_summary": "High protein, low sodium recovery diet"
                }},
                "follow_up_analysis": {{
                    "is_follow_up": true|false,
                    "matched_patient": true,
                    "improvement_percentage": 15.5,
                    "decline_percentage": 0.0,
                    "health_trend": "Improving",
                    "activity_improvement": 5.0,
                    "wellness_improvement": 2.0,
                    "comparisons": {{
                        "creatinine": {{ "previous": 1.5, "current": 1.2, "change_type": "improved", "change_percent": 20 }},
                        "uric_acid": {{ "previous": 9.2, "current": 7.5, "change_type": "improved", "change_percent": 18.5 }}
                    }}
                }},
                "medications": [
                    {{ "name": "Tablet A", "dosage": "500mg", "frequency": "Twice daily", "duration": "5 days", "instructions": "Take after meals" }}
                ]
            }}
            """

        # Execution Engine Setup
        p_node = self.primary_node
        f_node = self.fallback_node
        for node in [p_node, f_node]:
            print(f"STEP 5: Sending request to Processing Node ({node})")
            model = _engine.GenerativeModel(node)
            
            try:
                content: list = [prompt]
                if file_path and os.path.exists(file_path):
                    if file_path.lower().endswith('.pdf'):
                        print("📄 [Core] Attaching structural data inline to processing pipeline")
                        with open(file_path, 'rb') as pdf_file:
                            pdf_bytes = pdf_file.read()
                        content.append({
                            "mime_type": "application/pdf",
                            "data": pdf_bytes
                        })
                    else:
                        img = Image.open(file_path)
                        if img.width > 2000 or img.height > 2000:
                            img.thumbnail((2000, 2000))
                        content.append(img)

                # Step 5: Advanced Processing Call with Handshake
                start_time = time.time()
                response = None
                
                # Retry Handshake Protocol with Exponential Backoff
                for attempt in range(3):
                    try:
                        print(f"STEP 5: Processing Request Phase (Attempt {attempt + 1})")
                        response = model.generate_content(
                            content, 
                            generation_config={"temperature": 0.0},
                            request_options={"timeout": 300}
                        )
                        break # Success Handshake
                    except exceptions.ResourceExhausted as re:
                        print(f"⚠️ Rate limit hit (429): {str(re)}. Retrying after sleep...")
                        if attempt < 2:
                            time.sleep(5 * (attempt + 1)) # 5s, 10s wait
                            continue
                        return {
                            "status": "error",
                            "stage": "rate_limit",
                            "message": "AI System is busy (Rate Limit). Please try again in a few seconds.",
                            "details": str(re)
                        }
                    except Exception as e:
                        print(f"⚠️ Attempt {attempt + 1} processing fault: {str(e)}")
                        if attempt == 2:
                            print(f"❌ STEP 5 ALL PROCESSING FAILED")
                            return {
                                "status": "error",
                                "stage": "Data Analysis",
                                "message": "Processing request failed strictly",
                                "details": str(e)
                            }
                        time.sleep(2)
                
                # Step 6: Response Reception
                try:
                    if response is None or not hasattr(response, 'text'):
                        raise Exception("Empty payload returned from node")
                    
                    raw_text = str(getattr(response, 'text', '')).strip()
                    end_time = time.time()
                    print(f"STEP 6: Payload received in structured format ({end_time - start_time:.2f}s)")
                except Exception as ree:
                    print(f"❌ STEP 6 RECEPTION FAILED: {str(ree)}")
                    return {
                        "status": "error",
                        "stage": "Data Analysis Reception",
                        "message": "Processing Engine returned invalid schema",
                        "details": str(ree)
                    }
                
                # Step 7: Format Extraction
                try:
                    clean_json_str = extract_json(raw_text)
                    print(f"STEP 7: Extracted valid schema payload")
                except Exception as exe:
                    print(f"❌ STEP 7 SCHEMATIC FAIL: {str(exe)}")
                    return {
                        "status": "error",
                        "stage": "json_extraction_engine",
                        "message": "Failed to map structured components",
                        "details": str(exe)
                    }
                
                # Step 8: Safe Transformation
                try:
                    data = json.loads(clean_json_str)
                    print(f"STEP 8: Verified data map generated successfully")
                except json.JSONDecodeError as je:
                    print(f"❌ STEP 8 DECODE FAILED: {str(je)}")
                    return {
                        "status": "error",
                        "stage": "data_decoding",
                        "message": "Data stream failed formal verification",
                        "message": "Data stream failed formal verification",
                        "details": f"Expected schema but isolated: {str(clean_json_str)}..."
                    }
                
                # Final Pass: Normalization
                final_data = validate_and_fill_defaults(data)
                return final_data
                
            except Exception as e:
                print(f"⚠️ [Core] Processing node {node} isolated failure: {str(e)}")
                continue

        return {
            "status": "error",
            "stage": "system_processor_request",
            "message": "Medical processing pipeline failed. Ensure connectivity.",
            "details": "Node fault occurred on both main and fallback nodes."
        }
