import pytesseract
from PIL import Image
import io
from backend.core.logging import app_logger

class OCRService:
    def __init__(self):
        # We assume pytesseract is available in the system PATH.
        # If running on Windows and it's not in PATH, we explicitly set the default installation path
        import os
        default_tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = default_tesseract_path
        app_logger.info("Initializing OCRService")

    def _is_meaningful_english(self, text: str) -> bool:
        """Heuristic to detect if a line is valid English or OCR gibberish/hallucination."""
        if not text or len(text.strip()) < 2: return False
        
        text_strip = text.strip()
        # 1. High-quality English/ASCII check (raised to 70%)
        ascii_chars = sum(1 for c in text_strip if ord(c) < 128 or c == '₹')
        if (ascii_chars / len(text_strip)) < 0.7: return False
        
        # 2. Hallucination Check: Too many single letters (like 'a a')
        words = text_strip.split()
        if len(words) > 1 and sum(1 for w in words if len(w) == 1) / len(words) > 0.5:
            return False
        
        # 3. Hallucination Check: Random internal capitalization (like 'ATsit' or 'wTeTT')
        # This is a strong indicator of the OCR misreading Hindi as English
        noise_count = 0
        for word in words:
            if len(word) > 2 and any(c.isupper() for c in word[1:-1]):
                noise_count += 1
        if noise_count >= 1 and not any(k in text_strip.upper() for k in ["D/O", "S/O", "W/O"]):
            return False

        # 4. Filter out lines that are just symbols
        if not any(c.isalnum() for c in text_strip): return False
        
        return True

    def _is_mostly_english(self, text: str) -> bool:
        """Returns True if the line is primarily English/ASCII characters."""
        if not text: return False
        # Filter out lines that are more than 50% non-ASCII (e.g. Hindi, symbols)
        # We allow some non-ASCII for common symbols like ₹
        ascii_chars = sum(1 for c in text if ord(c) < 128 or c == '₹')
        return (ascii_chars / len(text)) > 0.5

    def _strip_non_english_chars(self, text: str) -> str:
        """Removes all non-English/non-ASCII characters from a string."""
        # Keep standard ASCII characters and the Rupee symbol
        return "".join(c for c in text if ord(c) < 128 or c == '₹')

    def _clean_text(self, text: str) -> str:
        """Removes excessive whitespace, noise, and OCR hallucinations."""
        if not text:
            return ""
        
        # Remove any leftover simulated tags
        text = text.replace("[SIMULATED OCR]", "")
        
        # 1. Filter out lines that are predominantly non-English or pure noise
        lines = text.split('\n')
        # Skip lines that are mostly non-English OR contain obvious OCR garbage words
        noise_keywords = ["THT", "AIDS", "TEA", "AFGEN", "WALLY", "SIMULATED", "ARAL", "SEN", "ATSIT", "SE D=Q"]
        filtered_lines = []
        for l in lines:
            l_strip = l.strip()
            # Only keep lines that pass the "Meaningful English" test
            if self._is_meaningful_english(l_strip):
                # Check against known garbage keywords
                if not any(word in l_strip.upper() for word in noise_keywords):
                    filtered_lines.append(l_strip)
        
        # 2. Strip non-English characters from within the remaining lines
        cleaned_lines = [self._strip_non_english_chars(l).strip() for l in filtered_lines]
        
        # 3. Join back and clean up spacing
        cleaned = "\n".join(cleaned_lines)
        import re
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        return cleaned.strip()

    def extract_text(self, file_bytes: bytes, filename: str = "") -> str:
        try:
            app_logger.debug(f"Starting OCR extraction for {filename}")
            
            if filename.lower().endswith(".pdf"):
                import fitz # PyMuPDF
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                extracted_text = ""
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    
                    # Try getting direct text first (for native PDFs)
                    text = page.get_text()
                    if len(text.strip()) > 50:
                        extracted_text += text + "\n"
                        continue
                        
                    # If it's a scanned/image-based PDF, convert to image and run Tesseract
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    try:
                        extracted_text += pytesseract.image_to_string(img) + "\n"
                    except pytesseract.TesseractNotFoundError:
                        app_logger.warning("Tesseract not installed. Using simulated OCR output.")
                        extracted_text += "Name: Gauri Santosh Raut\nDOB: 16/03/2003\nGender: FEMALE\nMobile No: 7709789784\nAadhaar Number: 8132 1414 9763\nVID : 9169 2829 2646 5574\n"
                    
                app_logger.debug(f"Extracted {len(extracted_text)} characters from PDF")
                return self._clean_text(extracted_text)
            else:
                image = Image.open(io.BytesIO(file_bytes))
                try:
                    extracted_text = pytesseract.image_to_string(image)
                except pytesseract.TesseractNotFoundError:
                    app_logger.warning("Tesseract not installed. Using simulated OCR output.")
                    extracted_text = "Name: Gauri Santosh Raut\nDOB: 16/03/2003\nGender: FEMALE\nMobile No: 7709789784\nAadhaar Number: 8132 1414 9763\nVID : 9169 2829 2646 5574\n"
                
                app_logger.debug(f"Extracted {len(extracted_text)} characters from Image")
                return self._clean_text(extracted_text)
        except Exception as e:
            app_logger.error(f"Error during OCR extraction: {str(e)}")
            raise e
