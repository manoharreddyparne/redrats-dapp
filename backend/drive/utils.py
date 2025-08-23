import io
import json
import requests
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.http import JsonResponse


def refresh_credentials_if_needed(token_data):
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
    token_data = request.session.get('token')
    if not token_data:
        raise Exception("Google credentials not found in session")

    token_data, creds = refresh_credentials_if_needed(token_data)
    request.session['token'] = token_data
    return build('drive', 'v3', credentials=creds)


def get_user_info_from_session(request):
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


def upload_encrypted_wallet_to_drive(request, encrypted_data, wallet_name=None, password_hint=None):
    from wallet.models import Wallet

    public_key = request.headers.get("X-Wallet-Key")
    if not public_key:
        return JsonResponse({"error": "X-Wallet-Key header required"}, status=400)

    wallet = Wallet.objects.filter(public_key=public_key).first()
    if not wallet:
        return JsonResponse({"error": "Wallet not found"}, status=404)

    token_data = request.session.get('token')
    if not token_data:
        return JsonResponse({"error": "Google credentials not found"}, status=401)

    token_data, creds = refresh_credentials_if_needed(token_data)
    request.session['token'] = token_data
    service = build('drive', 'v3', credentials=creds)

    media_stream = io.BytesIO(json.dumps(encrypted_data).encode('utf-8'))
    media = MediaIoBaseUpload(media_stream, mimetype='text/plain')

    uploaded_file = service.files().create(
        body={'name': 'redrats_wallet_backup.txt', 'mimeType': 'text/plain'},
        media_body=media,
        fields='id'
    ).execute()

    wallet.backup_drive_file_id = uploaded_file.get("id")
    wallet.wallet_name = wallet_name or wallet.wallet_name
    wallet.password_hint = password_hint or wallet.password_hint
    wallet.save()

    return JsonResponse({"file_id": wallet.backup_drive_file_id}, status=200)
