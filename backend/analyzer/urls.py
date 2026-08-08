"""
Analyzer App URL Configuration
RESTful Endpoints & Resource Aliases
"""
from django.urls import path
from . import views

urlpatterns = [
    # ── RESTful Resource Endpoints ──────────────────────────────
    path('products/search/', views.search_product, name='rest_search_product'),
    path('products/analyze/', views.analyze_product, name='rest_analyze_product'),
    path('products/alternatives/', views.get_alternatives, name='rest_get_alternatives'),
    path('analyses/text/', views.analyze_text, name='rest_analyze_text'),
    
    # ── Primary API Endpoints ────────────────────────────────────
    path('analyze/text/', views.analyze_text, name='analyze_text'),
    path('ai-providers/', views.ai_providers, name='ai_providers'),
    path('search-product/', views.search_product, name='search_product'),
    path('analyze-product/', views.analyze_product, name='analyze_product'),
    path('alternatives/', views.get_alternatives, name='get_alternatives'),
    path('contact/', views.contact_submit, name='contact_submit'),
    path('support/', views.support, name='support'),
    path('favorites/', views.favorites, name='favorites'),
    path('history/', views.analysis_history, name='analysis_history'),
    path('health/', views.health_check, name='health_check'),

    # Async task polling (Celery + Redis)
    path('task/<str:task_id>/', views.task_status, name='task_status'),

    # Payment Gateway Endpoints (RESTful & Legacy)
    path('payments/razorpay/order/', views.create_razorpay_order, name='rest_create_razorpay_order'),
    path('payments/razorpay/verify/', views.verify_razorpay_payment, name='rest_verify_razorpay_payment'),
    path('razorpay/create-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('razorpay/verify-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('razorpay/webhook/', views.razorpay_webhook, name='razorpay_webhook'),
]
