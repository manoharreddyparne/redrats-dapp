# drive/utils.py
import io
import json
import requests
from django.http import JsonResponse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from wallet.models import Wallet
import google.auth.transport.requests

# -------------------------
# Token and Credentials
# -------------------------
def refresh_credentials_if_needed(token_data):
    """
    Refresh Google OAuth credentials if expired.
    Returns updated token_data and Credentials object.
    """
    creds = Credentials(**token_data)
    request = google.auth.transport.requests.Request()

    if creds.expired and creds.refresh_token:
        creds.refresh(request)
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }

    return token_data, creds


def get_google_drive_service(request):
    """
    Return authenticated Google Drive service instance.
    """
    token_data = request.session.get('token')
    if not token_data:
        raise Exception("Google credentials not found in session")

    token_data, creds = refresh_credentials_if_needed(token_data)
    request.session['token'] = token_data
    return build('drive', 'v3', credentials=creds)


def get_user_info_from_session(request):
    """
    Fetch Google user info (email, sub, name) from session token.
    """
    token_data = request.session.get('token')
    if not token_data:
        raise Exception("No Google token in session")

    token_data, creds = refresh_credentials_if_needed(token_data)
    request.session['token'] = token_data

    response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {creds.token}"}
    )

    if response.status_code != 200:
        raise Exception("Failed to fetch user info from Google")

    return response.json()


# -------------------------
# Wallet Drive Utilities
# -------------------------
def upload_encrypted_wallet_to_drive(request, encrypted_data, wallet_name=None, password_hint=None):
    """
    Upload encrypted wallet data to Google Drive and link with Wallet object.
    Requires `X-Wallet-Key` header or session wallet access.
    """
    # 1. Identify wallet
    public_key = request.headers.get("X-Wallet-Key") or request.session.get("wallet_access", {}).get("public_key")
    if not public_key:
        return JsonResponse({"error": "X-Wallet-Key header or session wallet access required"}, status=400)

    wallet = Wallet.objects.filter(public_key=public_key).first()
    if not wallet:
        return JsonResponse({"error": "Wallet not found"}, status=404)

    # 2. Get authenticated Google Drive service
    try:
        service = get_google_drive_service(request)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=401)

    # 3. Upload data
    media_stream = io.BytesIO(json.dumps(encrypted_data).encode('utf-8'))
    media = MediaIoBaseUpload(media_stream, mimetype='text/plain')

    uploaded_file = service.files().create(
        body={'name': 'redrats_wallet_backup.txt', 'mimeType': 'text/plain'},
        media_body=media,
        fields='id'
    ).execute()

    # 4. Update wallet
    wallet.backup_drive_file_id = uploaded_file.get("id")
    wallet.wallet_name = wallet_name or wallet.wallet_name
    wallet.password_hint = password_hint or wallet.password_hint
    wallet.save()

    return JsonResponse({"file_id": wallet.backup_drive_file_id}, status=200)


def download_wallet_backup_from_drive(request, wallet=None, file_id=None):
    """
    Download encrypted wallet data from Drive by file_id or Wallet object.
    Returns JSON with encrypted data.
    """
    # Identify wallet
    if not wallet:
        public_key = request.headers.get("X-Wallet-Key") or request.session.get("wallet_access", {}).get("public_key")
        if not public_key:
            return JsonResponse({"error": "X-Wallet-Key header or session wallet access required"}, status=400)
        wallet = Wallet.objects.filter(public_key=public_key).first()
        if not wallet or not wallet.backup_drive_file_id:
            return JsonResponse({"error": "No backup file found for this wallet"}, status=404)
        file_id = wallet.backup_drive_file_id

    # Get authenticated Drive service
    try:
        service = get_google_drive_service(request)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=401)

    # Download file
    request_drive = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request_drive)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    fh.seek(0)
    content = fh.read().decode('utf-8')
    try:
        data = json.loads(content)
    except Exception:
        return JsonResponse({"error": "Failed to parse wallet backup content"}, status=400)

    if not isinstance(data, dict) or "ciphertext" not in data or "salt" not in data:
        return JsonResponse({"error": "Invalid encrypted backup format"}, status=400)

    return JsonResponse({"encrypted_wallet_data": data}, status=200)
