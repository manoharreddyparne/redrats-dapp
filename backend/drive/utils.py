import requests
import google.auth.transport.requests
from google.oauth2.credentials import Credentials

def refresh_credentials_if_needed(token_data):
    creds = Credentials(**token_data)
    request = google.auth.transport.requests.Request()

    if creds.expired and creds.refresh_token:
        creds.refresh(request)
        return {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }, creds

    return token_data, creds

def get_user_info_from_session(request):
    token_data = request.session.get('token')
    if not token_data:
        raise Exception("No Google token in session")

    # Refresh credentials if needed
    token_data, creds = refresh_credentials_if_needed(token_data)
    request.session['token'] = token_data  # Save updated token if refreshed

    # Fetch Google user info using the valid token
    access_token = creds.token
    response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code != 200:
        raise Exception("Failed to fetch user info from Google")

    return response.json()
