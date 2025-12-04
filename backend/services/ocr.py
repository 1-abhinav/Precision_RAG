"""
OCR utilities for extracting text from scanned PDF pages.
Handles page rotation detection and OCR in all orientations.
"""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# pdf2image is optional - we'll use pdfplumber's to_image() as primary method (no Poppler needed)
PDF2IMAGE_AVAILABLE = False
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    logger.debug("pdf2image not available - will use pdfplumber's to_image() method (no Poppler needed)")

try:
    import pytesseract
    from PIL import Image
    
    # Auto-detect Tesseract path on Windows if not in PATH
    if platform.system() == "Windows":
        # Common Tesseract installation paths on Windows
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        ]
        
        # Only set if pytesseract can't find it automatically
        try:
            # Try to get version - if this works, tesseract is already found
            pytesseract.get_tesseract_version()
        except Exception:
            # Tesseract not found, try to locate it
            for tesseract_path in possible_paths:
                if Path(tesseract_path).exists():
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    logger.info(f"Auto-detected Tesseract at: {tesseract_path}")
                    break
            else:
                logger.warning(
                    "Tesseract not found in PATH or common locations. "
                    "Please set pytesseract.pytesseract.tesseract_cmd manually."
                )
    
    # Import pdfplumber types only for type hints (optional)
    try:
        from pdfplumber import PDF, Page  # type: ignore
    except ImportError:
        # Type hints only, not critical for functionality
        PDF = None  # type: ignore
        Page = None  # type: ignore
    
    OCR_AVAILABLE = True
except ImportError as e:
    OCR_AVAILABLE = False
    logger.warning(f"OCR dependencies not available: {e}. OCR functionality will be disabled.")


def _detect_orientation(image: Image.Image) -> int:  # type: ignore
    """
    Detect the correct orientation of an image using Tesseract's OSD.
    
    Returns the rotation angle (0, 90, 180, or 270) needed to correct the orientation.
    """
    try:
        # Use Tesseract's Orientation and Script Detection (OSD)
        # This is much faster than trying all orientations
        osd = pytesseract.image_to_osd(image, config='--psm 0')
        
        # Parse OSD output to get rotation angle
        # Format: "Rotate: 90" or "Orientation in degrees: 90"
        for line in osd.split('\n'):
            if 'Rotate:' in line or 'Orientation in degrees:' in line:
                try:
                    detected_angle = int(line.split(':')[1].strip())
                    # Tesseract reports the angle needed to rotate TO correct orientation
                    # We need the angle to rotate FROM current orientation
                    return detected_angle
                except (ValueError, IndexError):
                    continue
    except Exception as e:
        logger.debug(f"OSD detection failed: {e}, trying fallback method")
    
    # Fallback: Try all orientations and pick the one with most text
    # This is slower but more reliable if OSD fails
    best_angle = 0
    best_text_length = 0
    
    for angle in [0, 90, 180, 270]:
        rotated = image.rotate(-angle, expand=True)
        try:
            # Quick OCR test with minimal config
            text = pytesseract.image_to_string(rotated, lang="eng", config='--psm 6')
            text_length = len(text.strip())
            
            if text_length > best_text_length:
                best_text_length = text_length
                best_angle = angle
        except Exception as e:
            logger.debug(f"OCR test failed for angle {angle}: {e}")
            continue
    
    return best_angle


def _ocr_image(image: Image.Image, rotation: int = 0) -> str:  # type: ignore
    """
    Perform OCR on an image with optional rotation.
    
    Args:
        image: PIL Image to process
        rotation: Rotation angle in degrees (0, 90, 180, or 270)
    
    Returns:
        Extracted text string
    """
    if rotation != 0:
        image = image.rotate(-rotation, expand=True)
    
    try:
        # Use Tesseract with optimized settings for scanned documents
        custom_config = r'--oem 3 --psm 6'  # OEM 3 = LSTM, PSM 6 = Assume uniform block of text
        text = pytesseract.image_to_string(image, lang="eng", config=custom_config)
        return text
    except Exception as e:
        logger.warning(f"OCR extraction failed: {e}")
        return ""


def extract_text_with_ocr_from_image(image: Image.Image) -> str:  # type: ignore
    """
    Extract text from an image using OCR with automatic orientation detection.
    
    Args:
        image: PIL Image to process
    
    Returns:
        Extracted text string
    """
    try:
        # Detect best orientation
        best_angle = _detect_orientation(image)
        if best_angle != 0:
            logger.debug(f"Detected page rotation: {best_angle} degrees")
        
        # Perform OCR with correct orientation
        text = _ocr_image(image, rotation=best_angle)
        
        # If text is still empty, try all orientations
        if not text.strip():
            logger.debug("Trying all orientations as fallback")
            for angle in [0, 90, 180, 270]:
                if angle == best_angle:
                    continue  # Already tried
                text = _ocr_image(image, rotation=angle)
                if text.strip():
                    logger.debug(f"Found text at {angle} degrees")
                    break
        
        return text
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return ""


def extract_text_with_ocr_from_pdf_page(
    pdf_path: str,
    page_number: int,
    dpi: int = 300,
) -> str:
    """
    Extract text from a specific PDF page using OCR.
    Uses pdf2image if available (requires Poppler), otherwise falls back to pdfplumber.
    
    Args:
        pdf_path: Path to PDF file (must be a file path, not bytes)
        page_number: 1-indexed page number
        dpi: Resolution for image conversion (higher = better quality but slower)
    
    Returns:
        Extracted text string
    """
    if not OCR_AVAILABLE:
        logger.error("OCR dependencies not available. Please install pytesseract and Pillow.")
        return ""
    
    # Try pdf2image first if available (requires Poppler)
    if PDF2IMAGE_AVAILABLE:
        try:
            images = convert_from_path(
                pdf_path,
                first_page=page_number,
                last_page=page_number,
                dpi=dpi,
            )
            
            if images:
                image = images[0]
                return extract_text_with_ocr_from_image(image)
        except Exception as e:
            logger.debug(f"pdf2image conversion failed (Poppler may be missing): {e}")
    
    # Fallback: Use pdfplumber (no Poppler needed)
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            if page_number <= len(pdf.pages):
                page = pdf.pages[page_number - 1]
                im = page.to_image(resolution=dpi)
                pil_image = im.original
                return extract_text_with_ocr_from_image(pil_image)
    except Exception as e:
        logger.error(f"Failed to extract text from PDF page {page_number}: {e}")
        return ""
    
    return ""


def extract_text_with_ocr_from_pdfplumber_page(
    pdf: PDF,  # type: ignore
    page: Page,  # type: ignore
    page_index: int,
    dpi: int = 300,
) -> str:
    """
    Extract text from a pdfplumber Page object using OCR.
    Uses pdfplumber's to_image() method (no Poppler required).
    
    Args:
        pdf: pdfplumber PDF object
        page: pdfplumber Page object
        page_index: 0-indexed page number
        dpi: Resolution for image conversion
    
    Returns:
        Extracted text string
    """
    if not OCR_AVAILABLE:
        logger.error("OCR dependencies not available. Please install pytesseract and Pillow.")
        return ""
    
    try:
        # Use pdfplumber's to_image() method - no Poppler needed!
        im = page.to_image(resolution=dpi)
        pil_image = im.original
        return extract_text_with_ocr_from_image(pil_image)
    except Exception as e:
        logger.error(f"OCR extraction from pdfplumber page {page_index + 1} failed: {e}")
        return ""

