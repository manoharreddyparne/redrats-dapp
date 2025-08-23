# users/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from .models import GoogleUser

class GoogleUserJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class for GoogleUser.
    Returns None if no token is provided instead of crashing.
    """

    def authenticate(self, request):
        # ⚡ Safe header check
        header = self.get_header(request)
        if header is None:
            return None  # No token, return None safely

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None  # No token after parsing, return None safely

        validated_token = self.get_validated_token(raw_token)
        sub = validated_token.get("sub")
        if not sub:
            raise AuthenticationFailed("Token payload missing 'sub'", code="invalid_token")

        try:
            user = GoogleUser.objects.get(sub=sub)
        except GoogleUser.DoesNotExist:
            raise AuthenticationFailed("User not found", code="user_not_found")

        return (user, validated_token)

# -------------------------
# Utility functions
# -------------------------
def blacklist_user_tokens(user: GoogleUser):
    """
    Blacklist all outstanding refresh tokens for the given user.
    """
    tokens = OutstandingToken.objects.filter(user_id=user.id)
    for token in tokens:
        _, created = BlacklistedToken.objects.get_or_create(token=token)


def get_authenticated_user(request):
    """
    Safely get GoogleUser from request using JWT authentication.
    Returns None if authentication fails.
    """
    auth = GoogleUserJWTAuthentication()
    try:
        user, token = auth.authenticate(request)
        return user
    except AuthenticationFailed:
        return None
