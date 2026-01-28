"""
OCR Service for extracting ingredient text from food product images
Supports multiple OCR engines with confidence scoring
"""
import cv2
import numpy as np
from PIL import Image
import io
import re

# Try to import OCR libraries
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
    # Initialize EasyOCR reader (lazy loading)
    _easyocr_reader = None
except ImportError:
    EASYOCR_AVAILABLE = False


class OCRResult:
    """Container for OCR extraction results with confidence metrics"""
    
    def __init__(self, text, confidence, method, raw_data=None):
        self.text = text
        self.confidence = confidence  # 0-100
        self.method = method  # 'tesseract', 'easyocr', or 'combined'
        self.raw_data = raw_data or []
        self.has_ingredients = self._detect_ingredients()
        self.quality_score = self._calculate_quality()
    
    def _detect_ingredients(self):
        """Check if extracted text likely contains ingredient information"""
        if not self.text or len(self.text.strip()) < 10:
            return False
        
        # Common ingredient-related keywords
        ingredient_keywords = [
            'ingredient', 'contains', 'wheat', 'flour', 'sugar', 'salt',
            'oil', 'water', 'milk', 'egg', 'soy', 'preservative',
            'color', 'flavor', 'vitamin', 'mineral', 'acid', 'starch'
        ]
        
        text_lower = self.text.lower()
        keyword_matches = sum(1 for keyword in ingredient_keywords if keyword in text_lower)
        
        # Check for comma-separated list pattern (common in ingredients)
        comma_count = text_lower.count(',')
        
        return keyword_matches >= 2 or comma_count >= 3
    
    def _calculate_quality(self):
        """Calculate overall quality score (0-100) based on multiple factors"""
        if not self.text:
            return 0
        
        score = self.confidence * 0.6  # Base score from OCR confidence
        
        # Bonus for having ingredients
        if self.has_ingredients:
            score += 20
        
        # Bonus for reasonable text length
        text_length = len(self.text.strip())
        if 50 <= text_length <= 1000:
            score += 10
        elif text_length > 1000:
            score += 5
        
        # Penalty for too many special characters (noise)
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s,.]', self.text)) / max(len(self.text), 1)
        if special_char_ratio > 0.3:
            score -= 15
        
        return min(100, max(0, score))
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'text': self.text,
            'confidence': round(self.confidence, 2),
            'quality_score': round(self.quality_score, 2),
            'method': self.method,
            'has_ingredients': self.has_ingredients,
            'text_length': len(self.text),
        }


def preprocess_image(image_file):
    """
    Preprocess image for better OCR results
    Returns: numpy array (OpenCV format)
    """
    # Convert PIL Image or file to numpy array
    if isinstance(image_file, Image.Image):
        img = np.array(image_file)
    else:
        # Read from file-like object
        image_file.seek(0)
        img = Image.open(image_file)
        img = np.array(img)
    
    # Convert to grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    
    # Apply adaptive thresholding to improve text contrast
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
    
    return denoised


def extract_with_tesseract(image_array):
    """
    Extract text using Tesseract OCR
    Returns: OCRResult object
    """
    if not TESSERACT_AVAILABLE:
        return None
    
    try:
        # Get detailed data with confidence scores
        data = pytesseract.image_to_data(image_array, output_type=pytesseract.Output.DICT)
        
        # Filter out low-confidence results
        text_parts = []
        confidences = []
        
        for i, conf in enumerate(data['conf']):
            if conf > 30:  # Minimum confidence threshold
                text = data['text'][i].strip()
                if text:
                    text_parts.append(text)
                    confidences.append(conf)
        
        if not text_parts:
            return OCRResult('', 0, 'tesseract')
        
        full_text = ' '.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return OCRResult(full_text, avg_confidence, 'tesseract', data)
    
    except Exception as e:
        print(f"Tesseract OCR error: {e}")
        return OCRResult('', 0, 'tesseract')


def extract_with_easyocr(image_array):
    """
    Extract text using EasyOCR
    Returns: OCRResult object
    """
    global _easyocr_reader
    
    if not EASYOCR_AVAILABLE:
        return None
    
    try:
        # Lazy load EasyOCR reader
        if _easyocr_reader is None:
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
        
        # Perform OCR
        results = _easyocr_reader.readtext(image_array)
        
        if not results:
            return OCRResult('', 0, 'easyocr')
        
        # Extract text and confidences
        text_parts = []
        confidences = []
        
        for (bbox, text, conf) in results:
            if conf > 0.3:  # Minimum confidence threshold
                text_parts.append(text)
                confidences.append(conf * 100)  # Convert to 0-100 scale
        
        if not text_parts:
            return OCRResult('', 0, 'easyocr')
        
        full_text = ' '.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return OCRResult(full_text, avg_confidence, 'easyocr', results)
    
    except Exception as e:
        print(f"EasyOCR error: {e}")
        return OCRResult('', 0, 'easyocr')


def extract_ingredients_from_image(image_file):
    """
    Main function to extract ingredients from image using best available OCR method
    
    Args:
        image_file: File-like object or PIL Image
    
    Returns:
        OCRResult object with extracted text and confidence metrics
    """
    # Preprocess image
    try:
        processed_image = preprocess_image(image_file)
    except Exception as e:
        print(f"Image preprocessing error: {e}")
        return OCRResult('', 0, 'none')
    
    results = []
    
    # Try EasyOCR first (generally more accurate)
    easyocr_result = extract_with_easyocr(processed_image)
    if easyocr_result:
        results.append(easyocr_result)
    
    # Try Tesseract as backup/alternative
    tesseract_result = extract_with_tesseract(processed_image)
    if tesseract_result:
        results.append(tesseract_result)
    
    # If no OCR engines available
    if not results:
        return OCRResult(
            '', 0, 'none',
        )
    
    # Return the result with highest quality score
    best_result = max(results, key=lambda r: r.quality_score)
    
    return best_result


