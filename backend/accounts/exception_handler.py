"""
Secure DRF exception handler.
"""
import logging
from django.conf import settings
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("django.security")


def safe_exception_handler(exc, context):
    """
    Drop-in replacement for rest_framework.views.exception_handler.
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception — Django will return a 500.
        logger.error(
            "Unhandled exception in view %s: %s",
            context.get("view"),
            str(exc),
            exc_info=True,
        )
        if not settings.DEBUG:
            return Response(
                {"success": False, "message": "An internal server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # In DEBUG, let Django's default error page take over.
        return None

    # Scrub 5xx details in production
    if not settings.DEBUG and response.status_code >= 500:
        response.data = {"success": False, "message": "An internal server error occurred."}

    return response
