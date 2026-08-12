import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

LOCAL_CLIENT_SECRET_PATH = "client_secret.json"
LOCAL_GMAIL_TOKEN_PATH = "gmail_token.json"


def authenticate_gmail() -> Credentials:
    """
    Authenticate with the Gmail API.

    Gmail uses its own OAuth token because the Gmail account is separate
    from the Google account used by the YouTube pipeline.
    """

    creds = None

    if os.path.exists(LOCAL_GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(
            LOCAL_GMAIL_TOKEN_PATH,
            GMAIL_SCOPES,
        )

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not os.path.exists(LOCAL_CLIENT_SECRET_PATH):
            raise FileNotFoundError(
                "client_secret.json was not found. It is required "
                "for the initial Gmail OAuth login."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            LOCAL_CLIENT_SECRET_PATH,
            GMAIL_SCOPES,
        )

        creds = flow.run_local_server(port=0)

    with open(LOCAL_GMAIL_TOKEN_PATH, "w", encoding="utf-8") as token_file:
        token_file.write(creds.to_json())

    return creds