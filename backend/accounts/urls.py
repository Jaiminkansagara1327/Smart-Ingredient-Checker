from django.urls import path

from .views import (
    EmailTokenObtainPairView,
    VerifyEmailAPIView,
    CookieTokenRefreshView,
    LogoutAPIView,
    MeAPIView,
    RegisterAPIView,
    GoogleLoginAPIView,
    ResendOTPAPIView,
)


urlpatterns = [
    path("register/",       RegisterAPIView.as_view(),        name="register"),
    path("token/",          EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('verify-email/', VerifyEmailAPIView.as_view(), name='verify-email'),
    path('resend-otp/', ResendOTPAPIView.as_view(), name='resend-otp'),
    path("token/refresh/",  CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/",         LogoutAPIView.as_view(),           name="logout"),
    path("google-login/",   GoogleLoginAPIView.as_view(),      name="google_login"),
    path("me/",             MeAPIView.as_view(),               name="me"),
]
