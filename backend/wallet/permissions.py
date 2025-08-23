from rest_framework.permissions import BasePermission
from drive.utils import get_user_info_from_session
from users.models import GoogleUser
from wallet.models import Wallet
import logging

logger = logging.getLogger(__name__)

class IsAuthenticatedWalletOwner(BasePermission):
    """
    Allow access only if user is the owner of the wallet (via Google session or mnemonic session).
    """

    def has_object_permission(self, request, view, obj: Wallet):
        # 1️⃣ Try Google session
        try:
            user_info = get_user_info_from_session(request)
            sub = user_info.get("sub")
            if sub and obj.user.sub == sub:
                return True
        except Exception as e:
            logger.debug(f"Google session check failed: {str(e)}")

        # 2️⃣ Try mnemonic session
        wallet_access = request.session.get("wallet_access")
        if wallet_access and wallet_access.get("method") == "mnemonic":
            if obj.public_key == wallet_access.get("public_key"):
                return True

        logger.warning(f"Unauthorized wallet access attempt: wallet={obj.public_key}")
        return False
