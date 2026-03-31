from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """
    Simple email/password registration using Django's built-in User model.

    We store the user's email in both `email` and `username` to support
    simplejwt's `username`-based authentication.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        name = validated_data.get("name", "").strip()

        # Username is required by Django's default User model.
        return User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
        )


__all__ = ["RegisterSerializer"]

