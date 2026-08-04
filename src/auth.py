import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
     "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]

TOKEN_ENV_VAR = "YOUTUBE_TOKEN_JSON"
LOCAL_TOKEN_PATH = "token.json"
LOCAL_CLIENT_SECRET_PATH = "client_secret.json"


def authenticate() -> Credentials:
    """
    Authenticate with the YouTube APIs.

    In Cloud Run, credentials are read from the YOUTUBE_TOKEN_JSON
    environment variable, supplied through Secret Manager.

    During local development, credentials are read from token.json.
    If no valid local token exists, an interactive OAuth flow is started.
    """

    token_json = os.getenv(TOKEN_ENV_VAR)
    using_cloud_token = bool(token_json)

    if using_cloud_token:
        token_info = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(
            token_info,
            SCOPES,
        )

    elif os.path.exists(LOCAL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(
            LOCAL_TOKEN_PATH,
            SCOPES,
        )

    else:
        creds = None

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if using_cloud_token:
            raise RuntimeError(
                "The YouTube OAuth credentials supplied through "
                "YOUTUBE_TOKEN_JSON are invalid and cannot be refreshed."
            )

        if not os.path.exists(LOCAL_CLIENT_SECRET_PATH):
            raise FileNotFoundError(
                "client_secret.json was not found. It is required "
                "for the initial local YouTube OAuth login."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            LOCAL_CLIENT_SECRET_PATH,
            SCOPES,
        )

        creds = flow.run_local_server(port=0)

    # Only persist credentials locally.
    # Cloud Run containers are temporary and use Secret Manager instead.
    if not using_cloud_token:
        with open(LOCAL_TOKEN_PATH, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return creds