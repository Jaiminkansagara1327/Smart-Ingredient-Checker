from django.urls import path

from .views import (
    EmailTokenObtainPairView,
    MeAPIView,
    RegisterAPIView,
    GoogleLoginAPIView,
)
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("google-login/", GoogleLoginAPIView.as_view(), name="google_login"),
    path("me/", MeAPIView.as_view(), name="me"),
]

