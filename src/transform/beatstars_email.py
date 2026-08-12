import re

from bs4 import BeautifulSoup
from bs4.element import NavigableString


ITEM_STYLE_MARKER = "border-bottom: solid 1px #EEEEEE"


def parse_price(value: str) -> float:
    """Convert a BeatStars price such as '$15.00' or '$0' to float."""

    cleaned = value.strip().replace("$", "").replace(",", "")
    return float(cleaned)


def parse_beatstars_sale_email(html: str) -> dict:
    """
    Parse a BeatStars sale notification email into structured data.
    """

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # -------------------------
    # Source
    # -------------------------
    if "from BeatStars Marketplace" in text:
        source = "marketplace"
    elif "from Versa Pro Page Store" in text:
        source = "pro_page"
    else:
        source = "unknown"

    # -------------------------
    # Order total
    # -------------------------
    total_match = re.search(
        r"Total\s+\$\s*([0-9]+(?:\.[0-9]{1,2})?)",
        text,
    )

    if not total_match:
        raise ValueError("Could not find BeatStars order total.")

    total = float(total_match.group(1))

    # -------------------------
    # Items
    # -------------------------
    items = []

    item_blocks = [
        div
        for div in soup.find_all("div")
        if ITEM_STYLE_MARKER in div.get("style", "")
    ]

    for block in item_blocks:
        # BeatStars track artwork identifies an actual sale item.
        # Marketplace and Pro Page use different artwork URL structures,
        # so we only require the image to come from BeatStars.
        artwork = block.find(
            "img",
            src=lambda value: value and "main.v2.beatstars.com" in value,
        )

        if not artwork:
            continue

        item_text = list(block.stripped_strings)

        if len(item_text) < 2:
            continue

        beat_title = item_text[0]
        price_text = item_text[1]

        if not price_text.startswith("$"):
            continue

        # Negotiation deals do not reliably expose the actual
        # beat title or license type in the notification email.
        if beat_title.startswith("NEGOTIATION DEAL WITH"):
            items.append(
                {
                    "beat_title": "Negotiation Deal",
                    "price": parse_price(price_text),
                    "license": None,
                    "sale_type": "negotiation",
                }
            )
            continue

        if len(item_text) < 3:
            continue

        license_type = item_text[2]

        items.append(
            {
                "beat_title": beat_title,
                "price": parse_price(price_text),
                "license": license_type,
                "sale_type": "standard",
            }
        )

    # -------------------------
    # Customer
    # -------------------------
    customer_name = None
    customer_email = None

    customer_label = soup.find(
        string=lambda value: value and value.strip() == "Customer:"
    )

    if customer_label:
        customer_section = customer_label.find_parent("div")

        if customer_section:
            # BeatStars places the customer name as a loose text node
            # after the Customer div / avatar / <br>.
            for element in customer_section.next_elements:
                if isinstance(element, NavigableString):
                    value = element.strip()

                    if not value or value == "Customer:":
                        continue

                    # Stop when we reach the email address.
                    if "@" in value:
                        break

                    customer_name = value
                    break

            # Customer email is contained in the next matching <a>.
            email_link = customer_section.find_next(
                "a",
                string=lambda value: value and "@" in value,
            )

            if email_link:
                customer_email = email_link.get_text(strip=True)

    return {
        "source": source,
        "total": total,
        "items": items,
        "customer": {
            "name": customer_name,
            "email": customer_email,
        },
    }