from django.urls import path
from . import views

urlpatterns = [
    path('analyze/text/', views.analyze_text, name='analyze_text'),
    path('contact/', views.contact_submit, name='contact_submit'),
    path('health/', views.health_check, name='health_check'),
]
