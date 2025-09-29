# information_extractor.py
# Contains functions to extract text from images and parse it for specific details.
import re
import pytesseract
from PIL import Image

# --- IMPORTANT ---
# You need to have Tesseract OCR installed on your system for this to work.
# After installation, you might need to specify the path to the Tesseract executable,
# especially on Windows. Uncomment the line below if needed.
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\Geshu.Sinha\\Desktop\\ODOMETER\\Code\\Tesseract-OCR\\tesseract.exe'

def extract_text_from_image(image_path):
    """
    Performs OCR on an image to extract all text.
    
    Args:
        image_path (str or file-like object): The path to or buffer of the image file.
    
    Returns:
        str: The extracted text from the image.
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error during OCR extraction: {e}")
        return ""

def extract_pan_details(text):
    """
    Extracts Name, Father's Name, DOB, and PAN number from PAN card text.
    
    Args:
        text (str): The text extracted from a PAN card image.
    
    Returns:
        dict: A dictionary containing the extracted details.
    """
    details = {
        'Name': 'Not Found',
        "Father's Name": 'Not Found',
        'Date of Birth': 'Not Found',
        'PAN Number': 'Not Found'
    }

    # Regex for PAN Number (10 alphanumeric characters)
    pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', text)
    if pan_match:
        details['PAN Number'] = pan_match.group(0)

    # Regex for Date of Birth (DD/MM/YYYY format)
    dob_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
    if dob_match:
        details['Date of Birth'] = dob_match.group(0)

    # Heuristic to find Name and Father's Name
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    name_found = False
    for i, line in enumerate(lines):
        # Name is often in all caps and appears before Father's Name or DOB
        if re.match(r'^[A-Z\s.]{5,}$', line) and len(line.split()) >= 2 and not name_found:
            for next_line in lines[i+1:i+4]:
                if re.search(r'\d{2}/\d{2}/\d{4}', next_line) or "Father's Name" in next_line:
                    details['Name'] = line
                    name_found = True
                    # The next line is often the Father's Name
                    if i + 1 < len(lines) and re.match(r'^[A-Z\s.]{5,}$', lines[i+1]):
                        details["Father's Name"] = lines[i+1]
                    break
        if name_found:
            break
            
    return details

def extract_aadhar_details(text):
    """
    Extracts Name, DOB, Gender, Aadhar number and Address from Aadhar card text.
    
    Args:
        text (str): The text extracted from an Aadhar card image.
    
    Returns:
        dict: A dictionary containing the extracted details.
    """
    details = {
        'Name': 'Not Found',
        'Date of Birth': 'Not Found',
        'Gender': 'Not Found',
        'Aadhar Number': 'Not Found',
        'Address': 'Not Found'
    }

    # Regex for Aadhar Number (12 digits, can have spaces)
    aadhar_match = re.search(r'(\d{4}\s?\d{4}\s?\d{4})', text)
    if aadhar_match:
        details['Aadhar Number'] = aadhar_match.group(1).replace(" ", "")

    # Regex for Gender (Male, Female, Transgender)
    gender_match = re.search(r'(Male|Female|Transgender|MALE|FEMALE)', text)
    if gender_match:
        details['Gender'] = gender_match.group(1).title()

    # Regex for DOB (dd/mm/yyyy) or Year of Birth (yyyy)
    dob_match = re.search(r'(?:DOB|Date of Birth)\s*[:]?\s*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
    if dob_match:
        details['Date of Birth'] = dob_match.group(1)
    else:
        yob_match = re.search(r'(?:Year of Birth)\s*[:]?\s*(\d{4})', text, re.IGNORECASE)
        if yob_match:
            details['Date of Birth'] = f"Year: {yob_match.group(1)}"

    # Heuristic for Name: Often one of the first few non-empty lines before DOB.
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines:
        if ('DOB' in line or 'Birth' in line or details['Date of Birth'] != 'Not Found'):
            break # Stop if we have reached lines containing DOB info
        if re.match(r'^[A-Za-z\s.]{5,}$', line) and len(line.split()) >= 2:
            details['Name'] = line
            break # Assume the first valid name found is the correct one

    # Heuristic for Address: Search for keyword "Address" and capture subsequent lines.
    address_match = re.search(r'Address\s*[:]?\s*(.*?)(?=\d{4}\s?\d{4}\s?\d{4}|$)', text, re.DOTALL | re.IGNORECASE)
    if address_match:
        address_text = address_match.group(1)
        # Clean up common OCR errors and formatting
        address_lines = [line.strip() for line in address_text.split('\n') if line.strip() and len(line) > 2]
        cleaned_address = ', '.join(address_lines).replace(' ,', ',').strip()
        details['Address'] = cleaned_address if cleaned_address else 'Not Found'
        
    return details
