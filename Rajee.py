import streamlit as st
import requests
import json
import pdfplumber
from dotenv import load_dotenv
import os
import re
import pandas as pd
import io
from datetime import datetime, timezone

# Load environment variables from .env file
load_dotenv()

# Gemini API Configuration
gemini_api_key = os.getenv("GOOGLE_API_KEY")
if not gemini_api_key:
    st.error("Gemini API key not found. Please set GOOGLE_API_KEY in your .env file.")
    st.stop()

gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# Function to generate content using the Gemini API
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

# Function to read and extract text from a PDF file (only page 1)
def extract_page_from_pdf(pdf_file_object):
    try:
        with pdfplumber.open(pdf_file_object) as pdf:
            if len(pdf.pages) > 0:
                return pdf.pages[0]
            else:
                st.warning(f"PDF file {pdf_file_object.name if hasattr(pdf_file_object, 'name') else 'Unknown'} contains no pages.")
                return None
    except Exception as e:
        st.error(f"Error extracting page from PDF ({pdf_file_object.name if hasattr(pdf_file_object, 'name') else 'Unknown'}): {e}")
        return None

# Function to extract specific data fields from the PDF text using Gemini
def extract_data_fields(pdf_file_object):
    page = extract_page_from_pdf(pdf_file_object)
    filename_for_error = pdf_file_object.name if hasattr(pdf_file_object, 'name') else 'Unknown'
    if page is None:
        return {"error": f"Could not extract page from PDF {filename_for_error} or PDF is empty."}

    document_text = page.extract_text()
    if not document_text:
        st.warning(f"No text could be extracted from the first page of {filename_for_error}.")
        document_text = "" 

    specific_box_coords = {
        "Customs Reference Code E Value": (600, 40, 680, 60),
        "Declarant Sequence Number Value": (650, 110, 800, 130), # This BBox is for the full DSN
        "Box 11 Value": (170, 100, 250, 130),
        "Box 31 Description Value": (550, 300, 800, 450),
        "Box 31 Full Text": (400, 280, 800, 480),
        "D.Val Value": (450, 500, 550, 530),
        "D.Qty Value": (580, 500, 680, 530),
    }

    specific_box_texts = {}
    for box_name, bbox in specific_box_coords.items():
        try:
            if page: 
                 extracted_text = page.extract_text(bbox=bbox)
                 specific_box_texts[box_name] = extracted_text.strip() if extracted_text else ""
            else: 
                specific_box_texts[box_name] = "Page not available"
        except Exception as e:
            st.warning(f"Could not extract text from {box_name} in {filename_for_error} using bbox {bbox}: {e}")
            specific_box_texts[box_name] = "Extraction Failed"
    
    specific_text_prompt = ""
    if "Customs Reference Code E Value" in specific_box_texts:
        specific_text_prompt += f"Text found in the approximate region of Customs Reference Code E (e.g., CBBE1): \"{specific_box_texts['Customs Reference Code E Value']}\"\n"
    # The prompt still refers to the BBox for the full Declarant's Sequence Number
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

    # common_fields_map tells Gemini what to look for. We still ask for the full DSN.
    common_fields_map = {
        "Customs Reference Code E": "Customs Reference Code E",
        "Declarant Sequence Number": "Declarant's Sequence Number", # Gemini extracts this full string
        "Box 2": "Box 2: Exporter", "Box 8": "Box 8: Consignee",
        "Box 9": "Box 9: Person Responsible for Financial Settlement", "Box 11": "Box 11: Trading",
        "Box 14": "Box 14: Declarant/Representative", "Box 15": "Box 15: Country of Export",
        "Box 16": "Box 16: Country of origin", "Box 18": "Box 18: Vessel/Flight",
        "Box 20": "Box 20: Delivery Terms", "Box 22": "Box 22: Currency & Total Amount Invoiced",
        "Box 23": "Box 23: Exchange Rate", "Box 28": "Box 28: Financial and banking data",
        "Customs Reference Number": "Customs Reference Number", "Guarantee LKR": "Guarantee LKR",
        "Box 31": "Box 31: Description", "Box 33": "Box 33: Commodity (HS) Code",
        "Box 35": "Box 35: Gross Mass (Kg)", "Box 38": "Box 38: Net Mass (Kg)",
        "D.Val": "D.Val", "D.Qty": "D.Qty",
    }
    fields_to_extract_prompt_list = list(common_fields_map.values())
    fields_to_extract_prompt = "\n".join([f"- {name}" for name in fields_to_extract_prompt_list])

    prompt = f"""Analyze the following text from the first page of a SRI LANKA CUSTOMS-GOODS DECLARATION (CUSDEC II) document.
{specific_text_prompt}
Extract the following specific fields. For each field, look for the associated label and extract the value next to it.
For 'Customs Reference Code E', use the text provided from its approximate region (e.g., CBBE1).
For 'Declarant's Sequence Number', use the text provided from its approximate region (e.g., 2024 #3041). This is the full sequence number.
For 'Box 11: Trading', use the text from its approximate value region.
For 'Box 31: Description', use text from its approximate value region, ignoring other labels.
For 'D.Val' and 'D.Qty', use text from their approximate regions near Box 44.
Return fields in "FieldName: FieldValue" format. Use FieldName exactly as specified below.
Common Fields to Extract:
{fields_to_extract_prompt.strip()}
If a field is not found, indicate 'Not Found'.
Document text:
{document_text}"""

    response = generate_content(prompt)
    common_data = {} # This will store initially extracted data
    
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
                        # Map Gemini's response key to our internal display key
                        for key_from_map, val_from_map in common_fields_map.items():
                            if key_from_map == gemini_key or val_from_map == gemini_key:
                                display_key = val_from_map # Use the value from map as the consistent key
                                break
                        if display_key:
                            cleaned_value = value.strip()
                            # ... (prefix cleaning logic remains the same)
                            potential_prefixes = []
                            if gemini_key:
                                potential_prefixes.extend([f"{gemini_key}:", f"{gemini_key} :", f"{gemini_key} "])
                                gemini_key_parts = re.split(r'[:\s]+', gemini_key)
                                for part in gemini_key_parts:
                                    if part: potential_prefixes.extend([f"{part}:", f"{part} :", f"{part} "])
                            if display_key: # Check if display_key is not None
                                potential_prefixes.extend([f"{display_key}:", f"{display_key} :", f"{display_key} "])
                                display_key_parts = re.split(r'[:\s]+', display_key)
                                for part_dp in display_key_parts: # Use different var name
                                    if part_dp: potential_prefixes.extend([f"{part_dp}:", f"{part_dp} :", f"{part_dp} "])
                            potential_prefixes = sorted(list(set(potential_prefixes)), key=len, reverse=True)
                            for prefix in potential_prefixes:
                                if re.match(re.escape(prefix), cleaned_value, re.IGNORECASE):
                                    cleaned_value = cleaned_value[len(prefix):].strip(); break
                            common_data[display_key] = cleaned_value
    
    # --- Split Declarant's Sequence Number ---
    full_dsn = common_data.pop("Declarant's Sequence Number", "") # Remove original, get its value
    dsn_year = ""
    dsn_identifier = ""

    if full_dsn:
        # Try regex matching: first 4 digits, then the rest
        match = re.match(r"(\d{4})\s*(.*)", full_dsn.strip())
        if match:
            dsn_year = match.group(1)
            dsn_identifier = match.group(2).strip()
        else:
            # Fallback to simple split if regex doesn't match (e.g., not starting with 4 digits)
            parts = full_dsn.split(" ", 1)
            dsn_year = parts[0]
            if len(parts) > 1:
                dsn_identifier = parts[1]
            else: # If no space, put the whole thing as year if it's mostly digits, or identifier if it has #
                if full_dsn.startswith("#") or not full_dsn.replace(" ","").isalnum() : # Crude check for identifier-like
                    dsn_identifier = full_dsn
                    dsn_year = "" # Clear year if it was wrongly assigned
                else:
                    dsn_year = full_dsn # Assume it's mostly year if no space and no clear identifier pattern

    common_data["Declarant Sequence Year"] = dsn_year
    common_data["Declarant Sequence Identifier"] = dsn_identifier
    # --- End Split ---

    return common_data

