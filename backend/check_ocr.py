"""
Quick diagnostic script to check if OCR dependencies are properly installed.
Run this to verify your OCR setup before processing scanned PDFs.
"""

import sys
from pathlib import Path

def check_ocr_setup():
    """Check if all OCR dependencies are available."""
    print("=" * 60)
    print("OCR Dependencies Check")
    print("=" * 60)
    
    all_ok = True
    
    # Check Python packages
    print("\n1. Checking Python packages...")
    
    try:
        import pytesseract
        print("   ✓ pytesseract: installed")
    except ImportError:
        print("   ✗ pytesseract: NOT installed")
        print("      Run: pip install pytesseract")
        all_ok = False
    
    try:
        import pdf2image
        print("   ✓ pdf2image: installed")
    except ImportError:
        print("   ✗ pdf2image: NOT installed")
        print("      Run: pip install pdf2image")
        all_ok = False
    
    try:
        from PIL import Image
        print("   ✓ Pillow: installed")
    except ImportError:
        print("   ✗ Pillow: NOT installed")
        print("      Run: pip install Pillow")
        all_ok = False
    
    # Check Tesseract OCR binary
    print("\n2. Checking Tesseract OCR binary...")
    try:
        import pytesseract
        import platform
        import os
        from pathlib import Path
        
        # Auto-detect Tesseract on Windows if not in PATH
        if platform.system() == "Windows":
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
            ]
            
            try:
                version = pytesseract.get_tesseract_version()
                print(f"   ✓ Tesseract OCR: installed (version {version})")
            except Exception:
                # Try to find and configure Tesseract
                found = False
                for tesseract_path in possible_paths:
                    if Path(tesseract_path).exists():
                        pytesseract.pytesseract.tesseract_cmd = tesseract_path
                        print(f"   ✓ Tesseract OCR: found at {tesseract_path}")
                        try:
                            version = pytesseract.get_tesseract_version()
                            print(f"      Version: {version}")
                        except Exception:
                            pass
                        found = True
                        break
                
                if not found:
                    raise Exception("Tesseract not found in PATH or common locations")
        else:
            version = pytesseract.get_tesseract_version()
            print(f"   ✓ Tesseract OCR: installed (version {version})")
    except Exception as e:
        print(f"   ✗ Tesseract OCR: NOT found")
        print(f"      Error: {e}")
        print("      Install Tesseract OCR:")
        print("      - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("      - macOS: brew install tesseract")
        print("      - Linux: sudo apt-get install tesseract-ocr")
        all_ok = False
    
    # Check Poppler (optional - pdf2image is not required)
    print("\n3. Checking optional dependencies...")
    try:
        from pdf2image import convert_from_path
        print("   ✓ pdf2image: available (optional - Poppler may be needed if used)")
        print("   ℹ  Note: The system uses pdfplumber's to_image() by default (no Poppler needed)")
    except ImportError:
        print("   ℹ  pdf2image: not installed (optional)")
        print("      The system will use pdfplumber's to_image() method (no Poppler needed)")
        # Don't mark as error - it's optional
    
    # Summary
    print("\n" + "=" * 60)
    if all_ok:
        print("✓ All required OCR dependencies are installed!")
        print("  You can process scanned PDFs without Poppler.")
        print("  The system uses pdfplumber's to_image() method (no Poppler needed).")
    else:
        print("✗ Some required OCR dependencies are missing.")
        print("  Please install the missing components and try again.")
        print("  See OCR_SETUP.md for detailed installation instructions.")
        print("  Note: Poppler is NOT required - pdfplumber handles image conversion.")
    print("=" * 60)
    
    return all_ok

if __name__ == "__main__":
    success = check_ocr_setup()
    sys.exit(0 if success else 1)

