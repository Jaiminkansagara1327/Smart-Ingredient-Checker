"""
Authentication Views for Accounts.
"""
import logging
import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.mail import send_mail
from .models import EmailVerificationToken

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

def _set_refresh_cookie(response, refresh_token_str: str) -> None:
    """
    Attach the refresh token as an HttpOnly cookie.
    """
    response.set_cookie(
        key=settings.JWT_AUTH_COOKIE,
        value=refresh_token_str,
        max_age=settings.JWT_AUTH_COOKIE_MAX_AGE,
        httponly=settings.JWT_AUTH_COOKIE_HTTPONLY,
        secure=settings.JWT_AUTH_COOKIE_SECURE,
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
        path='/',
    )


def _clear_refresh_cookie(response) -> None:
    response.delete_cookie(
        key=settings.JWT_AUTH_COOKIE,
        path='/',
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
    )


def _generic_error(msg="A server error occurred.", http_status=status.HTTP_500_INTERNAL_SERVER_ERROR):
    return Response({"success": False, "message": msg}, status=http_status)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = drf_serializers.EmailField(required=False, write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "username" in self.fields:
            self.fields["username"].required = False
            self.fields["username"].allow_blank = True

    def validate(self, attrs):
        if attrs.get("email") and not attrs.get("username"):
            attrs["username"] = attrs["email"].lower()
        data = super().validate(attrs)
        try:
            if not self.user.emailverificationtoken.verified:
                raise drf_serializers.ValidationError("Please verify your email before logging in.")
        except EmailVerificationToken.DoesNotExist:
            pass
        return data


@extend_schema(tags=["Auth"], summary="JWT login")
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

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
    throttle_classes = [RegisterRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                user = serializer.save()
                token_obj, _ = EmailVerificationToken.objects.get_or_create(user=user)
                otp_code = token_obj.code
                print(f"[VERIFICATION CODE] User: {user.email} -> {otp_code}", flush=True)
                logger.info("[VERIFICATION CODE] User: %s -> %s", user.email, otp_code)
                
                subject = "Your Ingrexa verification code"
                body = f"Your 6-digit verification code is: {otp_code}"
                
                def send_email_bg(email_to, subj, msg):
                    email_sent = False
                    try:
                        send_mail(
                            subject=subj,
                            message=msg,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email_to],
                            fail_silently=False,
                        )
                        email_sent = True
                        logger.info("Verification email sent via SMTP to %s", email_to)
                    except Exception as smtp_err:
                        logger.warning("SMTP verification email failed: %s. Trying Resend API...", smtp_err)
                    
                    if not email_sent:
                        import requests as http_requests
                        resend_api_key = os.environ.get('RESEND_API_KEY', '')
                        if resend_api_key:
                            try:
                                resp = http_requests.post(
                                    'https://api.resend.com/emails',
                                    headers={
                                        'Authorization': f'Bearer {resend_api_key}',
                                        'Content-Type': 'application/json'
                                    },
                                    json={
                                        'from': 'Ingrexa Verification <onboarding@resend.dev>',
                                        'to': [email_to],
                                        'subject': subj,
                                        'text': msg
                                    },
                                    timeout=10,
                                )
                                if resp.status_code in [200, 201, 202]:
                                    logger.info("Verification email sent via Resend API to %s", email_to)
                                else:
                                    logger.error("Resend API failed with status %s: %s", resp.status_code, resp.text)
                            except Exception as e:
                                logger.error("Resend API error: %s", str(e))
                        else:
                            logger.warning("No Resend API key configured for fallback.")
                
                import threading
                threading.Thread(target=send_email_bg, args=(user.email, subject, body)).start()
        except Exception as e:
            logger.error("Registration error: %s", str(e), exc_info=True)
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


@extend_schema(tags=["Auth"], summary="Refresh access token")
class CookieTokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/
    Reads the refresh token from cookie and returns a new access token.
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
            new_refresh_str = str(refresh)
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


@extend_schema(tags=["Auth"], summary="Login with Google")
class GoogleLoginAPIView(APIView):
    """
    Handle Google OAuth login.
    Supports credential ID tokens and access tokens.
    """
    permission_classes = [AllowAny]
    throttle_classes = [GoogleLoginRateThrottle]

    def post(self, request):
        credential = request.data.get("credential")
        access_token = request.data.get("access_token")
        nonce = request.data.get("nonce", "")

        if not credential and not access_token:
            return Response(
                {"success": False, "message": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            email, first_name, last_name = None, "", ""

            if credential:
                import requests as py_requests
                from google.oauth2 import id_token
                from google.auth.transport import requests as google_requests

                client_id = os.environ.get("GOOGLE_CLIENT_ID")
                idinfo = id_token.verify_oauth2_token(
                    credential, google_requests.Request(), client_id
                )

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

@extend_schema(tags=["Auth"], summary="Verify email address via OTP code")
class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response(
                {"success": False, "message": "Email and code are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            token_obj = EmailVerificationToken.objects.get(user=user)
        except (User.DoesNotExist, EmailVerificationToken.DoesNotExist):
            return Response(
                {"success": False, "message": "Invalid email or verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token_obj.verified:
            return Response(
                {"success": True, "message": "Email already verified."},
                status=status.HTTP_200_OK,
            )

        if token_obj.is_expired():
            return Response(
                {"success": False, "message": "Verification code has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(token_obj.code) != str(code):
            return Response(
                {"success": False, "message": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_obj.verified = True
        token_obj.save()

        # Generate tokens so the user is immediately logged in
        refresh = RefreshToken.for_user(user)
        access_str = str(refresh.access_token)
        refresh_str = str(refresh)

        response = Response(
            {"success": True, "message": "Email verified successfully.", "access": access_str},
            status=status.HTTP_200_OK,
        )
        _set_refresh_cookie(response, refresh_str)
        return response

@extend_schema(tags=["Auth"], summary="Resend verification OTP code")
class ResendOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"success": False, "message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            token_obj = EmailVerificationToken.objects.get(user=user)
        except (User.DoesNotExist, EmailVerificationToken.DoesNotExist):
            return Response({"success": True, "message": "If the email exists, a new code has been sent."}, status=status.HTTP_200_OK)

        if token_obj.verified:
            return Response({"success": False, "message": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate new code
        import random
        from django.utils import timezone
        token_obj.code = ''.join(random.choices('0123456789', k=6))
        token_obj.created_at = timezone.now()
        token_obj.save()

        otp_code = token_obj.code
        print(f"[VERIFICATION CODE RESENT] User: {user.email} -> {otp_code}", flush=True)
        
        subject = "Your new Ingrexa verification code"
        body = f"Your new 6-digit verification code is: {otp_code}"
        
        def send_email_bg(email_to, subj, msg):
            try:
                send_mail(subj, msg, settings.DEFAULT_FROM_EMAIL, [email_to], fail_silently=False)
            except Exception as e:
                logger.error("Failed to resend verification email: %s", e)
                
        import threading
        threading.Thread(target=send_email_bg, args=(user.email, subject, body)).start()

        return Response({"success": True, "message": "OTP resent successfully."}, status=status.HTTP_200_OK)

__all__ = [
    "RegisterAPIView",
    "MeAPIView",
    "EmailTokenObtainPairView",
    "VerifyEmailAPIView",
    "CookieTokenRefreshView",
    "LogoutAPIView",
    "GoogleLoginAPIView",
    "ResendOTPAPIView",
]
