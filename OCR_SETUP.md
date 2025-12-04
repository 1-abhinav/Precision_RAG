# OCR Setup Guide

This application now supports OCR (Optical Character Recognition) for scanned PDFs. To use OCR functionality, you need to install the following dependencies:

## Python Dependencies

The Python packages are already listed in `requirements.txt`:
- `pytesseract==0.3.13` - Python wrapper for Tesseract OCR
- `Pillow==10.4.0` - Image processing library
- `pdf2image==1.17.0` - **OPTIONAL** - Only needed if you want Poppler-based conversion (not required)

**Note:** The system uses `pdfplumber`'s built-in `to_image()` method by default, which does **NOT require Poppler**. The `pdf2image` package is optional and only used as a fallback.

Install them with:
```bash
pip install -r backend/requirements.txt
```

## System Dependencies

### Tesseract OCR

You need to install Tesseract OCR on your system:

#### Windows
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (recommended: `tesseract-ocr-w64-setup-5.x.x.exe`)
3. Add Tesseract to your PATH, or set the path in your code:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

#### macOS
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### Poppler (OPTIONAL - Not Required!)

**Poppler is NOT required!** The system uses `pdfplumber`'s built-in `to_image()` method which doesn't need Poppler.

Poppler is only needed if you want to use the optional `pdf2image` package for PDF-to-image conversion. If you don't install Poppler, the system will automatically use `pdfplumber` instead.

#### If you want to use pdf2image (optional):

##### Windows
1. Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extract and add `bin` folder to your PATH

##### macOS
```bash
brew install poppler
```

##### Linux (Ubuntu/Debian)
```bash
sudo apt-get install poppler-utils
```

## Features

- **Automatic OCR**: When text extraction fails, OCR is automatically attempted
- **Rotation Detection**: Automatically detects and handles horizontal/rotated pages
- **Multi-orientation Support**: Tries all orientations (0°, 90°, 180°, 270°) to find the best text extraction
- **Page-wise Processing**: Each page is processed independently with OCR if needed

## Usage

OCR is automatically used when:
1. Normal text extraction returns empty
2. Layout-based extraction returns empty
3. Table extraction returns empty

The system will log when OCR is used:
```
INFO - Attempting OCR for page 1 (scanned/image-based)
INFO - OCR successfully extracted text from page 1
```

## Performance Notes

- OCR is slower than text extraction (typically 1-5 seconds per page)
- Higher DPI (default: 300) provides better accuracy but is slower
- The system processes pages sequentially to avoid memory issues

## Troubleshooting

If OCR is not working:
1. Verify Tesseract is installed: `tesseract --version`
2. Verify Poppler is installed: `pdftoppm -h`
3. Check that Python packages are installed: `pip list | grep -E "pytesseract|pdf2image|Pillow"`
4. Check application logs for specific error messages

