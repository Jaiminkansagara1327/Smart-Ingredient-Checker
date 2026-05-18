from django.urls import path

from .views import (
    EmailTokenObtainPairView,
    VerifyEmailAPIView,
    CookieTokenRefreshView,
    LogoutAPIView,
    MeAPIView,
    RegisterAPIView,
    GoogleLoginAPIView,
)


urlpatterns = [
    path("register/",       RegisterAPIView.as_view(),        name="register"),
    path("token/",          EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('verify-email/<uuid:token>/', VerifyEmailAPIView.as_view(), name='verify-email'),
    # Cookie-based refresh replaces the raw SimpleJWT TokenRefreshView (finding #1)
    path("token/refresh/",  CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/",         LogoutAPIView.as_view(),           name="logout"),
    path("google-login/",   GoogleLoginAPIView.as_view(),      name="google_login"),
    path("me/",             MeAPIView.as_view(),               name="me"),
]
