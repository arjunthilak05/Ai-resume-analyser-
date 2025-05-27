from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
import pytesseract
from PIL import Image
import pdf2image
import requests
import json
from werkzeug.utils import secure_filename
import tempfile
import logging
import PyPDF2
import pdfplumber
from concurrent.futures import ThreadPoolExecutor
import threading
from io import BytesIO
import fitz  # PyMuPDF - faster PDF processing
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "gemma3:1b"

# Thread pool for parallel processing
thread_pool = ThreadPoolExecutor(max_workers=4)

# Configure Tesseract for faster OCR
pytesseract.pytesseract.tesseract_cmd = r'tesseract'  # Adjust path if needed

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf_fast(pdf_path):
    """Fast PDF text extraction using multiple methods with fallback"""
    try:
        # Method 1: Try PyMuPDF (fastest for text-based PDFs)
        text = extract_with_pymupdf(pdf_path)
        if text and len(text.strip()) > 50:  # Good text extraction
            logger.info("Successfully extracted text using PyMuPDF")
            return text
            
        # Method 2: Try pdfplumber (good for structured PDFs)
        text = extract_with_pdfplumber(pdf_path)
        if text and len(text.strip()) > 50:
            logger.info("Successfully extracted text using pdfplumber")
            return text
            
        # Method 3: Try PyPDF2 (fallback)
        text = extract_with_pypdf2(pdf_path)
        if text and len(text.strip()) > 50:
            logger.info("Successfully extracted text using PyPDF2")
            return text
            
        # Method 4: OCR fallback (slowest but works on image PDFs)
        logger.info("Falling back to OCR extraction")
        return extract_text_from_pdf_ocr(pdf_path)
        
    except Exception as e:
        logger.error(f"Error in fast PDF extraction: {str(e)}")
        return extract_text_from_pdf_ocr(pdf_path)

def extract_with_pymupdf(pdf_path):
    """Extract text using PyMuPDF (fastest)"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"PyMuPDF extraction failed: {str(e)}")
        return None

def extract_with_pdfplumber(pdf_path):
    """Extract text using pdfplumber"""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {str(e)}")
        return None

def extract_with_pypdf2(pdf_path):
    """Extract text using PyPDF2"""
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"PyPDF2 extraction failed: {str(e)}")
        return None

def extract_text_from_pdf_ocr(pdf_path):
    """OCR-based extraction for image PDFs (slower but thorough)"""
    try:
        # Convert PDF to images with optimized settings
        pages = pdf2image.convert_from_path(
            pdf_path,
            dpi=200,  # Reduced DPI for speed
            first_page=1,
            last_page=None,
            thread_count=4,  # Use multiple threads
            grayscale=True,  # Faster processing
            size=(1700, None)  # Optimize image size
        )
        
        extracted_text = ""
        
        # Process pages in parallel
        def process_page(page_data):
            page_num, page = page_data
            try:
                # Optimize image for OCR
                page = page.convert('L')  # Convert to grayscale
                
                # Use optimized OCR settings
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?@#$%^&*()_+-=[]{}|;:,.<>?/~` '
                
                # Extract text
                page_text = pytesseract.image_to_string(page, config=custom_config)
                
                if page_text.strip():
                    return f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                return ""
            except Exception as e:
                logger.error(f"Error processing page {page_num + 1}: {str(e)}")
                return ""
        
        # Process pages in parallel
        page_data = list(enumerate(pages))
        with ThreadPoolExecutor(max_workers=min(4, len(pages))) as executor:
            results = list(executor.map(process_page, page_data))
        
        extracted_text = "".join(results)
        return extracted_text.strip()
        
    except Exception as e:
        logger.error(f"Error in OCR extraction: {str(e)}")
        return None

def extract_text_from_image_fast(image_path):
    """Optimized image text extraction"""
    try:
        # Open and optimize image
        image = Image.open(image_path)
        
        # Convert to grayscale for faster processing
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize if too large (maintain aspect ratio)
        max_size = (2000, 2000)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Optimized OCR configuration
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, config=custom_config)
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        return None

def analyze_resume_with_ollama(resume_text, job_description=""):
    """Send resume text to local Ollama for analysis"""
    try:
        # Construct the analysis prompt
        if job_description.strip():
            prompt = f"""
As an expert resume reviewer and career coach, analyze the following resume and provide detailed feedback. Also consider how well it matches the job description provided.

RESUME CONTENT:
{resume_text}

JOB DESCRIPTION:
{job_description}

Please provide a comprehensive analysis in the following format:

## OVERALL ASSESSMENT
Rate the resume overall (1-10) and provide a brief summary.

## STRENGTHS
List the main strengths of this resume.

## AREAS FOR IMPROVEMENT
Identify specific areas that need improvement.

