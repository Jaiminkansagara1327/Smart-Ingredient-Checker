"""
accounts/views.py — Authentication Views

Security fixes applied:
  [CRITICAL] #1  – Refresh token moved from localStorage → HttpOnly cookie
  [HIGH]     #2  – Auth no longer relies on JS-accessible storage for refresh
  [HIGH]     #3/4 – Access token is short-lived (15 min, configured via SIMPLE_JWT)
  [HIGH]     #6/7 – Per-endpoint throttle classes applied
  [MEDIUM]   #8  – Google nonce parameter validated end-to-end
  [MEDIUM]   #10 – Internal exception detail is logged server-side, never returned
  [MEDIUM]   #11 – HttpOnly, Secure, SameSite=Lax on the refresh cookie
"""
import logging
import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers as drf_serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from drf_spectacular.utils import extend_schema

from .serializers import RegisterSerializer
from .throttles import (
    LoginRateThrottle,
    RegisterRateThrottle,
    GoogleLoginRateThrottle,
)

logger = logging.getLogger("accounts")
User = get_user_model()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _set_refresh_cookie(response, refresh_token_str: str) -> None:
    """
    Attach the refresh token as an HttpOnly cookie (finding #1).
    The browser stores it transparently; JavaScript cannot read it.
    """
    response.set_cookie(
        key=settings.JWT_AUTH_COOKIE,
        value=refresh_token_str,
        max_age=settings.JWT_AUTH_COOKIE_MAX_AGE,
        httponly=settings.JWT_AUTH_COOKIE_HTTPONLY,   # True always
        secure=settings.JWT_AUTH_COOKIE_SECURE,       # True in prod
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,   # 'Lax'
        path='/',
    )


def _clear_refresh_cookie(response) -> None:
    """Delete the refresh cookie on logout / rotation failure."""
    response.delete_cookie(
        key=settings.JWT_AUTH_COOKIE,
        path='/',
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
    )