# Main Streamlit application function
def main():
    st.markdown("""
        <style>
            .main-title { font-size: 40px; color: #4F8BF9; text-align: center; margin-bottom: 20px; }
            .sub-title { font-size: 24px; color: #4F8BF9; margin-top: 20px; margin-bottom: 10px; }
            .info-text { font-size: 14px; color: #555; margin-bottom: 5px; }
            .text-field { border-radius: 10px; padding: 10px; background: #f4f4f9; border: 1px solid #ccc; margin-bottom: 15px; }
            .stDataFrame { margin-bottom: 15px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-title">CUSDEC II Data Extractor (Multi-PDF)</h1>', unsafe_allow_html=True)
    st.write("Upload one or more CUSDEC II PDFs to extract specific data fields from the first page of each.")
    st.warning("AI-powered extraction may make mistakes. Always double-check extracted data.")

    current_user_login = "dilshan-jolanka" 
    
    uploaded_files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)

    excel_column_order = [
        "Source File", 
        "Processing DateTime (UTC)", 
        "Processed By User",
        "Customs Reference Code E", 
        "Customs Reference Number", 
        "Declarant Sequence Year",       # New
        "Declarant Sequence Identifier", # New
        "Box 2: Exporter", 
        "Box 8: Consignee", 
        "Box 9: Person Responsible for Financial Settlement",
        "Box 11: Trading", 
        "Box 14: Declarant/Representative", 
        "Box 15: Country of Export",
        "Box 16: Country of origin", 
        "Box 18: Vessel/Flight", 
        "Box 20: Delivery Terms",
        "Box 22: Currency & Total Amount Invoiced", 
        "Box 23: Exchange Rate",
        "Box 28: Financial and banking data", 
        "Guarantee LKR", 
        "Box 31: Description",
        "Box 33: Commodity (HS) Code", 
        "Box 35: Gross Mass (Kg)", 
        "Box 38: Net Mass (Kg)",
        "D.Val", 
        "D.Qty",
    ]
    
    common_fields_to_display_in_ui = [ # Updated for UI
        "Customs Reference Code E", "Customs Reference Number", 
        "Declarant Sequence Year",       # New
        "Declarant Sequence Identifier", # New
        "Box 2: Exporter", "Box 8: Consignee", "Box 9: Person Responsible for Financial Settlement",
        "Box 11: Trading", "Box 14: Declarant/Representative", "Box 15: Country of Export",
        "Box 16: Country of origin", "Box 18: Vessel/Flight", "Box 20: Delivery Terms",
        "Box 22: Currency & Total Amount Invoiced", "Box 23: Exchange Rate",
        "Box 28: Financial and banking data", "Guarantee LKR", "Box 31: Description",
        "Box 33: Commodity (HS) Code", "Box 35: Gross Mass (Kg)", "Box 38: Net Mass (Kg)",
        "D.Val", "D.Qty",
    ]

    if 'all_extracted_data' not in st.session_state:
        st.session_state.all_extracted_data = []

    if uploaded_files:
        st.write(f"{len(uploaded_files)} PDF(s) selected.")
        if st.button("Extract Data from All Uploaded PDFs"):
            processing_start_time_utc_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.all_extracted_data = [] 
            
            with st.spinner("Extracting data from all PDFs..."):
                for uploaded_file in uploaded_files:
                    st.write(f"Processing {uploaded_file.name}...")
                    common_data_from_extraction = extract_data_fields(uploaded_file) # Renamed var
                    st.session_state.all_extracted_data.append({
                        "filename": uploaded_file.name,
                        "data": common_data_from_extraction, # Use the renamed var
                        "processing_datetime_utc": processing_start_time_utc_str,
                        "processed_by_user": current_user_login
                    })
            st.success("Data extraction complete for all files!")

    if st.session_state.all_extracted_data:
        st.markdown("---")
        for item_idx, item in enumerate(st.session_state.all_extracted_data):
            filename = item["filename"]
            data_for_file = item["data"]
            proc_datetime = item.get("processing_datetime_utc", "N/A")
            proc_user = item.get("processed_by_user", "N/A")

            st.markdown(f'<h2 class="sub-title">Extracted Data for: {filename}</h2>', unsafe_allow_html=True)
            st.markdown(f'<p class="info-text">Processed on: {proc_datetime} (UTC) by {proc_user}</p>', unsafe_allow_html=True)
            
            if "error" in data_for_file: # Check if the 'data' dict itself is an error marker
                st.error(data_for_file["error"])
                st.markdown("---")
                continue
            # Additional check if 'data' is a dict but contains an error message from Gemini
            if isinstance(data_for_file, dict) and data_for_file.get("error"):
                st.error(f"Extraction error for {filename}: {data_for_file.get('error')}")
                st.markdown("---")
                continue


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

        if st.session_state.all_extracted_data:
            all_files_rows_for_excel = []

            for item in st.session_state.all_extracted_data:
                filename = item["filename"]
                data_for_file = item["data"] # This is the dict returned by extract_data_fields
                proc_datetime = item.get("processing_datetime_utc", "N/A")
                proc_user = item.get("processed_by_user", "N/A")

                row_data = {
                    "Source File": filename,
                    "Processing DateTime (UTC)": proc_datetime,
                    "Processed By User": proc_user
                }
                
                # Check if data_for_file itself is an error string or contains an error key
                is_error_state = isinstance(data_for_file, str) or (isinstance(data_for_file, dict) and "error" in data_for_file)

                if is_error_state:
                    error_message = data_for_file if isinstance(data_for_file, str) else data_for_file.get("error", "Unknown extraction error")
                    row_data["Declarant Sequence Year"] = f"ERROR: {error_message}" # Put error in a prominent place
                    for field_name in excel_column_order: # Iterate through all potential excel columns
                        if field_name not in row_data: # Fill other fields for this error row
                             row_data[field_name] = "N/A due to error" if field_name not in ["Source File", "Processing DateTime (UTC)", "Processed By User"] else row_data.get(field_name)
                else:
                    for field_name in excel_column_order: # Use excel_column_order to ensure all columns are considered
                        if field_name not in ["Source File", "Processing DateTime (UTC)", "Processed By User"]:
                            row_data[field_name] = data_for_file.get(field_name, "") 
                
                all_files_rows_for_excel.append(row_data)
            
            if all_files_rows_for_excel:
                df_export = pd.DataFrame(all_files_rows_for_excel)
                
                final_columns_for_excel = []
                for col in excel_column_order:
                    if col in df_export.columns:
                        final_columns_for_excel.append(col)
                    # If a column from excel_column_order is somehow missing from all rows,
                    # it won't be added here, which is fine. Pandas handles missing columns.
                
                df_export = df_export[final_columns_for_excel]


                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_export.to_excel(writer, sheet_name='All Extracted Data', index=False)
                
                excel_data = output.getvalue()
                if excel_data: 
                    st.download_button(
                        label="Export All Data to Excel (Tabular)",
                        data=excel_data,
                        file_name='all_cusdec_extracted_data_tabular.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        help='Download all extracted data in a single sheet tabular format.'
                    )

if __name__ == "__main__":
    main()
