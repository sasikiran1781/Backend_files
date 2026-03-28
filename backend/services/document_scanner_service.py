import os
import shutil
from PIL import Image

class DocumentScannerService:
    @staticmethod
    def extract_text(file_path):
        """
        Extracts raw textual data from medical documents for analysis.
        FALLBACK: If local extraction binaries are omitted from the environment,
        the system delegates extraction to the advanced processing engine.
        """
        print(f"📄 [SCANNER] Processing: {file_path}")
        
        # 1. Verify existence of standard extraction binaries
        binary_path = shutil.which("tesseract")
        
        if not binary_path:
            print("⚠️ [SCANNER] Local extraction binary not found. Delegating to Advanced Processing Engine.")
            return "[Advanced Processing Triggered]"

        # 2. Local extraction attempt
        try:
            import pytesseract
            img = Image.open(file_path)
            if img.width > 2000 or img.height > 2000:
                img.thumbnail((2000, 2000))
            text = pytesseract.image_to_string(img)
            return text if text.strip() else "[Empty Scanner Result - Fallback Trigger]"
        except Exception as e:
            print(f"❌ [SCANNER] Extraction Error: {str(e)}")
            return "[Advanced Processing Triggered]"

    @staticmethod
    def is_scanner_available():
        return shutil.which("tesseract") is not None
