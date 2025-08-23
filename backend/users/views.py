# users/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import GoogleUser
from .serializers import GoogleUserSerializer
from drive.utils import get_user_info_from_session
from wallet.serializers import WalletSerializer

@api_view(['GET'])
def get_user_profile(request):
    try:
        user_info = get_user_info_from_session(request)
        sub = user_info.get("sub")
        user = GoogleUser.objects.get(sub=sub)

        profile_data = {
            "user": GoogleUserSerializer(user).data,
            "wallet": WalletSerializer(user.wallet).data if hasattr(user, "wallet") else None
        }

        return Response(profile_data)

    except Exception as e:
        return Response({"error": str(e)}, status=400)
