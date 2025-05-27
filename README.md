# 🔍 AI Resume Analyzer & Cover Letter Generator

A powerful, AI-driven web application that analyzes resumes and generates tailored cover letters using local Ollama models. Built with Flask and featuring an intuitive web interface with drag-and-drop functionality.

## ✨ Features

### 📄 Resume Analysis
- **Multi-format Support**: Upload PDF, PNG, JPG, JPEG, GIF, or TXT files
- **Smart Text Extraction**: Advanced PDF processing with multiple fallback methods
- **OCR Technology**: Tesseract-powered text extraction from image-based documents
- **AI-Powered Analysis**: Comprehensive resume feedback using local Ollama models
- **Job Matching**: Compare resume against specific job descriptions
- **ATS Optimization**: Keyword suggestions for better applicant tracking system compatibility

### ✉️ Cover Letter Generation
- **AI-Generated Content**: Professional cover letters tailored to job descriptions
- **Company Customization**: Personalized content based on company information
- **Resume Integration**: Uses analyzed resume data for relevant experience highlighting

### 🚀 Technical Features
- **Parallel Processing**: Multi-threaded OCR and document processing
- **Memory Optimization**: Efficient file handling without persistent storage
- **Real-time Status**: Health monitoring for Ollama service
- **Responsive Design**: Mobile-friendly interface with modern UI
- **Drag & Drop**: Intuitive file upload experience

## 🛠️ Tech Stack

### Backend
- **Flask** - Web framework
- **PyTesseract** - OCR text extraction
- **PyMuPDF (fitz)** - Fast PDF processing
- **pdfplumber** - Advanced PDF text extraction
- **PyPDF2** - PDF processing fallback
- **pdf2image** - PDF to image conversion
- **PIL (Pillow)** - Image processing
- **Requests** - HTTP client for Ollama API

### Frontend
- **HTML5** - Modern semantic markup
- **CSS3** - Responsive design with gradients and animations
- **Vanilla JavaScript** - Interactive functionality and API integration

### AI Integration
- **Ollama** - Local AI model serving
- **Gemma 3 1B** - Default language model (configurable)

## 📋 Prerequisites

Before running the application, ensure you have the following installed:

### System Requirements
- Python 3.8+
- Tesseract OCR
- Ollama
- Poppler (for PDF processing)

### Installation Commands

#### Ubuntu/Debian
```bash
# Install system dependencies
sudo apt update
sudo apt install tesseract-ocr poppler-utils

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

#### macOS
```bash
# Install system dependencies
brew install tesseract poppler

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows
1. Download and install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
2. Download and install [Poppler](http://blog.alivate.com.au/poppler-windows/)
3. Install [Ollama for Windows](https://ollama.ai/download)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ai-resume-analyzer.git
cd ai-resume-analyzer
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start Ollama Service
```bash
# Start Ollama server
ollama serve

# In another terminal, pull the AI model
ollama pull gemma3:1b
```

### 5. Configure Application
Update the configuration in `app.py` if needed:
```python
# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "gemma3:1b"  # Change to your preferred model

# Tesseract path (Windows users)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### 6. Run the Application
```bash
python app.py
```

Visit `http://localhost:5001` in your web browser.

## 📁 Project Structure

```
ai-resume-analyzer/
├── app.py                 # Flask application main file
├── templates/
│   └── index.html         # Frontend HTML template
├── uploads/               # Temporary file storage (auto-created)
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
└── static/               # Static assets (if any)
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file for configuration:
```env
SECRET_KEY=your-secret-key-here
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=gemma3:1b
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=uploads
```

### Supported Models
The application works with various Ollama models:
- `gemma3:1b` (default, fast)
- `llama3:8b` (more comprehensive)
- `mistral:7b` (balanced performance)
- `codellama:13b` (for technical resumes)

Change the model in `app.py`:
```python
MODEL_NAME = "your-preferred-model"
```

## 📊 API Endpoints

### Resume Analysis
```http
POST /upload
Content-Type: multipart/form-data

Parameters:
- resume_file: File upload
- resume_text: Text content
- job_description: Optional job description
```

### Cover Letter Generation
```http
POST /generate_cover_letter
Content-Type: application/json

{
  "resume_text": "...",
  "job_description": "...",
  "company_name": "Optional"
}
```

### Health Check
```http
GET /health
```

## 🎯 Usage Examples

### Basic Resume Analysis
1. Upload a PDF resume or paste text content
2. Optionally add a job description for tailored feedback
3. Click "Analyze Resume" to get AI-powered insights

### Cover Letter Generation
1. Switch to the "Generate Cover Letter" tab
2. Provide resume content and job description
3. Add company name for personalization
4. Generate professional cover letter

## 🔍 Features in Detail

### Resume Analysis Output
- **Overall Assessment**: Numerical rating and summary
- **Strengths**: Key positive aspects identified
- **Areas for Improvement**: Specific enhancement suggestions
- **Formatting & Structure**: Layout and organization feedback
- **Content Analysis**: Skills, experience, and education evaluation
- **Job Match Analysis**: Alignment with job requirements
- **Specific Recommendations**: Actionable improvement steps
- **Keywords**: ATS optimization suggestions

### Text Extraction Methods
1. **PyMuPDF**: Fastest for text-based PDFs
2. **pdfplumber**: Excellent for structured documents
3. **PyPDF2**: Reliable fallback method
4. **OCR Processing**: For image-based documents with parallel processing

## 🚀 Performance Optimizations

- **Multi-method PDF extraction** with intelligent fallback
- **Parallel OCR processing** using ThreadPoolExecutor
- **Memory-efficient file handling** without persistent storage
- **Optimized image preprocessing** for faster OCR
- **Configurable thread pools** for concurrent processing

## 🐛 Troubleshooting

### Common Issues

#### Ollama Not Running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

#### Model Not Available
```bash
# List available models
ollama list

# Pull required model
ollama pull gemma3:1b
```

#### Tesseract Not Found
- **Linux**: `sudo apt install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Update the path in `app.py`

#### PDF Processing Issues
```bash
# Install poppler
# Ubuntu: sudo apt install poppler-utils
# macOS: brew install poppler
```

## 📈 Development

### Adding New Models
1. Pull the model with Ollama: `ollama pull model-name`
2. Update `MODEL_NAME` in `app.py`
3. Adjust prompt templates if needed

### Extending Features
- Add support for more file formats
- Implement user authentication
- Add resume templates
- Create API rate limiting
- Add database storage

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and commit: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Update documentation for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** - Local AI model serving
- **Tesseract** - OCR technology
- **Flask** - Web framework
- **PyMuPDF** - PDF processing
- **Contributors** - Open source community
