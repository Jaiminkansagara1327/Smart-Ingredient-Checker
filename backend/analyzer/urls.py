from django.urls import path
from . import views

urlpatterns = [
    path('analyze/image/', views.analyze_image, name='analyze_image'),
    path('analyze/url/', views.analyze_url, name='analyze_url'),
    path('health/', views.health_check, name='health_check'),
]
