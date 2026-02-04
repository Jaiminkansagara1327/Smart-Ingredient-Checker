from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import traceback
from .models import ContactMessage
from .serializers import ContactMessageSerializer
from .ai_service import analyze_product_from_text

@api_view(['POST'])
def analyze_text(request):
    """
    Analyze product from manually entered ingredient text
    """
    text = request.data.get('text')
    
    if not text or not text.strip():
        return Response(
            {
                'success': False,
                'error': 'NO_TEXT',
                'message': 'No ingredient text provided',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        print(f"Analyzing manual text: {text[:200]}...")
        
        # Analyze ingredients directly using the new text-based service method
        print("Starting analysis...")
        analysis_result = analyze_product_from_text(text.strip())
        
        # If analysis failed
        if not analysis_result.get('success', True):
            return Response(analysis_result, status=status.HTTP_200_OK)
        
        # Add metadata about manual entry
        analysis_result['input_method'] = 'manual'
        
        # Return successful analysis
        return Response(analysis_result, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Text analysis error: {e}")
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
def contact_submit(request):
    """
    Handle contact form submission
    """
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Message sent successfully!'
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def health_check(request):
    """
    Simple health check endpoint
    """
    return Response({
        'status': 'healthy',
        'services': {
            'text_analyzer': True
        }
    })
