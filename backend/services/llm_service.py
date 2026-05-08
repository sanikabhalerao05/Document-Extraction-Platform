import json
import re
import datetime
from typing import Dict, Any
from backend.core.logging import app_logger
from backend.core.config import settings

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        app_logger.info(f"Initializing LLMService with provider: {self.provider}")

    def format_cleaned_text(self, parsed_json: Dict[str, Any]) -> str:
        """Converts structured JSON back into a clean, human-readable text block."""
        data = parsed_json.get("extracted_data", {})
        meta = parsed_json.get("metadata", {})
        doc_type_str = meta.get("document_type", "").lower()
        
        lines = []
        if "aadhaar" in doc_type_str:
            if data.get("name") and data["name"] != "Unknown": lines.append(f"Name: {data['name']}")
            if data.get("dob") and data["dob"] != "Not Found": lines.append(f"DOB: {data['dob']}")
            if data.get("gender") and data["gender"] != "Not Found": lines.append(f"Gender: {data['gender']}")
            if data.get("mobile_no") and data["mobile_no"] != "Not Found": lines.append(f"Mobile No: {data['mobile_no']}")
            if data.get("aadhaar_number") and data["aadhaar_number"] != "Not Found": lines.append(f"Aadhaar Number: {data['aadhaar_number']}")
            if data.get("vid") and data["vid"] != "Not Found": lines.append(f"VID : {data['vid']}")
            if data.get("address") and data["address"] != "Not Found":
                lines.append("Address :")
                # Indent address lines slightly if they are multiline
                addr = data["address"].replace(", ", "\n")
                lines.append(addr)
            
            # Duplicate ID/VID at bottom as per sample requirement
            if data.get("aadhaar_number") and data["aadhaar_number"] != "Not Found": lines.append(data["aadhaar_number"])
            if data.get("vid") and data["vid"] != "Not Found": lines.append(f"VID : {data['vid']}")
            
        elif "invoice" in doc_type_str:
            if data.get("vendor"): lines.append(f"Vendor: {data['vendor']}")
            if data.get("invoice_number"): lines.append(f"Invoice #: {data['invoice_number']}")
            if data.get("invoice_date"): lines.append(f"Date: {data['invoice_date']}")
            if data.get("total_amount"): lines.append(f"Total Amount: {data['total_amount']}")
            if data.get("tax_amount"): lines.append(f"Tax: {data['tax_amount']}")
            if data.get("currency"): lines.append(f"Currency: {data['currency']}")
        
        elif "licence" in doc_type_str:
            if data.get("name"): lines.append(f"Name: {data['name']}")
            if data.get("licence_number"): lines.append(f"DL No: {data['licence_number']}")
            if data.get("dob"): lines.append(f"DOB: {data['dob']}")
            if data.get("valid_upto"): lines.append(f"Valid Upto: {data['valid_upto']}")
            if data.get("address"): lines.append(f"Address: {data['address']}")
            
        elif "passport" in doc_type_str:
            if data.get("given_name"): lines.append(f"Given Name: {data['given_name']}")
            if data.get("surname"): lines.append(f"Surname: {data['surname']}")
            if data.get("passport_number"): lines.append(f"Passport No: {data['passport_number']}")
            if data.get("dob"): lines.append(f"DOB: {data['dob']}")
            if data.get("gender"): lines.append(f"Gender: {data['gender']}")
            if data.get("nationality"): lines.append(f"Nationality: {data['nationality']}")
            if data.get("date_of_expiry"): lines.append(f"Expiry: {data['date_of_expiry']}")
        
        else:
            # Fallback for unknown documents
            for k, v in data.items():
                if v and v != "Not Found":
                    lines.append(f"{k.replace('_', ' ').capitalize()}: {v}")
                
        return "\n".join(lines)

    def extract_structured_data(self, text: str, doc_type: str) -> Dict[str, Any]:
        app_logger.debug(f"Extracting structured data for doc_type: {doc_type}")
        
        if self.provider == "mock":
            return self._mock_extraction(text, doc_type)
        else:
            # Here you would integrate with OpenAI or a local LLM via LangChain/LiteLLM
            # For demonstration, we fall back to mock if real integration isn't fully implemented yet
            app_logger.warning("Real LLM provider called but not fully implemented, falling back to mock")
            return self._mock_extraction(text, doc_type)

    def _mock_extraction(self, text: str, doc_type: str) -> Dict[str, Any]:
        # Simple heuristic-based mock extraction based on doc_type
        text_lower = text.lower()
        
        # Organized structure
        result = {
            "metadata": {
                "document_type": doc_type.capitalize(),
                "extraction_method": "mock_heuristic",
                "processed_at": datetime.datetime.now().isoformat()
            },
            "extracted_data": {}
        }
        
        # Common pattern matches
        dob_match = re.search(r'DOB[:\s/]*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
        gender_match = re.search(r'(MALE|FEMALE)', text, re.IGNORECASE)
        
        if doc_type == "aadhaar":
            result["metadata"]["document_type"] = "Aadhaar Card"
            
            # Extract specific fields using refined patterns
            mobile_match = re.search(r'Mobile No[:\s]*(\d{10})', text, re.IGNORECASE)
            # Improved regex for Aadhaar (12 digits) and VID (16 digits) with flexible spacing
            # Use negative lookahead to ensure Aadhaar doesn't match the start of a longer VID
            aadhaar_match = re.search(r'\b(\d{4}\s?\d{4}\s?\d{4})\b(?!\s?\d{4})', text)
            
            # Look for VID (16 digits), either with the VID keyword or just by length
            vid_match = re.search(r'VID\s*[:\s]*\b(\d{4}\s?\d{4}\s?\d{4}\s?\d{4})\b', text, re.IGNORECASE)
            if not vid_match:
                vid_match = re.search(r'\b(\d{4}\s?\d{4}\s?\d{4}\s?\d{4})\b', text)
            
            # Smart Name Extraction: Look for the line above the DOB or a clean line near the top
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 3]
            name = "Unknown"
            
            # Find the index of the DOB line
            dob_idx = -1
            for i, line in enumerate(lines):
                if "DOB" in line.upper() or ("/" in line and re.search(r'\d{2}/\d{2}/\d{4}', line)):
                    dob_idx = i
                    break
            
            # If DOB found, the name is usually the line right above it
            if dob_idx > 0:
                potential_name = lines[dob_idx - 1]
                # Filter out garbage keywords often found in OCR
                if not any(word in potential_name.upper() for word in ["GOVERNMENT", "INDIA", "UNIQUE", "AUTHORITY"]):
                    name = potential_name
            
            if name == "Unknown":
                # Fallback: Look for a clean line at the top that isn't noise
                for line in lines[:5]:
                    if not any(c.isdigit() for c in line) and len(line.split()) >= 2:
                        # Add common OCR noise words to skip
                        if not any(word in line.upper() for word in ["DOB", "GENDER", "MOBILE", "ADDRESS", "THT", "AIDS", "TEA"]):
                            name = line
                            break

            # Extract Address
            address = "Not Found"
            clean_addr = []
            if "Address" in text:
                addr_part = text.split("Address")[-1].strip()
                addr_lines = [l.strip() for l in addr_part.split('\n') if l.strip()]
                for al in addr_lines:
                    if re.search(r'\d{4}\s?\d{4}\s?\d{4}', al) or "VID" in al.upper() or "HELP@" in al.upper():
                        break
                    if al in [":", ".", "-", ","] or len(al) < 2:
                        continue
                    clean_addr.append(al)
                address = ", ".join(clean_addr[:10])
                
            # Extract Pincode and Geo Info
            pincode_match = re.search(r'\b(\d{6})\b', text)
            state = "Not Found"
            if clean_addr:
                last_addr_line = clean_addr[-1].upper()
                if " - " in last_addr_line:
                    state = last_addr_line.split(" - ")[0].strip()

            result["extracted_data"] = {
                "name": name,
                "dob": dob_match.group(1) if dob_match else "Not Found",
                "gender": gender_match.group(1).upper() if gender_match else "Not Found",
                "mobile_no": mobile_match.group(1) if mobile_match else "Not Found",
                "aadhaar_number": aadhaar_match.group(1) if aadhaar_match else "Not Found",
                "vid": vid_match.group(1) if vid_match else "Not Found",
                "pincode": pincode_match.group(1) if pincode_match else "Not Found",
                "state": state,
                "address": address,
                "full_address_lines": clean_addr
            }
                
        elif doc_type == "dl":
            result["metadata"]["document_type"] = "Driving Licence"
            dl_num = re.search(r'([A-Z]{2}[0-9]{2}\s?[0-9]{11})', text)
            result["extracted_data"] = {
                "licence_number": dl_num.group(1) if dl_num else "DL-MH12-20230001",
                "name": "SAMPLE DRIVER NAME",
                "dob": dob_match.group(1) if dob_match else "01/01/1990",
                "valid_upto": "2040-12-31",
                "address": "SAMPLE ADDRESS, MAHARASHTRA",
                "blood_group": "B+"
            }
            
        elif doc_type == "passport":
            result["metadata"]["document_type"] = "Passport"
            p_num = re.search(r'([A-Z][0-9]{7})', text)
            result["extracted_data"] = {
                "passport_number": p_num.group(1) if p_num else "Z1234567",
                "surname": "RAUT",
                "given_name": "GAURI SANTOSH",
                "nationality": "INDIAN",
                "gender": gender_match.group(1) if gender_match else "FEMALE",
                "dob": dob_match.group(1) if dob_match else "16/03/2003",
                "place_of_birth": "MAHARASHTRA",
                "date_of_issue": "2020-01-01",
                "date_of_expiry": "2030-01-01"
            }
            
        elif doc_type == "invoice":
            result["metadata"]["document_type"] = "Invoice"
            inv_num = re.search(r'(?:inv|invoice|bill)\s*(?:no|#)?[:\s]*([A-Z0-9-]+)', text_lower)
            matches = re.findall(r'(?:total|amount|due|inr|rs\.?|₹)[\s\:\.\-]*[a-z]*[\s\:\.\-]*((?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d{2})?)', text_lower)
            
            result["extracted_data"] = {
                "invoice_number": inv_num.group(1).upper() if inv_num else "INV-2024-001",
                "total_amount": f"₹{matches[-1]}" if matches else "Not Detected",
                "tax_amount": f"₹{matches[0]}" if len(matches) > 1 else "0.00",
                "vendor": "DETECTED VENDOR NAME",
                "invoice_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "currency": "INR"
            }
            
        else:
            result["metadata"]["document_type"] = "Unknown"
            result["extracted_data"]["summary"] = text[:200] + "..." if len(text) > 200 else text

        return result
