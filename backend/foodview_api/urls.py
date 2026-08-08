"""
URL Configuration for Ingrexa API Engine
Includes Professional API Versioning (v1) and OpenAPI documentation
"""
from django.contrib import admin
from django.urls import path, include
from accounts.views import AdditiveListAPIView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # ── Admin Panel ──────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── API v1 Routes (Standardized Professional Versioning) ──
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/additives/', AdditiveListAPIView.as_view(), name='v1-additive-list'),
    path('api/v1/', include('analyzer.urls')),

    # ── Legacy / Unversioned API Routes (Backwards Compatibility) ──
    path('api/auth/', include('accounts.urls')),
    path('api/additives/', AdditiveListAPIView.as_view(), name='additive-list'),
    path('api/', include('analyzer.urls')),

    # ── OpenAPI 3.0 & Swagger/ReDoc Documentation ────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='v1-schema'),
    path('api/docs/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/docs/', SpectacularRedocView.as_view(url_name='v1-schema'), name='v1-redoc'),
    path('api/v1/swagger/', SpectacularSwaggerView.as_view(url_name='v1-schema'), name='v1-swagger'),
]
