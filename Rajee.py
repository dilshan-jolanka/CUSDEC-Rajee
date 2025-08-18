import streamlit as st
import requests
import json
import pdfplumber
from dotenv import load_dotenv
import os
import re
import pandas as pd
import io
import base64
from datetime import datetime, timezone

COMPANY_NAME = "Jolanka Group"
COMPANY_SLOGAN = "Innovative Customs Data Solutions"
COMPANY_LOGO_URL = "https://jolankagroup.com/wp-content/themes/jolanka/assets/images/icons/jolanka-logo-no-text.png"

# --- Custom CSS for AI Robot Theme + Beautiful Table and Button ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@400;700&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Roboto', Arial, sans-serif;
        background: linear-gradient(120deg, #eaf6fb 0%, #f6fafd 100%);
    }}
    .ai-logo {{
        text-align:center;
        margin-bottom: 6px;
        margin-top: -14px;
    }}
    .ai-header {{
        background: linear-gradient(90deg, #1877c1 0%, #00d4ff 100%);
        color: white;
        border-radius: 14px;
        margin-top: 6px;
        margin-bottom: 18px;
        padding: 10px 0 2px 0;
        box-shadow: 0 6px 18px 0 rgba(24,119,193,0.13);
    }}
    .ai-header-title {{
        font-size: 2.1rem;
        font-family: 'Orbitron', 'Roboto', sans-serif;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-align: center;
        margin-bottom: 2px;
        margin-top: 2px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.07);
    }}
    .ai-header-subtitle {{
        font-size: 1.01rem;
        font-weight: 400;
        letter-spacing: 0.5px;
        text-align: center;
        margin-top: 2px;
        margin-bottom: 4px;
        color: #e2f6ff;
    }}
    .company-sub {{
        font-size: 1.08rem;
        color: #fff;
        font-weight: 700;
        letter-spacing: 1.1px;
        text-align: center;
        margin-bottom: 2px;
        margin-top: 0px;
        text-shadow: 0 1px 8px #00d4ff44;
    }}
    .ai-info-box {{
        background: linear-gradient(90deg,#fff9e6 60%, #e2f6ff 100%);
        color: #b05a00;
        box-shadow: 0 2px 12px 0 #f7d38b30;
        border-radius: 13px;
        font-size: 1.12rem;
        font-weight: 500;
        margin: 14px 0 28px 0;
        padding: 12px 18px 12px 18px;
        display: flex;
        align-items: center;
        gap: 14px;
    }}
    .ai-info-icon {{
        font-size: 1.4rem;
        margin-right: 7px;
        vertical-align: middle;
    }}
    /* Table styling below */
    .stDataFrame, .custom-table {{
        background: #ffffffcc;
        border-radius: 16px;
        box-shadow: 0 4px 28px 0 #1877c115;
        padding: 20px 12px;
        margin-bottom: 18px;
        font-size: 1.07rem;
    }}
    .custom-table table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        overflow: hidden;
        border-radius: 12px;
        background: #f9fbfd;
    }}
    .custom-table th {{
        background: linear-gradient(90deg,#1877c1 0%, #00d4ff 100%);
        color: #fff;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 12px 14px;
        border-bottom: 2px solid #b3daff;
    }}
    .custom-table td {{
        padding: 10px 14px;
        background: #f4fafd;
        border-bottom: 1px solid #eaf3fc;
    }}
    .custom-table tr:last-child td {{
        border-bottom: none;
    }}
    /* Beautiful button */
    .stButton>button {{
        background: linear-gradient(90deg, #22c1c3 0%, #1877c1 100%);
        color: white;
        border-radius: 22px;
        border: none;
        font-weight: 700;
        font-size: 1.18rem;
        padding: 13px 36px;
        margin-top: 12px;
        margin-bottom: 6px;
        transition: box-shadow 0.2s, transform 0.15s;
        box-shadow: 0 2px 14px 0 #1877c133, 0 2px 8px 0 #22c1c322;
        outline: none;
    }}
    .stButton>button:hover {{
        background: linear-gradient(90deg, #1877c1 0%, #22c1c3 100%);
        color: #fff;
        transform: translateY(-2px) scale(1.04);
        box-shadow: 0 6px 20px 0 #22c1c344;
    }}
    
    </style>
""", unsafe_allow_html=True)

# --- Company Logo (small up) ---
st.markdown(
    f'<div class="ai-logo"><img src="{COMPANY_LOGO_URL}" width="80"></div>',
    unsafe_allow_html=True
)

# --- Compact AI Robot Header with Company Name ---
st.markdown(f'''
    <div class="ai-header">
        <div class="ai-header-title">🤖 CUSDEC II Data Extractor (Multi-PDF)</div>
        <div class="ai-header-subtitle">
            Upload one or more CUSDEC II PDFs to extract <b>specific data fields</b> from the first page of each.<br>
            <span class="company-sub">{COMPANY_NAME}</span>
        </div>
    </div>
''', unsafe_allow_html=True)

# --- AI Info Box ---
st.markdown(f'''
    <div class="ai-info-box">
        <span class="ai-info-icon">⚠️</span>
        <span>AI-powered extraction may make mistakes.<br><b>Always double-check extracted data.</b></span>
    </div>
''', unsafe_allow_html=True)

# Load environment variables from .env file
load_dotenv()

# Gemini API Configuration
gemini_api_key = os.getenv("GOOGLE_API_KEY")
if not gemini_api_key:
    st.error("Gemini API key not found. Please set GOOGLE_API_KEY in your .env file.")
    st.stop()

gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def generate_content(prompt):
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(f"{gemini_endpoint}?key={gemini_api_key}", headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling Gemini API: {e}")
        return None

def extract_page_from_pdf(pdf_file_bytes):
    """Extract the first page from PDF bytes"""
    try:
        with pdfplumber.open(io.BytesIO(pdf_file_bytes)) as pdf:
            if len(pdf.pages) > 0:
                return pdf.pages[0]
            else:
                return None
    except Exception:
        return None

def parse_customs_reference(raw_customs_ref):
    """Parse customs reference to extract type and numbers"""
    if not raw_customs_ref:
        return "", []
    lines = [line.strip() for line in raw_customs_ref.splitlines() if line.strip()]
    if not lines:
        return "", []
    ref_type = ""
    ref_numbers = []
    # For every line, extract only the number part
    for idx, line in enumerate(lines):
        match = re.match(r"([A-Za-z])?\s*(\d+)", line)
        if match:
            if idx == 0 and match.group(1):
                ref_type = match.group(1)
            ref_numbers.append(match.group(2))
        else:
            ref_numbers.append(line)
    return ref_type, ref_numbers

def extract_customs_reference_date(document_text, raw_customs_ref):
    """Extract date in DD/MM/YYYY format from document"""
    date_pattern = r"(\b\d{2}/\d{2}/\d{4}\b)"
    if raw_customs_ref:
        # Find all matches in the document, take the one nearest to customs ref block if possible
        matches = list(re.finditer(date_pattern, document_text))
        if matches:
            # Try to use the first one after the customs ref block
            ref_pos = document_text.find(raw_customs_ref)
            for m in matches:
                if m.start() > ref_pos:
                    return m.group(1)
            # fallback to first date found
            return matches[0].group(1)
    else:
        match = re.search(date_pattern, document_text)
        if match:
            return match.group(1)
    return ""

def extract_data_fields(file_bytes, filename):
    """Extract data from PDF bytes with improved error handling"""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if len(pdf.pages) > 0:
                page = pdf.pages[0]
            else:
                return {"error": f"PDF file {filename} contains no pages."}
            document_text = page.extract_text()
    except Exception as e:
        st.write(f"Debug - PDF Error: {type(e).__name__}: {str(e)}")
        return {"error": f"Error extracting page from PDF ({filename}): {e}"}

    if not document_text:
        return {"error": f"No text could be extracted from the first page of {filename}."}

    # Custom bbox for additional fields (can be adjusted as needed)
    specific_box_coords = {
        "Customs Reference Code E Value": (600, 40, 680, 60),
        "Declarant Sequence Number Value": (650, 110, 800, 130),
        "Box 11 Value": (170, 100, 250, 130),
        "Box 31 Description Value": (550, 300, 800, 450),
        "Box 31 Full Text": (400, 280, 800, 480),
        "D.Val Value": (450, 500, 550, 530),
        "D.Qty Value": (580, 500, 680, 530),
    }

    specific_box_texts = {}
    for box_name, bbox in specific_box_coords.items():
        try:
            extracted_text = page.extract_text(bbox=bbox)
            specific_box_texts[box_name] = extracted_text.strip() if extracted_text else ""
        except Exception:
            specific_box_texts[box_name] = ""

    specific_text_prompt = ""
    if "Customs Reference Code E Value" in specific_box_texts:
        specific_text_prompt += f"Text found in the approximate region of Customs Reference Code E (e.g., CBBE1): \"{specific_box_texts['Customs Reference Code E Value']}\"\n"
    if "Declarant Sequence Number Value" in specific_box_texts:
        specific_text_prompt += f"Text found in the approximate region of Declarant's Sequence Number (e.g., 2024 #3041): \"{specific_box_texts['Declarant Sequence Number Value']}\"\n"
    if "Box 11 Value" in specific_box_texts:
        specific_text_prompt += f"Text found in the approximate region of Box 11 value: \"{specific_box_texts['Box 11 Value']}\"\n"
    if "Box 31 Description Value" in specific_box_texts:
        specific_text_prompt += f"Text found in the approximate region of Box 31 Description value: \"{specific_box_texts['Box 31 Description Value']}\"\n"
    if "Box 31 Full Text" in specific_box_texts:
         specific_text_prompt += f"Full text found in the approximate region of Box 31: \"{specific_box_texts['Box 31 Full Text']}\"\n"
    if "D.Val Value" in specific_box_texts:
         specific_text_prompt += f"Text found in the approximate region of D.Val value: \"{specific_box_texts['D.Val Value']}\"\n"
    if "D.Qty Value" in specific_box_texts:
         specific_text_prompt += f"Text found in the approximate region of D.Qty value: \"{specific_box_texts['D.Qty Value']}\"\n"

    # Map for field extraction
    common_fields_map = {
        "Customs Reference Code E": "Customs Reference Code E",
        "Customs Reference Number": "Customs Reference Number",
        "Declarant Sequence Number": "Declarant's Sequence Number",
        "Box 2": "Box 2: Exporter",
        "Box 8": "Box 8: Consignee",
        "Box 9": "Box 9: Person Responsible for Financial Settlement",
        "Box 11": "Box 11: Trading",
        "Box 14": "Box 14: Declarant/Representative",
        "Box 15": "Box 15: Country of Export",
        "Box 16": "Box 16: Country of origin",
        "Box 18": "Box 18: Vessel/Flight",
        "Box 20": "Box 20: Delivery Terms",
        "Box 22": "Box 22: Currency & Total Amount Invoiced",
        "Box 23": "Box 23: Exchange Rate",
        "Box 28": "Box 28: Financial and banking data",
        "Guarantee LKR": "Guarantee LKR",
        "Box 31": "Box 31: Description",
        "Marks & Nos of Packages": "Marks & Nos of Packages",
        "Number & Kind": "Number & Kind",
        "Box 33": "Box 33: Commodity (HS) Code",
        "Box 35": "Box 35: Gross Mass (Kg)",
        "Box 38": "Box 38: Net Mass (Kg)",
        "D.Val": "D.Val",
        "D.Qty": "D.Qty",
    }
    fields_to_extract_prompt_list = list(common_fields_map.values())
    fields_to_extract_prompt = "\n".join([f"- {name}" for name in fields_to_extract_prompt_list])

    prompt = f"""Analyze the following text from the first page of a SRI LANKA CUSTOMS-GOODS DECLARATION (CUSDEC II) document.
{specific_text_prompt}
Extract the following specific fields. For each field, look for the associated label and extract the value next to it.
For 'Customs Reference Code E', use the text provided from its approximate region (e.g., CBBE1).
For 'Customs Reference Number', extract all reference numbers (e.g., E 72766, E 76315, etc.) and keep the original lines.
For 'Declarant's Sequence Number', use the text provided from its approximate region (e.g., 2024 #3041).
For 'Marks & Nos of Packages', 'Number & Kind', and 'Description', extract the relevant text block under Box 31 and split according to the sublabels.
Return fields in "FieldName: FieldValue" format. Use FieldName exactly as specified below.
Common Fields to Extract:
{fields_to_extract_prompt.strip()}
If a field is not found, indicate 'Not Found'.
Document text:
{document_text}"""

    # Call Gemini API with retry mechanism
    attempts = 0
    max_attempts = 2
    response = None
    
    while attempts < max_attempts:
        response = generate_content(prompt)
        if response and "candidates" in response and len(response['candidates']) > 0:
            break
        attempts += 1
        # Small delay between attempts
        import time
        time.sleep(1)
    
    common_data = {}
    extracted_text_response = ""
    
    if response and "candidates" in response and len(response['candidates']) > 0:
        content_part = response['candidates'][0]['content']['parts'][0]
        if 'text' in content_part:
            extracted_text_response = content_part['text']
            for line in extracted_text_response.strip().split('\n'):
                line = line.strip()
                if ": " in line:
                    parts = line.split(": ", 1)
                    if len(parts) == 2:
                        gemini_key, value = parts[0].strip(), parts[1].strip()
                        display_key = None
                        for key_from_map, val_from_map in common_fields_map.items():
                            if key_from_map == gemini_key or val_from_map == gemini_key:
                                display_key = val_from_map
                                break
                        if display_key:
                            cleaned_value = value.strip()
                            potential_prefixes = []
                            if gemini_key:
                                potential_prefixes.extend([f"{gemini_key}:", f"{gemini_key} :", f"{gemini_key} "])
                                gemini_key_parts = re.split(r'[:\s]+', gemini_key)
                                for part in gemini_key_parts:
                                    if part: potential_prefixes.extend([f"{part}:", f"{part} :", f"{part} "])
                            if display_key:
                                potential_prefixes.extend([f"{display_key}:", f"{display_key} :", f"{display_key} "])
                                display_key_parts = re.split(r'[:\s]+', display_key)
                                for part_dp in display_key_parts:
                                    if part_dp: potential_prefixes.extend([f"{part_dp}:", f"{part_dp} :", f"{part_dp} "])
                            potential_prefixes = sorted(list(set(potential_prefixes)), key=len, reverse=True)
                            for prefix in potential_prefixes:
                                if re.match(re.escape(prefix), cleaned_value, re.IGNORECASE):
                                    cleaned_value = cleaned_value[len(prefix):].strip(); break
                            common_data[display_key] = cleaned_value

    # Declarant's Sequence Number split
    full_dsn = common_data.pop("Declarant's Sequence Number", "")
    dsn_year = ""
    dsn_identifier = ""
    if full_dsn:
        match = re.match(r"(\d{4})\s*(.*)", full_dsn.strip())
        if match:
            dsn_year = match.group(1)
            dsn_identifier = match.group(2).strip()
        else:
            parts = full_dsn.split(" ", 1)
            dsn_year = parts[0]
            if len(parts) > 1:
                dsn_identifier = parts[1]
            else:
                if full_dsn.startswith("#") or not full_dsn.replace(" ","").isalnum():
                    dsn_identifier = full_dsn
                    dsn_year = ""
                else:
                    dsn_year = full_dsn
    common_data["Declarant Sequence Year"] = dsn_year
    common_data["Declarant Sequence Identifier"] = dsn_identifier

    # Customs Reference Number: Remove the type letter from all numbers
    raw_customs_ref = common_data.pop("Customs Reference Number", "")
    customs_ref_type, customs_ref_numbers = parse_customs_reference(raw_customs_ref)
    custom_ref_number_str = "\n".join(customs_ref_numbers) if customs_ref_numbers else ""
    common_data["Customs Reference Type"] = customs_ref_type
    common_data["Customs Reference Number"] = custom_ref_number_str

    # Customs Reference Date: Extract from the document near the Customs Reference Number
    customs_reference_date = extract_customs_reference_date(document_text, raw_customs_ref)
    common_data["Customs Reference Date"] = customs_reference_date

    # Box 35 and 38: Remove "Mass (Kg):" prefix
    for mass_key in ["Box 35: Gross Mass (Kg)", "Box 38: Net Mass (Kg)"]:
        val = common_data.get(mass_key, "")
        if val:
            cleaned_val = re.sub(r"Mass \(Kg\):\s*", "", val)
            common_data[mass_key] = cleaned_val

    # Box 22: Currency & Total Amount Invoiced
    box22_val = common_data.get("Box 22: Currency & Total Amount Invoiced", "")
    currency, total_amount = "", ""
    if box22_val:
        # Remove "& Total Amount Invoiced:" prefix
        box22_val = re.sub(r"& Total Amount Invoiced:\s*", "", box22_val)
        # Try to extract currency and amount
        match = re.match(r"([A-Z]{3})\s*([\d,]+\.\d{2})", box22_val)
        if match:
            currency = match.group(1)
            total_amount = match.group(2)
        else:
            # fallback: if only amount
            total_amount = box22_val
    common_data["Currency"] = currency
    common_data["Total Amount Invoiced"] = total_amount

    return common_data

# Function to create a download link for Excel file that doesn't require page refresh
def get_excel_download_link(df, filename="data.xlsx"):
    """
    Generates a link to download the excel file without needing page refresh
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='All Extracted Data', index=False)
        # Auto-adjust columns' width
        worksheet = writer.sheets['All Extracted Data']
        for i, col in enumerate(df.columns):
            # Find the maximum length of the column content
            column_len = max(df[col].astype(str).map(len).max(), len(col))
            # Add a little extra space
            column_len = min(column_len + 2, 50)  # Cap at 50 to prevent overly wide columns
            worksheet.set_column(i, i, column_len)
    
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    
    download_link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="download-button">Download Excel File</a>'
    
    return download_link

def main():
    current_user_login = "dilshan-jolanka" 

    # Initialize session state for stable file handling
    if 'cached_uploaded_files' not in st.session_state:
        st.session_state['cached_uploaded_files'] = {}
    
    if 'all_extracted_data' not in st.session_state:
        st.session_state.all_extracted_data = []
        
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
        
    if 'download_link' not in st.session_state:
        st.session_state.download_link = None

    # File upload area
    uploaded_files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)

    # Process the uploaded files
    if uploaded_files:
        # Cache uploaded files in session state for stability
        for file in uploaded_files:
            if file.name not in st.session_state['cached_uploaded_files']:
                file_bytes = file.read()
                # Check if this is a valid PDF by trying to open it
                try:
                    with pdfplumber.open(io.BytesIO(file_bytes)):
                        st.session_state['cached_uploaded_files'][file.name] = file_bytes
                except Exception as e:
                    st.error(f"Error loading {file.name}: {e}")
                    
        # Confirm number of PDFs
        st.write(f"{len(st.session_state['cached_uploaded_files'])} PDF(s) cached.")
        
        # Process button
        if st.button("Extract Data from All Uploaded PDFs"):
            processing_start_time_utc_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.all_extracted_data = [] 
            st.session_state.processing_complete = False
            
            with st.spinner("Extracting data from all PDFs..."):
                for filename, file_bytes in st.session_state['cached_uploaded_files'].items():
                    # Create a placeholder for each file being processed
                    file_placeholder = st.empty()
                    file_placeholder.write(f"Processing {filename}...")
                    
                    # Process the file with improved error handling
                    try:
                        common_data_from_extraction = extract_data_fields(file_bytes, filename)
                        st.session_state.all_extracted_data.append({
                            "filename": filename,
                            "data": common_data_from_extraction,
                            "processing_datetime_utc": processing_start_time_utc_str,
                            "processed_by_user": current_user_login
                        })
                        file_placeholder.write(f"✅ Processed {filename}")
                    except Exception as e:
                        st.error(f"Error processing {filename}: {str(e)}")
                        # Still add an error entry to keep track of all files
                        st.session_state.all_extracted_data.append({
                            "filename": filename,
                            "data": {"error": f"Processing error: {str(e)}"},
                            "processing_datetime_utc": processing_start_time_utc_str,
                            "processed_by_user": current_user_login
                        })
                        file_placeholder.write(f"❌ Failed to process {filename}")
                        
            st.success("Data extraction complete for all files!")
            st.session_state.processing_complete = True

    # Display section - define column order
    excel_column_order = [
        "Source File", 
        "Customs Reference Code E", 
        "Customs Reference Type",
        "Customs Reference Number",
        "Customs Reference Date",
        "Declarant Sequence Year",
        "Declarant Sequence Identifier",
        "Box 2: Exporter",
        "Box 8: Consignee",
        "Box 9: Person Responsible for Financial Settlement",
        "Box 11: Trading",
        "Box 14: Declarant/Representative",
        "Box 15: Country of Export",
        "Box 16: Country of origin",
        "Box 18: Vessel/Flight",
        "Box 20: Delivery Terms",
        "Currency",
        "Total Amount Invoiced",
        "Box 23: Exchange Rate",
        "Box 28: Financial and banking data",
        "Guarantee LKR", 
        "Box 31: Description",
        "Marks & Nos of Packages",
        "Number & Kind",
        "Box 33: Commodity (HS) Code",
        "Box 35: Gross Mass (Kg)", 
        "Box 38: Net Mass (Kg)",
        "D.Val", 
        "D.Qty",
    ]

    common_fields_to_display_in_ui = [field for field in excel_column_order if field != "Source File"]

    # Display extracted data
    if st.session_state.all_extracted_data:
        st.markdown("---")
        for item_idx, item in enumerate(st.session_state.all_extracted_data):
            filename = item["filename"]
            data_for_file = item["data"]
            proc_datetime = item.get("processing_datetime_utc", "N/A")
            proc_user = item.get("processed_by_user", "N/A")

            st.markdown(f'<h2 class="sub-title">Extracted Data for: {filename}</h2>', unsafe_allow_html=True)
            st.markdown(f'<p class="info-text">Processed on: {proc_datetime} (UTC) by {proc_user}</p>', unsafe_allow_html=True)
            
            if "error" in data_for_file:
                st.error(data_for_file["error"])
                st.markdown("---")
                continue
                
            if isinstance(data_for_file, dict) and data_for_file.get("error"):
                st.error(f"Extraction error for {filename}: {data_for_file.get('error')}")
                st.markdown("---")
                continue

            # Display data in 3 columns
            col1, col2, col3 = st.columns(3)
            for field_idx, field in enumerate(common_fields_to_display_in_ui):
                field_value = data_for_file.get(field, "")
                sanitized_field_name = re.sub(r'[^A-Za-z0-9_]', '', field)
                unique_key = f"file{item_idx}_field{field_idx}_{sanitized_field_name}"
                
                if field_idx % 3 == 0:
                    with col1: st.text_input(field, value=field_value, key=unique_key, disabled=True)
                elif field_idx % 3 == 1:
                    with col2: st.text_input(field, value=field_value, key=unique_key, disabled=True)
                else:
                    with col3: st.text_input(field, value=field_value, key=unique_key, disabled=True)
                    
            st.markdown("---")

        # Create Excel file for download
        if st.session_state.processing_complete:
            all_files_rows_for_excel = []

            for item in st.session_state.all_extracted_data:
                filename = item["filename"]
                data_for_file = item["data"]

                row_data = {"Source File": filename}
                
                # Handle error cases
                is_error_state = isinstance(data_for_file, str) or (isinstance(data_for_file, dict) and "error" in data_for_file)
                if is_error_state:
                    error_message = data_for_file if isinstance(data_for_file, str) else data_for_file.get("error", "Unknown extraction error")
                    row_data["Declarant Sequence Year"] = f"ERROR: {error_message}"
                    for field_name in excel_column_order:
                        if field_name not in row_data:
                             row_data[field_name] = "N/A due to error" if field_name != "Source File" else row_data.get(field_name)
                else:
                    # Normal case - add all fields
                    for field_name in excel_column_order:
                        if field_name != "Source File":
                            row_data[field_name] = data_for_file.get(field_name, "")
                
                all_files_rows_for_excel.append(row_data)
            
            if all_files_rows_for_excel:
                # Create DataFrame for Excel
                df_export = pd.DataFrame(all_files_rows_for_excel)
                
                # Ensure all columns exist, even if empty
                for col in excel_column_order:
                    if col not in df_export.columns:
                        df_export[col] = ""
                
                # Order columns correctly
                df_export = df_export[excel_column_order]
                
                # Create the download link that doesn't require page refresh
                st.markdown("""
                    <style>
                    .download-button {
                        display: inline-block;
                        padding: 12px 24px;
                        background: linear-gradient(90deg, #22c1c3 0%, #1877c1 100%);
                        color: white !important;
                        text-decoration: none;
                        font-weight: bold;
                        border-radius: 22px;
                        margin-top: 20px;
                        text-align: center;
                        box-shadow: 0 2px 14px 0 #1877c133;
                        transition: all 0.3s ease;
                    }
                    .download-button:hover {
                        background: linear-gradient(90deg, #1877c1 0%, #22c1c3 100%);
                        box-shadow: 0 4px 20px 0 #1877c155;
                        transform: translateY(-2px);
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # Generate the download link
                download_link = get_excel_download_link(df_export, "all_cusdec_extracted_data.xlsx")
                st.session_state.download_link = download_link
                
                # Display the download link
                st.markdown(download_link, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