## FORMATTING & STRUCTURE
Comment on the layout, organization, and readability.

## CONTENT ANALYSIS
- Skills and qualifications assessment
- Experience relevance and presentation
- Education section effectiveness
- Missing elements

## JOB MATCH ANALYSIS
How well does this resume match the job requirements? What's missing?

## SPECIFIC RECOMMENDATIONS
Provide 5-7 actionable recommendations for improvement.

## KEYWORDS TO ADD
Suggest relevant keywords to improve ATS compatibility.

Be specific, constructive, and professional in your feedback.
"""
        else:
            prompt = f"""
As an expert resume reviewer and career coach, analyze the following resume and provide detailed feedback.

RESUME CONTENT:
{resume_text}

Please provide a comprehensive analysis in the following format:

## OVERALL ASSESSMENT
Rate the resume overall (1-10) and provide a brief summary.

## STRENGTHS
List the main strengths of this resume.

## AREAS FOR IMPROVEMENT
Identify specific areas that need improvement.

## FORMATTING & STRUCTURE
Comment on the layout, organization, and readability.

## CONTENT ANALYSIS
- Skills and qualifications assessment
- Experience relevance and presentation
- Education section effectiveness
- Missing elements

## SPECIFIC RECOMMENDATIONS
Provide 5-7 actionable recommendations for improvement.

## KEYWORDS TO ADD
Suggest relevant keywords to improve ATS compatibility.

Be specific, constructive, and professional in your feedback.
"""

        # Send request to Ollama
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'No response generated')
        else:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return f"Error: Unable to analyze resume. Status code: {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Please ensure Ollama is running locally on port 11434."
    except requests.exceptions.Timeout:
        return "Error: Request timed out. The analysis is taking too long."
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        return f"Error analyzing resume: {str(e)}"

def generate_cover_letter_with_ollama(resume_text, job_description, company_name=""):
    """Generate a cover letter using Ollama"""
    try:
        prompt = f"""
Based on the following resume and job description, write a professional cover letter.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

COMPANY: {company_name if company_name else "the company"}

Write a compelling cover letter that:
1. Highlights relevant experience from the resume
2. Addresses key requirements from the job description
3. Shows enthusiasm for the role
4. Is professional and well-structured
5. Is approximately 300-400 words

Format the cover letter properly with salutation, body paragraphs, and closing.
"""

        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "max_tokens": 1500
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'No cover letter generated')
        else:
            return f"Error generating cover letter. Status code: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        return f"Error generating cover letter: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        resume_text = ""
        job_description = request.form.get('job_description', "").strip()

        # Extract text from uploaded file or pasted text
        if 'resume_file' in request.files:
            file = request.files['resume_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                resume_text = extract_text_from_pdf_fast(filepath)  # Ensure this function works correctly
                os.remove(filepath)
        elif 'resume_text' in request.form:
            resume_text = request.form['resume_text'].strip()

        if not resume_text:
            return jsonify({'success': False, 'error': 'No resume content provided'}), 400

        # Analyze resume using Ollama
        analysis = analyze_resume_with_ollama(resume_text, job_description)

        return jsonify({
            'success': True,
            'extracted_text': resume_text,
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate_cover_letter', methods=['POST'])
def generate_cover_letter():
    try:
        data = request.get_json()
        resume_text = data.get('resume_text', '')
        job_description = data.get('job_description', '')
        company_name = data.get('company_name', '')
        
        if not resume_text or not job_description:
            return jsonify({'error': 'Resume text and job description are required'}), 400
        
        cover_letter = generate_cover_letter_with_ollama(resume_text, job_description, company_name)
        
        return jsonify({
            'success': True,
            'cover_letter': cover_letter
        })
        
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Check if Ollama is running and model is available"""
    try:
        # Test Ollama connection
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_available = any(model.get('name', '').startswith(MODEL_NAME.split(':')[0]) for model in models)
            
            return jsonify({
                'ollama_running': True,
                'model_available': model_available,
                'available_models': [model.get('name') for model in models]
            })
        else:
            return jsonify({'ollama_running': False, 'model_available': False})
    except:
        return jsonify({'ollama_running': False, 'model_available': False})

if __name__ == '__main__':
    print("Starting Optimized Resume Analyzer...")
    print(f"Make sure Ollama is running: ollama serve")
    print(f"Make sure model is available: ollama run {MODEL_NAME}")
    print("Optimizations enabled:")
    print("- Multi-method PDF extraction (PyMuPDF, pdfplumber, PyPDF2)")
    print("- Parallel OCR processing")
    print("- Memory-based file processing")
    print("- Optimized image preprocessing")
    app.run(debug=True, host='0.0.0.0', port=5001)