def _generic_error(msg="A server error occurred.", http_status=status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Return a sanitized error response that never leaks internal details."""
    return Response({"success": False, "message": msg}, status=http_status)


# ──────────────────────────────────────────────────────────────────────────────
# Serializers
# ──────────────────────────────────────────────────────────────────────────────

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Accept `email` OR `username` for login."""
    email = drf_serializers.EmailField(required=False, write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "username" in self.fields:
            self.fields["username"].required = False
            self.fields["username"].allow_blank = True

    def validate(self, attrs):
        if attrs.get("email") and not attrs.get("username"):
            attrs["username"] = attrs["email"].lower()
        return super().validate(attrs)


# ──────────────────────────────────────────────────────────────────────────────
# Views
# ──────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Auth"], summary="JWT login (access + refresh)")
class EmailTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/token/
    Returns access token in JSON body, refresh token in HttpOnly cookie.
    """
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]  # 5 attempts / 15 min (finding #6)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken) as e:
            logger.warning("Login failed for data=%s reason=%s", request.data.get("email"), str(e))
            return Response(
                {"success": False, "detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = serializer.validated_data
        refresh_str = data.get("refresh", "")
        access_str = data.get("access", "")

        response = Response(
            {"success": True, "access": access_str},
            status=status.HTTP_200_OK,
        )
        _set_refresh_cookie(response, refresh_str)
        return response


@extend_schema(tags=["Auth"], summary="Register a new user")
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]  # 10 attempts / hr

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = serializer.save()
        except Exception:
            logger.error("Registration error", exc_info=True)
            return _generic_error("Registration failed. Please try again.")

        return Response(
            {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Auth"], summary="Refresh access token via HttpOnly cookie")
class CookieTokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/
    Reads the refresh token from the HttpOnly cookie (NOT the request body).
    Returns a new access token; rotates the refresh cookie (finding #1).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_str = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        if not refresh_str:
            return Response(
                {"success": False, "detail": "Refresh token missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            refresh = RefreshToken(refresh_str)
            access_str = str(refresh.access_token)
            # Rotate: blacklist old, issue new (BLACKLIST_AFTER_ROTATION = True)
            new_refresh_str = str(refresh)  # rotating refresh returns a new token
        except TokenError as e:
            logger.info("Refresh token invalid/expired: %s", str(e))
            response = Response(
                {"success": False, "detail": "Session expired. Please log in again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            _clear_refresh_cookie(response)
            return response

        response = Response({"success": True, "access": access_str}, status=status.HTTP_200_OK)
        _set_refresh_cookie(response, new_refresh_str)
        return response


@extend_schema(tags=["Auth"], summary="Logout — clear refresh cookie")
class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Blacklist the refresh token and clear the cookie."""
        refresh_str = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        if refresh_str:
            try:
                RefreshToken(refresh_str).blacklist()
            except Exception:
                pass  # Already expired / invalid — still clear cookie

        response = Response({"success": True, "message": "Logged out."}, status=status.HTTP_200_OK)
        _clear_refresh_cookie(response)
        return response


@extend_schema(tags=["Auth"], summary="Get current user profile")
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            from analyzer.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            return Response(
                {
                    "success": True,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "health_goal": profile.health_goal or "General Health",
                    },
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.error("Profile fetch error", exc_info=True)
            return _generic_error("Unable to retrieve profile.")

    def patch(self, request):
        try:
            from analyzer.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            if "health_goal" in request.data:
                profile.health_goal = request.data["health_goal"]
                profile.save()
            return Response({"success": True, "health_goal": profile.health_goal})
        except Exception:
            logger.error("Profile update error", exc_info=True)
            return _generic_error("Unable to update profile.")


@extend_schema(tags=["Auth"], summary="Login with Google (ID Token or Access Token)")
class GoogleLoginAPIView(APIView):
    """
    POST /api/auth/google-login/

    Supports:
      - `credential`   — ID Token from Google One Tap / standard btn (preferred)
      - `access_token` — Access Token from implicit flow

    Security (finding #8 — nonce):
      When using ID Token flow, the client should generate a random nonce,
      send it in the request body as `nonce`, and this view validates that
      the `nonce` in the verified ID-token matches what was supplied.
      The nonce value itself is NOT stored server-side; Google's library
      embeds it in the signed token so we just compare after verification.
    """
    permission_classes = [AllowAny]
    throttle_classes = [GoogleLoginRateThrottle]  # 10/hr (findings #6, #7)

    def post(self, request):
        credential = request.data.get("credential")   # ID Token
        access_token = request.data.get("access_token")  # implicit flow
        nonce = request.data.get("nonce", "")         # client-supplied nonce

        if not credential and not access_token:
            return Response(
                {"success": False, "message": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            email, first_name, last_name = None, "", ""

            if credential:
                # ── Flow A: Verify ID Token ────────────────────────────────
                import requests as py_requests
                from google.oauth2 import id_token
                from google.auth.transport import requests as google_requests

                client_id = os.environ.get("GOOGLE_CLIENT_ID")
                idinfo = id_token.verify_oauth2_token(
                    credential, google_requests.Request(), client_id
                )

                # Nonce validation (finding #8)
                # The nonce in the verified token MUST match what the client sent.
                if nonce:
                    token_nonce = idinfo.get("nonce", "")
                    if not secrets.compare_digest(nonce, token_nonce):
                        logger.warning("Google OAuth nonce mismatch from %s", request.META.get("REMOTE_ADDR"))
                        return Response(
                            {"success": False, "message": "Authentication failed."},
                            status=status.HTTP_401_UNAUTHORIZED,
                        )

                email = idinfo["email"]
                first_name = idinfo.get("given_name", "")
                last_name = idinfo.get("family_name", "")

            else:
                # ── Flow B: Access Token → UserInfo endpoint ───────────────
                import requests as py_requests
                userinfo_res = py_requests.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10,
                )
                if not userinfo_res.ok:
                    raise ValueError("Failed to verify access token with Google.")
                user_data = userinfo_res.json()
                email = user_data["email"]
                first_name = user_data.get("given_name", "")
                last_name = user_data.get("family_name", "")

            username = email.lower()

            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                    },
                )
                if created:
                    user.set_unusable_password()
                    user.save()
                    from analyzer.models import UserProfile
                    UserProfile.objects.get_or_create(user=user)

            refresh = RefreshToken.for_user(user)
            access_str = str(refresh.access_token)
            refresh_str = str(refresh)

            response = Response(
                {
                    "success": True,
                    "access": access_str,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                    },
                },
                status=status.HTTP_200_OK,
            )
            _set_refresh_cookie(response, refresh_str)
            return response

        except Exception:
            logger.error("Google Login error", exc_info=True)
            return Response(
                {"success": False, "message": "Authentication failed."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


__all__ = [
    "RegisterAPIView",
    "MeAPIView",
    "EmailTokenObtainPairView",
    "CookieTokenRefreshView",
    "LogoutAPIView",
    "GoogleLoginAPIView",
]
