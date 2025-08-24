# drive/views.py

import os
import io
import json
import secrets
from functools import wraps
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from wallet.models import Wallet
from drive.utils import refresh_credentials_if_needed, upload_encrypted_wallet_to_drive
from users.authentication import get_authenticated_user

load_dotenv()
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/drive/oauth2callback/"
)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.file",
]

# -------------------------
# Helpers
# -------------------------
def get_flow(state=None):
    """Create an OAuth2 Flow object."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=state,
    )


def IsAuthenticatedWalletOwner(view_func):
    """Decorator to ensure request is from authenticated user who owns the wallet."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = get_authenticated_user(request)
        if not user:
            return JsonResponse({"error": "Authentication required"}, status=401)

        public_key = request.headers.get("X-Wallet-Key")
        if not public_key:
            return JsonResponse({"error": "X-Wallet-Key header required"}, status=400)

        wallet = Wallet.objects.filter(public_key=public_key, user=user).first()
        if not wallet:
            return JsonResponse(
                {"error": "Wallet not found or not owned by user"}, status=403
            )

        request.wallet = wallet
        return view_func(request, *args, **kwargs)

    return wrapper


# -------------------------
# OAuth Endpoints
# -------------------------
def initiate_auth(request):
    """Redirect-based OAuth2 flow to Google consent screen."""
    if "oauth_state" not in request.session:
        request.session["oauth_state"] = secrets.token_urlsafe(32)
        request.session.modified = True

    flow = get_flow(state=request.session["oauth_state"])
    auth_url, _ = flow.authorization_url(
        prompt="consent", access_type="offline", include_granted_scopes="true"
    )
    return HttpResponseRedirect(auth_url)


def get_oauth_url(request):
    """Return Google OAuth URL for frontend (JSON) with wallet_id tracked in session."""
    wallet_id = request.GET.get("wallet_id")
    if not wallet_id:
        return JsonResponse({"error": "wallet_id is required"}, status=400)

    # Ensure oauth_state exists
    if "oauth_state" not in request.session:
        request.session["oauth_state"] = secrets.token_urlsafe(32)
    request.session["wallet_id_for_oauth"] = wallet_id
    request.session.modified = True

    flow = get_flow(state=request.session["oauth_state"])
    auth_url, _ = flow.authorization_url(
        prompt="consent", access_type="offline", include_granted_scopes="true"
    )
    return JsonResponse({"url": auth_url})


@csrf_exempt
def oauth2_callback(request):
    """Handle OAuth2 callback, store credentials, then redirect to frontend."""
    try:
        state_from_google = request.GET.get("state")
        state_from_session = request.session.get("oauth_state")

        if not state_from_google or not state_from_session:
            return HttpResponseRedirect(
                f"{FRONTEND_URL}/wallet-access/set-backup-password/?error=missing_state"
            )

        if state_from_google != state_from_session:
            return HttpResponseRedirect(
                f"{FRONTEND_URL}/wallet-access/set-backup-password/?error=csrf_mismatch"
            )

        # Fetch token
        flow = get_flow(state_from_session)
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        creds = flow.credentials

        # Save credentials
        request.session["token"] = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
        request.session.modified = True
        del request.session["oauth_state"]

        # Get wallet ID stored in session
        wallet_id = request.session.pop("wallet_id_for_oauth", None)

        # Redirect frontend with wallet info
        redirect_url = f"{FRONTEND_URL}/wallet-access/set-backup-password/?wallet={wallet_id}"
        return HttpResponseRedirect(redirect_url)

    except Exception as e:
        return HttpResponseRedirect(
            f"{FRONTEND_URL}/wallet-access/set-backup-password/?error={str(e)}"
        )


# -------------------------
# Backup / Restore
# -------------------------
@csrf_exempt
@IsAuthenticatedWalletOwner
def upload_wallet_backup(request):
    """Upload encrypted wallet backup to Drive."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        body = json.loads(request.body.decode("utf-8"))
        encrypted_data = body.get("encrypted_wallet_data")
        wallet_name = body.get("wallet_name")
        password_hint = body.get("password_hint")

        if not encrypted_data:
            return JsonResponse({"error": "Missing encrypted wallet data"}, status=400)

        return upload_encrypted_wallet_to_drive(
            request,
            encrypted_data,
            wallet_name=wallet_name,
            password_hint=password_hint,
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@IsAuthenticatedWalletOwner
def download_wallet_backup(request):
    """Download encrypted wallet backup from Drive."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        token_data = request.session.get("token")
        if not token_data:
            return JsonResponse({"error": "Google credentials not found"}, status=401)

        token_data, creds = refresh_credentials_if_needed(token_data)
        request.session["token"] = token_data

        service = build("drive", "v3", credentials=creds)
        file_id = request.wallet.backup_drive_file_id

        if not file_id:
            return JsonResponse({"error": "No backup file found for this wallet"}, status=404)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, service.files().get_media(fileId=file_id))
        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)
        data = json.loads(fh.read().decode("utf-8"))

        if not isinstance(data, dict) or "ciphertext" not in data or "salt" not in data:
            return JsonResponse({"error": "Invalid backup format"}, status=400)

        return JsonResponse({"encrypted_wallet_data": data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_GET
def oauth_check(request):
    """Check if user has authenticated Google Drive."""
    token_data = request.session.get("token")
    return JsonResponse({"success": bool(token_data)})
