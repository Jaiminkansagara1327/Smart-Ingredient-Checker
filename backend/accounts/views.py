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


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Accept `email` OR `username` for login.

    Since we store `email` in the `username` field for our default User model,
    this maps email-based login to the underlying username-based JWT flow.
    """

    # Accept email in addition to username.
    # SimpleJWT will still inject a `username` field in `__init__`, so we must
    # loosen its required-ness after calling super().
    from rest_framework import serializers as drf_serializers

    email = drf_serializers.EmailField(required=False, write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow providing only `email` (we map it to username in validate()).
        if "username" in self.fields:
            self.fields["username"].required = False
            self.fields["username"].allow_blank = True

    def validate(self, attrs):
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


@extend_schema(tags=["Auth"], summary="Get current user profile")
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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

    def patch(self, request):
        user = request.user
        from analyzer.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        if "health_goal" in request.data:
            profile.health_goal = request.data["health_goal"]
            profile.save()
            
        return Response({"success": True, "health_goal": profile.health_goal})


__all__ = [
    "RegisterAPIView",
    "MeAPIView",
    "EmailTokenObtainPairView",
    "TokenRefreshView",
]

