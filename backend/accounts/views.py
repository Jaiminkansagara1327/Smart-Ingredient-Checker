from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import RegisterSerializer


User = get_user_model()


from rest_framework import serializers as drf_serializers

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Accept `email` OR `username` for login.
    """
    email = drf_serializers.EmailField(required=False, write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow providing only `email` (we map it to username in validate()).
        if "username" in self.fields:
            self.fields["username"].required = False
            self.fields["username"].allow_blank = True

    def validate(self, attrs):
        # Map email to username for SimpleJWT
        if attrs.get("email") and not attrs.get("username"):
            attrs["username"] = attrs["email"].lower()
        return super().validate(attrs)


@extend_schema(tags=["Auth"], summary="JWT login (access + refresh)")
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


@extend_schema(tags=["Auth"], summary="Register a new user")
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"success": False, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = serializer.save()
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
        except Exception as e:
            import logging
            logger = logging.getLogger("accounts")
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            return Response(
                {"success": False, "message": f"Server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(tags=["Auth"], summary="Get current user profile")
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            # Get or create profile
            from analyzer.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
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
        except Exception as e:
            import logging
            logger = logging.getLogger("accounts")
            logger.error(f"Profile error: {str(e)}", exc_info=True)
            return Response(
                {"success": False, "message": f"Server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request):
        try:
            user = request.user
            from analyzer.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            if "health_goal" in request.data:
                profile.health_goal = request.data["health_goal"]
                profile.save()
                
            return Response({"success": True, "health_goal": profile.health_goal})
        except Exception as e:
            import logging
            logger = logging.getLogger("accounts")
            logger.error(f"Profile update error: {str(e)}", exc_info=True)
            return Response(
                {"success": False, "message": f"Server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(tags=["Auth"], summary="Login with Google")
class GoogleLoginAPIView(APIView):
    """
    Backend view to handle the Google Login. 
    Supports both `credential` (ID Token) and `access_token` (implicit flow).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("credential") # ID Token from standard btn
        access_token = request.data.get("access_token") # From custom hook btn
        
        if not token and not access_token:
            return Response({"success": False, "message": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        import os
        import requests as py_requests
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.db import transaction

        try:
            email, first_name, last_name = None, "", ""

            if token:
                # Flow A: Verify ID Token
                from google.oauth2 import id_token
                from google.auth.transport import requests as google_requests
                client_id = os.environ.get("GOOGLE_CLIENT_ID")
                idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
                email = idinfo['email']
                first_name = idinfo.get('given_name', '')
                last_name = idinfo.get('family_name', '')
            else:
                # Flow B: Verify Access Token via Google UserInfo API
                userinfo_res = py_requests.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if not userinfo_res.ok:
                    raise Exception("Failed to verify access token with Google")
                
                user_data = userinfo_res.json()
                email = user_data['email']
                first_name = user_data.get('given_name', '')
                last_name = user_data.get('family_name', '')

            # In this project, we map email to the username
            username = email.lower()

            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                    }
                )

                if created:
                    user.set_unusable_password()
                    user.save()
                    from analyzer.models import UserProfile
                    UserProfile.objects.get_or_create(user=user)

            # Generate local tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "success": True,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import logging
            logger = logging.getLogger("accounts")
            logger.error(f"Google Login error: {str(e)}", exc_info=True)
            return Response({
                "success": False, 
                "message": f"Login failed: {str(e)}"
            }, status=status.HTTP_401_UNAUTHORIZED)


__all__ = [
    "RegisterAPIView",
    "MeAPIView",
    "EmailTokenObtainPairView",
    "TokenRefreshView",
    "GoogleLoginAPIView",
]

