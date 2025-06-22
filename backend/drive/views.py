import os
import io
import json
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from wallet.models import Wallet
from drive.utils import refresh_credentials_if_needed
from rest_framework.decorators import api_view

from dotenv import load_dotenv
load_dotenv()

# Allow insecure HTTP (for localhost only — NEVER use in production)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Load credentials from .env
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/drive/oauth2callback/")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.file"
]

# Configure OAuth Flow
flow = Flow.from_client_config(
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
    redirect_uri=REDIRECT_URI
)

# Step 1: Start Google OAuth
def initiate_auth(request):
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        include_granted_scopes='true'
    )
    return HttpResponseRedirect(auth_url)

# Step 2: Handle callback and save session
from django.views.decorators.http import require_GET

@require_GET
def oauth2_callback(request):
    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        creds = flow.credentials

        # Save token to session
        request.session['token'] = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        request.session.modified = True

        return JsonResponse({
            "message": "Google authentication successful.",
            "scopes": creds.scopes,
            "access_token": creds.token
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Step 3: Upload encrypted wallet backup
@csrf_exempt
def upload_wallet_backup(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        body = json.loads(request.body.decode('utf-8'))
        encrypted_data = body.get("encrypted_wallet_data")  # Must be dict
        wallet_name = body.get("wallet_name")
        password_hint = body.get("password_hint")
        public_key = request.headers.get("X-Wallet-Key")

        if not encrypted_data or not isinstance(encrypted_data, dict):
            return JsonResponse({"error": "Encrypted wallet data (as dict) is required"}, status=400)
        if not public_key:
            return JsonResponse({"error": "X-Wallet-Key header required"}, status=400)

        wallet = Wallet.objects.filter(public_key=public_key).first()
        if not wallet:
            return JsonResponse({"error": "Wallet not found"}, status=404)

        if wallet.backup_drive_file_id:
            return JsonResponse({
                "message": "Wallet is already linked with Drive",
                "file_id": wallet.backup_drive_file_id
            }, status=200)

        token_data = request.session.get('token')
        if not token_data:
            return JsonResponse({"error": "Google credentials not found. Please authenticate again."}, status=401)

        token_data, creds = refresh_credentials_if_needed(token_data)
        request.session['token'] = token_data

        service = build('drive', 'v3', credentials=creds)

        # Upload JSON file to Drive
        file_metadata = {
            'name': 'redrats_wallet_backup.txt',
            'mimeType': 'text/plain'
        }
        media_stream = io.BytesIO(json.dumps(encrypted_data).encode('utf-8'))
        media = MediaIoBaseUpload(media_stream, mimetype='text/plain')

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        file_id = uploaded_file.get("id")

        # Save metadata to wallet
        wallet.backup_drive_file_id = file_id
        wallet.wallet_name = wallet_name or wallet.wallet_name
        wallet.password_hint = password_hint or wallet.password_hint
        wallet.save()

        return JsonResponse({"file_id": file_id})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Step 4: Download wallet backup
@csrf_exempt
def download_wallet_backup(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        token_data = request.session.get('token')
        if not token_data:
            return JsonResponse({"error": "Google credentials not found. Please authenticate again."}, status=401)

        token_data, creds = refresh_credentials_if_needed(token_data)
        request.session['token'] = token_data
        service = build('drive', 'v3', credentials=creds)

        body = json.loads(request.body or '{}')
        file_id = body.get("file_id")

        if not file_id:
            public_key = request.headers.get("X-Wallet-Key")
            if not public_key:
                return JsonResponse({"error": "file_id or X-Wallet-Key header required"}, status=400)

            wallet = Wallet.objects.filter(public_key=public_key).first()
            if not wallet or not wallet.backup_drive_file_id:
                return JsonResponse({"error": "No backup file found for this wallet"}, status=404)
            file_id = wallet.backup_drive_file_id

        request_drive = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_drive)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)
        content = fh.read().decode('utf-8')
        data = json.loads(content)

        if not isinstance(data, dict) or "ciphertext" not in data or "salt" not in data:
            return JsonResponse({"error": "Invalid encrypted backup format"}, status=400)

        return JsonResponse({"encrypted_wallet_data": data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
