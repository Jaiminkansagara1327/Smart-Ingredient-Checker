from django.urls import path
from . import views

urlpatterns = [
    path('analyze/text/', views.analyze_text, name='analyze_text'),
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

    # Razorpay Full API Endpoints
    path('razorpay/create-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('razorpay/verify-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('razorpay/webhook/', views.razorpay_webhook, name='razorpay_webhook'),
]

