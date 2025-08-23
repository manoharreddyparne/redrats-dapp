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
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from wallet.models import Wallet
from drive.utils import refresh_credentials_if_needed, upload_encrypted_wallet_to_drive
from users.authentication import get_authenticated_user

load_dotenv()
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/drive/oauth2callback/")
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.file"
]

# -------------------------
# Helper functions
# -------------------------
def get_flow(state=None):
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
        state=state
    )

def IsAuthenticatedWalletOwner(view_func):
    """Decorator to ensure that the request user owns the wallet specified by X-Wallet-Key."""
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
            return JsonResponse({"error": "Wallet not found or not owned by user"}, status=403)

        request.wallet = wallet  # attach wallet to request for downstream usage
        return view_func(request, *args, **kwargs)
    return wrapper

# -------------------------
# OAuth Endpoints
# -------------------------
def initiate_auth(request):
    """Start Google OAuth2 flow."""
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state
    request.session.modified = True
    flow = get_flow(state)
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        include_granted_scopes='true',
        state=state
    )
    return HttpResponseRedirect(auth_url)

@csrf_exempt
@require_GET
def oauth2_callback(request):
    """Handle OAuth2 callback and store credentials in session."""
    try:
        state_from_google = request.GET.get("state")
        state_from_session = request.session.get("oauth_state")

        if not state_from_google or not state_from_session:
            return JsonResponse({"error": "Missing state"}, status=400)
        if state_from_google != state_from_session:
            return JsonResponse({"error": "CSRF Warning! State mismatch."}, status=403)

        flow = get_flow(state_from_session)
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        creds = flow.credentials

        request.session['token'] = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        request.session.modified = True

        return JsonResponse({"message": "Google Drive authenticated successfully."}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# -------------------------
# Wallet Backup / Restore Endpoints
# -------------------------
@csrf_exempt
@IsAuthenticatedWalletOwner
def upload_wallet_backup(request):
    """Upload wallet backup to Google Drive (POST only)."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        body = json.loads(request.body.decode('utf-8'))
        encrypted_data = body.get("encrypted_wallet_data")
        wallet_name = body.get("wallet_name")
        password_hint = body.get("password_hint")
        return upload_encrypted_wallet_to_drive(
            request,
            encrypted_data,
            wallet_name=wallet_name,
            password_hint=password_hint
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@IsAuthenticatedWalletOwner
def download_wallet_backup(request):
    """Download wallet backup from Google Drive (POST only)."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        token_data = request.session.get('token')
        if not token_data:
            return JsonResponse({"error": "Google credentials not found."}, status=401)

        token_data, creds = refresh_credentials_if_needed(token_data)
        request.session['token'] = token_data
        service = build('drive', 'v3', credentials=creds)

        file_id = request.wallet.backup_drive_file_id
        if not file_id:
            return JsonResponse({"error": "No backup file found for this wallet"}, status=404)

        request_drive = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_drive)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        data = json.loads(fh.read().decode('utf-8'))

        if not isinstance(data, dict) or "ciphertext" not in data or "salt" not in data:
            return JsonResponse({"error": "Invalid backup format"}, status=400)

        return JsonResponse({"encrypted_wallet_data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
