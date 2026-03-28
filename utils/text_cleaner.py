import re

def clean_ocr_text(text):
    """
    Cleans OCR text: corrects common OCR errors, merges broken words, 
    and splits lines properly. Limits length to 8000 chars.
    """
    if not text:
        return ""
    
    # STEP 1: Truncate to avoid Gemini context bloating
    text = text[:8000]

    # STEP 2: Remove special noise characters common in bad OCR
    text = re.sub(r'[|\\_~`^*]', ' ', text)
    
    # STEP 3: Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # STEP 4: Common Medical Term Corrections
    corrections = {
        r"S\.? Creat": "Creatinine",
        r"Sr\.? Creatinine": "Creatinine",
        r"Bld\.? Urea": "Blood Urea",
        r"Na\+": "Sodium",
        r"K\+": "Potassium",
        r"Cl-": "Chloride",
        r"Hb": "Hemoglobin",
        r"Hgb": "Hemoglobin",
        r"S\.? Bilirubin": "Serum Bilirubin",
        r"SGPT": "ALT",
        r"SGOT": "AST",
        r"mg\s?/\s?dL": "mg/dL",
        r"g\s?/\s?dL": "g/dL"
    }
    
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text.strip()

def normalize_medical_terms(text):
    """
    The AI handles most of this now, but we keep this for legacy reasons.
    """
    return text
