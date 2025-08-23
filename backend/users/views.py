# users/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import GoogleUser
from .serializers import GoogleUserSerializer
from wallet.serializers import WalletSerializer
from drive.utils import get_user_info_from_session
from rest_framework_simplejwt.tokens import RefreshToken
from .authentication import blacklist_user_tokens, get_authenticated_user
import logging

logger = logging.getLogger(__name__)

# -------------------------
# Helper functions
# -------------------------
def get_tokens_for_user(user):
    """Generates JWT access and refresh tokens for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

# -------------------------
# Public endpoints
# -------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Login or register GoogleUser via OAuth session.
    Expects session info validated by frontend.
    """
    try:
        user_info = get_user_info_from_session(request)
        sub = user_info.get("sub")
        if not sub:
            return Response({"error": "Invalid session"}, status=status.HTTP_401_UNAUTHORIZED)

        # Fetch or create user
        user, created = GoogleUser.objects.get_or_create(
            sub=sub,
            defaults={
                "email": user_info.get("email"),
                "name": user_info.get("name"),
            }
        )

        # Update last login
        user.last_login = user_info.get("last_login")
        user.save(update_fields=["last_login"])

        tokens = get_tokens_for_user(user)

        return Response({
            "user": GoogleUserSerializer(user).data,
            "tokens": tokens,
            "message": "Login successful" if not created else "User created and logged in"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Google login error: {str(e)}", exc_info=True)
        return Response({"error": "Login failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -------------------------
# Authenticated endpoints
# -------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Returns user profile and all wallets.
    """
    try:
        user = get_authenticated_user(request)
        if not user:
            return Response({"error": "Invalid authentication"}, status=status.HTTP_401_UNAUTHORIZED)

        wallets = getattr(user, "wallets", None)
        wallet_data = WalletSerializer(wallets.all(), many=True).data if wallets else []

        profile_data = {
            "user": GoogleUserSerializer(user).data,
            "wallets": wallet_data
        }
        return Response(profile_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error fetching profile: {str(e)}", exc_info=True)
        return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logs out the user by blacklisting the refresh token (if using JWT).
    """
    try:
        user = get_authenticated_user(request)
        if not user:
            return Response({"error": "Invalid authentication"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

        # Blacklist the provided refresh token
        token = RefreshToken(refresh_token)
        token.blacklist()

        # Optionally, blacklist all tokens for full logout
        # blacklist_user_tokens(user)

        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        return Response({"error": "Logout failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
