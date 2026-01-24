from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from PIL import Image
import io


def generate_mock_analysis():
    """Generate mock analysis data for demonstration"""
    return {
        'product': {
            'name': 'Organic Whole Wheat Bread',
            'brand': "Nature's Best",
            'category': 'Bakery • Bread',
        },
        'verdict': 'Suitable for daily consumption, good source of fiber and nutrients with minimal processing.',
        'score': 8,
        'suitability': {
            'goodFor': 'High-fiber diets, heart health, sustained energy, digestive wellness',
            'cautionFor': 'Gluten sensitivity, low-carb diets, blood sugar management',
            'avoidFor': 'Celiac disease, wheat allergies, strict keto diet',
        },
        'ingredientGroups': [
            {
                'title': 'Grains & Flours',
                'description': 'Whole wheat flour provides fiber, vitamins, and minerals',
                'note': 'Contains gluten - primary allergen concern',
            },
            {
                'title': 'Leavening Agents',
                'description': 'Yeast and natural fermentation for texture and digestibility',
                'note': 'Generally safe, aids in nutrient absorption',
            },
            {
                'title': 'Natural Sweeteners',
                'description': 'Honey or molasses for mild sweetness and moisture',
                'note': 'Low glycemic impact in small amounts',
            },
            {
                'title': 'Preservatives',
                'description': 'Minimal use of natural preservatives like vinegar',
                'note': 'Clean label - no artificial additives',
            },
        ],
        'flags': [
            {'icon': '🌾', 'text': 'Contains Gluten'},
            {'icon': '🍯', 'text': 'Natural Sweeteners'},
            {'icon': '✨', 'text': 'Minimal Processing'},
            {'icon': '🌱', 'text': 'Organic Certified'},
        ],
    }


@api_view(['POST'])
def analyze_image(request):
    """
    Analyze product from uploaded image
    """
    if 'image' not in request.FILES:
        return Response(
            {'error': 'No image file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    image_file = request.FILES['image']
    
    # Validate image
    try:
        img = Image.open(image_file)
        img.verify()
    except Exception as e:
        return Response(
            {'error': 'Invalid image file'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # TODO: Implement actual image analysis
    # For now, return mock data
    analysis_data = generate_mock_analysis()
    
    return Response(analysis_data, status=status.HTTP_200_OK)


@api_view(['POST'])
def analyze_url(request):
    """
    Analyze product from URL
    """
    url = request.data.get('url')
    
    if not url:
        return Response(
            {'error': 'No URL provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # TODO: Implement actual URL scraping and analysis
    # For now, return mock data
    analysis_data = generate_mock_analysis()
    
    return Response(analysis_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint
    """
    return Response({'status': 'healthy'}, status=status.HTTP_200_OK)
