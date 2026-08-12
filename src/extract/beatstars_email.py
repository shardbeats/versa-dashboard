import base64
import re
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build

from src.auth_gmail import authenticate_gmail
from src.transform.beatstars_email import parse_beatstars_sale_email


BEATSTARS_SALES_QUERY = (
    'from:noreply@beatstars.com '
    'subject:"@BeatStars Sale Notification"'
)


def find_html_part(part):
    if part.get("mimeType") == "text/html":
        return part

    for child in part.get("parts", []):
        result = find_html_part(child)

        if result:
            return result

    return None


def decode_html_part(html_part) -> str:
    encoded_html = html_part["body"]["data"]

    return base64.urlsafe_b64decode(
        encoded_html + "=" * (-len(encoded_html) % 4)
    ).decode("utf-8")


def extract_invoice_number(subject: str) -> str | None:
    """
    Extract the BeatStars invoice number from an email subject.

    Example:
    @BeatStars Sale Notification PRO7534763_0575623001785368450_2303563

    Returns:
    PRO7534763_0575623001785368450_2303563
    """

    match = re.search(
        r"@BeatStars Sale Notification\s+(.+)$",
        subject,
    )

    if not match:
        return None

    return match.group(1).strip()


def extract_beatstars_sales(
    max_results: int = 10,
    query: str = BEATSTARS_SALES_QUERY,
) -> list[dict]:
    """
    Fetch recent BeatStars sale notification emails from Gmail
    and return them as structured sale events.
    """

    creds = authenticate_gmail()
    service = build(
        "gmail",
        "v1",
        credentials=creds,
    )

    result = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results,
    ).execute()

    messages = result.get("messages", [])
    sales = []

    for message_ref in messages:
        message = service.users().messages().get(
            userId="me",
            id=message_ref["id"],
            format="full",
        ).execute()

        headers = {
            header["name"]: header["value"]
            for header in message["payload"].get("headers", [])
        }

        html_part = find_html_part(message["payload"])

        if not html_part:
            continue

        html = decode_html_part(html_part)

        parsed = parse_beatstars_sale_email(html)

        subject = headers.get("Subject", "")
        invoice_number = extract_invoice_number(subject)

        date = headers.get("Date")

        if not date:
            continue

        sold_at = parsedate_to_datetime(
            date
        ).isoformat()

        sales.append(
            {
                "message_id": message["id"],
                "invoice_number": invoice_number,
                "sold_at": sold_at,
                **parsed,
            }
        )

    return sales