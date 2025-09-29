# streamlit_app.py
# The main application file for the Streamlit web interface.

import streamlit as st
from ultralytics import YOLO
import os
import collections
from information_extractor import extract_text_from_image, extract_aadhar_details, extract_pan_details
from PIL import Image

# --- Page Configuration ---
st.set_page_config(page_title="KYC Document Extractor", layout="wide", initial_sidebar_state="expanded")

# --- Configuration & Setup ---
#MODEL_PATH = os.path.join('kyc_classifier', 'aadhar_pan_run', 'weights', 'best.pt')
MODEL_PATH=r"C:\Users\Geshu.Sinha\Desktop\Projects\PERS\Aadhar_Panb\train6\weights\best.pt"
UPLOAD_FOLDER = 'uploads'

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Model Loading ---
@st.cache_resource
def load_yolo_model(path):
    """Loads the YOLOv8 model from the specified path. Caches the model for performance."""
    try:
        model = YOLO(path)
        return model
    except Exception as e:
        return e

# --- Main App UI ---
st.title("📄 KYC Document Classification & Data Extraction")
st.write("Upload an image of an Aadhar or PAN card. The system will classify it and extract key information.")

# --- Sidebar ---
st.sidebar.header("How it Works")
st.sidebar.info(
    "This app uses a **YOLOv8** model to classify the document type and **Tesseract OCR** "
    "to extract text. The accuracy of the extraction depends heavily on the image quality."
)
st.sidebar.header("Instructions")
st.sidebar.markdown(
    """
    1.  **Upload Image**: Click 'Browse files' to select a JPG, JPEG, or PNG file.
    2.  **View Results**: The app automatically analyzes the image.
    3.  **Check Raw Text**: If a field is wrong, expand 'View Raw OCR Text' to see what the machine read.
    """
)

# Load the classification model
model = load_yolo_model(MODEL_PATH)
if isinstance(model, Exception):
    st.error(f"Error: Could not load the classification model.")
    st.error(f"Details: {model}")
    st.info("Please ensure the model file exists at the path specified in the script and that all dependencies are installed.")
    st.stop()

# File uploader
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save the uploaded file to process it
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Create two columns for image and results
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Uploaded Image")
        st.image(file_path, use_column_width=True)

    with col2:
        st.subheader("Analysis Results")
        with st.spinner("Analyzing image... Please wait."):
            
            # --- Step 1: Classification ---
            results = model(file_path, verbose=False)
            result = results[0]
            if result.probs is None:
                st.error("Classification failed. The model could not determine the document type.")
                st.stop()
            
            predicted_class = result.names[result.probs.top1].lower()
            confidence = result.probs.top1conf.item()

            st.write("**Document Type:**")
            if 'aadhar' in predicted_class:
                st.success(f"Aadhar Card (Confidence: {confidence:.2%})")
            elif 'pan' in predicted_class:
                st.success(f"PAN Card (Confidence: {confidence:.2%})")
            else:
                st.warning(f"Uncertain: {predicted_class.title()} (Confidence: {confidence:.2%})")

            # --- Step 2: Information Extraction ---
            st.write("**Extracted Information:**")
            
            try:
                extracted_text = extract_text_from_image(file_path)
                details = collections.OrderedDict()

                if not extracted_text.strip():
                    st.warning("OCR could not detect any text. The image may be blurry or of low quality.")
                else:
                    if 'aadhar' in predicted_class:
                        details = extract_aadhar_details(extracted_text)
                    elif 'pan' in predicted_class:
                        details = extract_pan_details(extracted_text)
                    
                    # Display the extracted details
                    for key, value in details.items():
                        if value and value != 'Not Found':
                            st.text_input(label=key, value=value, disabled=True)
                        else:
                            st.text_input(label=key, value="Could not extract.", disabled=True)
                
                    with st.expander("View Raw OCR Text"):
                        st.text_area("OCR Output", extracted_text, height=300)

            except Exception as e:
                st.error(f"An error occurred during information extraction: {e}")

    # Clean up by removing the uploaded file
    os.remove(file_path)
