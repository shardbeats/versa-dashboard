import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

TOKEN_ENV_VAR = "GMAIL_TOKEN_JSON"
LOCAL_CLIENT_SECRET_PATH = "client_secret.json"
LOCAL_GMAIL_TOKEN_PATH = "gmail_token.json"


def authenticate_gmail() -> Credentials:
    """
    Authenticate with the Gmail API.

    In Cloud Run, credentials are read from the GMAIL_TOKEN_JSON
    environment variable, supplied through Secret Manager.

    During local development, credentials are read from gmail_token.json.
    If no valid local token exists, an interactive OAuth flow is started.
    """

    token_json = os.getenv(TOKEN_ENV_VAR)
    using_cloud_token = bool(token_json)

    if using_cloud_token:
        token_info = json.loads(token_json)

        creds = Credentials.from_authorized_user_info(
            token_info,
            GMAIL_SCOPES,
        )

    elif os.path.exists(LOCAL_GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(
            LOCAL_GMAIL_TOKEN_PATH,
            GMAIL_SCOPES,
        )

    else:
        creds = None

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if using_cloud_token:
            raise RuntimeError(
                "The Gmail OAuth credentials supplied through "
                "GMAIL_TOKEN_JSON are invalid and cannot be refreshed."
            )

        if not os.path.exists(LOCAL_CLIENT_SECRET_PATH):
            raise FileNotFoundError(
                "client_secret.json was not found. It is required "
                "for the initial local Gmail OAuth login."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            LOCAL_CLIENT_SECRET_PATH,
            GMAIL_SCOPES,
        )

        creds = flow.run_local_server(port=0)

    # Only persist credentials locally.
    # Cloud Run containers are temporary and use Secret Manager instead.
    if not using_cloud_token:
        with open(
            LOCAL_GMAIL_TOKEN_PATH,
            "w",
            encoding="utf-8",
        ) as token_file:
            token_file.write(creds.to_json())

    return creds