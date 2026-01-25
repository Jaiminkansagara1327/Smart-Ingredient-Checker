from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from PIL import Image
import io
import traceback

from .ocr_service import extract_ingredients_from_image, clean_ingredient_text
from .ai_service import analyze_product_from_ocr


@api_view(['POST'])
def analyze_image(request):
    """
    Analyze product from uploaded image using OCR and AI
    """
    if 'image' not in request.FILES:
        return Response(
            {
                'success': False,
                'error': 'NO_IMAGE',
                'message': 'No image file provided',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    image_file = request.FILES['image']
    
    # Validate image
    try:
        img = Image.open(image_file)
        img.verify()
        
        # Reopen for processing (verify closes the file)
        image_file.seek(0)
        img = Image.open(image_file)
        
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': 'INVALID_IMAGE',
                'message': 'Invalid or corrupted image file',
                'details': str(e),
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Check if OCR services are available
        from .ocr_service import TESSERACT_AVAILABLE, EASYOCR_AVAILABLE
        
        if not TESSERACT_AVAILABLE and not EASYOCR_AVAILABLE:
            # Return a helpful message if no OCR is available
            return Response(
                {
                    'success': False,
                    'error': 'OCR_NOT_AVAILABLE',
                    'message': 'OCR services are not yet installed. Please install pytesseract and/or easyocr.',
                    'details': 'Run: pip install pytesseract easyocr',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Step 1: Extract text using OCR
        print("Starting OCR extraction...")
        ocr_result = extract_ingredients_from_image(img)
        
        print(f"OCR completed: confidence={ocr_result.confidence}, quality={ocr_result.quality_score}")
        print(f"Has ingredients: {ocr_result.has_ingredients}")
        print(f"Extracted text: {ocr_result.text[:200]}...")
        
        # Step 2: Analyze ingredients with AI
        print("Starting AI analysis...")
        analysis_result = analyze_product_from_ocr(ocr_result)
        
        print(f"Analysis success: {analysis_result.get('success', True)}")
        
        # If analysis failed (low confidence or no ingredients)
        if not analysis_result.get('success', True):
            return Response(analysis_result, status=status.HTTP_200_OK)
        
        # Return successful analysis
        return Response(analysis_result, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Analysis error: {e}")
        print(traceback.format_exc())
        
        return Response(
            {
                'success': False,
                'error': 'ANALYSIS_FAILED',
                'message': 'An error occurred during analysis. Please try again.',
                'details': str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def analyze_url(request):
    """
    Analyze product from URL by scraping the page
    """
    url = request.data.get('url')
    
    if not url:
        return Response(
            {
                'success': False,
                'error': 'NO_URL',
                'message': 'No URL provided',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Import scraper service
        from .scraper_service import scrape_product_url
        
        # Step 1: Scrape the URL
        print(f"Scraping URL: {url}")
        scrape_result = scrape_product_url(url)
        
        print(f"Scrape result: success={scrape_result.get('success')}")
        
        # If scraping failed
        if not scrape_result.get('success'):
            return Response(
                {
                    'success': False,
                    'error': scrape_result.get('error', 'SCRAPING_FAILED'),
                    'message': scrape_result.get('message', 'Failed to extract ingredient information from the URL.'),
                    'suggestions': [
                        'Make sure the URL is a product page with ingredient information',
                        'Try a different product page or e-commerce site',
                        'Some sites may block automated access',
                        'Consider uploading an image of the ingredients instead',
                    ]
                },
                status=status.HTTP_200_OK
            )
        
        # Step 2: Create a mock OCR result from scraped text
        from .ocr_service import OCRResult
        
        ingredients_text = scrape_result.get('ingredients', '')
        print(f"Extracted ingredients: {ingredients_text[:200]}...")
        
        # Create OCR result with high confidence since it's from structured data
        ocr_result = OCRResult(
            text=ingredients_text,
            confidence=95.0,  # High confidence for scraped data
            method='web_scraping',
            raw_data={'url': url, 'scrape_result': scrape_result}
        )
        
        # Step 3: Analyze ingredients with AI
        print("Starting AI analysis...")
        from .ai_service import analyze_product_from_ocr
        analysis_result = analyze_product_from_ocr(ocr_result)
        
        # If analysis failed
        if not analysis_result.get('success', True):
            return Response(analysis_result, status=status.HTTP_200_OK)
        
        # Enhance with scraped product info
        if scrape_result.get('product_name'):
            analysis_result['product']['name'] = scrape_result['product_name']
        if scrape_result.get('brand'):
            analysis_result['product']['brand'] = scrape_result['brand']
        if scrape_result.get('image_url'):
            analysis_result['product_image_url'] = scrape_result['image_url']
        
        # Add source URL
        analysis_result['source_url'] = url
        
        # Return successful analysis
        return Response(analysis_result, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"URL analysis error: {e}")
        print(traceback.format_exc())
        
        return Response(
            {
                'success': False,
                'error': 'ANALYSIS_FAILED',
                'message': 'An error occurred while analyzing the URL. Please try again.',
                'details': str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint
    """
    # Check OCR availability
    from .ocr_service import TESSERACT_AVAILABLE, EASYOCR_AVAILABLE
    from .ai_service import OPENAI_AVAILABLE
    import os
    
    return Response({
        'status': 'healthy',
        'services': {
            'tesseract': TESSERACT_AVAILABLE,
            'easyocr': EASYOCR_AVAILABLE,
            'openai': OPENAI_AVAILABLE and bool(os.getenv('OPENAI_API_KEY')),
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def contact_submit(request):
    """
    Handle contact form submission
    """
    from .serializers import ContactMessageSerializer
    from django.core.mail import send_mail
    from django.conf import settings
    
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        instance = serializer.save()
        
        # Send Email Notification
        try:
            subject = f"New Contact Message: {instance.name}"
            message = f"You received a new message from FoodView contact form.\n\n" \
                      f"Name: {instance.name}\n" \
                      f"Email: {instance.email}\n" \
                      f"Message:\n{instance.message}\n\n" \
                      f"Sent at: {instance.created_at}"
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL_RECIPIENT],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            # We still return success since the message is saved in DB
            
        return Response({
            'success': True,
            'message': 'Your message has been received. We read every message and will get back to you if needed.'
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': 'Please correct the errors in the form.',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)
