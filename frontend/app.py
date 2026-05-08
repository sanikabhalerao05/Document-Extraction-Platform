import streamlit as st
import time
import os
import sys

# Add the project root to the python path so it can find the 'frontend' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.api_client import APIClient

# Initialize API Client
api_client = APIClient(base_url="http://localhost:8000/api/v1")

# Page Configuration
st.set_page_config(
    page_title="Intelligent Document Extraction",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    local_css("frontend/assets/style.css")
except FileNotFoundError:
    pass

st.markdown('<div style="text-align: center; margin-bottom: 3rem; animation: fadeIn 0.8s ease-out;">', unsafe_allow_html=True)
st.title("📄 Document AI")
st.markdown("<p style='font-size: 1.2rem; color: #94a3b8; max-width: 600px; margin: 0 auto; line-height: 1.6;'>Automate data extraction from Aadhaar, Driving Licences, Passports, and Invoices using Next-Gen OCR & Artificial Intelligence.</p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Sidebar for settings / history
with st.sidebar:
    st.header("Upload Document")
    doc_type = st.selectbox(
        "Select Document Type",
        ["Aadhaar Card", "Driving Licence", "Passport", "Invoice", "Unknown"]
    )
    
    # Map selection to backend enum
    type_map = {
        "Aadhaar Card": "aadhaar",
        "Driving Licence": "dl",
        "Passport": "passport",
        "Invoice": "invoice",
        "Unknown": "unknown"
    }
    selected_type_enum = type_map[doc_type]

    uploaded_file = st.file_uploader("Upload Document (JPG, PNG, PDF)", type=['jpg', 'jpeg', 'png', 'pdf'])

    if st.button("Extract Data", type="primary", use_container_width=True) and uploaded_file is not None:
        with st.spinner("Processing document..."):
            # Save file temporarily to send via httpx
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            try:
                # Upload to backend
                doc_record = api_client.upload_document(temp_path, selected_type_enum)
                st.session_state.current_doc_id = doc_record["id"]
                st.success("Document uploaded successfully! Extraction started.")
            except Exception as e:
                st.error(f"Failed to upload: {str(e)}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

# Main Dashboard Area
col1, col2 = st.columns([1, 1])

if "current_doc_id" in st.session_state:
    doc_id = st.session_state.current_doc_id
    
    # Polling for completion
    with st.spinner("Waiting for extraction to complete..."):
        for _ in range(15): # Poll for up to 30 seconds
            try:
                doc_details = api_client.get_document_details(doc_id)
                if doc_details["status"] == "completed":
                    break
                elif doc_details["status"] == "failed":
                    st.error("Document extraction failed.")
                    break
            except Exception:
                pass
            time.sleep(2)
            
    doc_details = api_client.get_document_details(doc_id)
    
    with col1:
        st.subheader("Document Details")
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.4); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <p style="margin: 0 0 10px 0; font-size: 1.05rem;"><strong style="color: #a78bfa; margin-right: 8px;">Filename:</strong> <span style="color: #f1f5f9;">{doc_details['filename']}</span></p>
            <p style="margin: 0 0 10px 0; font-size: 1.05rem;"><strong style="color: #a78bfa; margin-right: 8px;">Status:</strong> <span style="color: #10b981;">{doc_details['status'].capitalize()}</span></p>
            <p style="margin: 0; font-size: 1.05rem;"><strong style="color: #a78bfa; margin-right: 8px;">Uploaded At:</strong> <span style="color: #94a3b8;">{doc_details['uploaded_at'].replace('T', ' ')[:16]}</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        if doc_details.get("extracted_data"):
            st.subheader("Raw Extracted Text")
            
            # Clean up messy OCR text: remove empty lines and strip excess whitespace
            raw_text = doc_details["extracted_data"]["extracted_text"]
            clean_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            clean_text = "\n".join(clean_lines)
            
            # Use st.code for a native, clean, monospaced view that safely handles special characters
            st.code(clean_text, language="text")

    with col2:
        st.subheader("Structured Extracted Data")
        if doc_details.get("extracted_data") and doc_details["extracted_data"].get("parsed_json"):
            parsed_data = doc_details["extracted_data"]["parsed_json"]
            
            # Display nicely instead of just JSON
            for key, value in parsed_data.items():
                if key != "raw_text_length":
                    st.metric(label=key.replace("_", " ").title(), value=str(value))
                    
            with st.expander("View Raw JSON"):
                st.json(parsed_data)
        elif doc_details["status"] == "completed":
            st.warning("Extraction completed but no structured data was returned.")
        else:
            st.info("Still processing or failed...")

st.markdown("---")
st.subheader("Recent Documents")
try:
    recent_docs = api_client.get_documents(limit=5)
    if recent_docs:
        # Header row
        header_cols = st.columns([3, 2, 2, 3, 2])
        header_cols[0].markdown("**Filename**")
        header_cols[1].markdown("**Type**")
        header_cols[2].markdown("**Status**")
        header_cols[3].markdown("**Uploaded At**")
        header_cols[4].markdown("**Action**")
        
        for doc in recent_docs:
            row_cols = st.columns([3, 2, 2, 3, 2])
            row_cols[0].write(doc["filename"])
            row_cols[1].write(doc["document_type"].title())
            row_cols[2].write(doc["status"].capitalize())
            
            # Format datetime nicely if possible
            up_time = doc["uploaded_at"].replace("T", " ")[:16]
            row_cols[3].write(up_time)
            
            if row_cols[4].button("Delete", key=f"del_{doc['id']}", type="secondary"):
                try:
                    api_client.delete_document(doc['id'])
                    if st.session_state.get("current_doc_id") == doc['id']:
                        del st.session_state["current_doc_id"]
                    st.rerun()
                except Exception as e:
                    st.error("Failed to delete document")
    else:
        st.info("No documents processed yet.")
except Exception as e:
    st.error("Could not fetch recent documents. Is the backend running?")
