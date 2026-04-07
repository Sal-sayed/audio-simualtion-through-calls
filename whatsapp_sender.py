"""
WhatsApp Web Automation Sender
──────────────────────────────
Uses pyautogui + webbrowser to open WhatsApp Web links.
Run AFTER uploading contacts and starting the Flask server.

Usage:
    python whatsapp_sender.py --base-url https://yourapp.com --batch 50 --delay 8
"""

import csv
import time
import webbrowser
import argparse
import urllib.parse
import sys

DEFAULT_BASE_URL = "http://localhost:5000"
DEFAULT_BATCH    = 50
DEFAULT_DELAY    = 8   # seconds between messages


def load_contacts(csv_path: str) -> list[dict]:
    contacts = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            contacts.append(row)
    return contacts


def build_message(name: str, phone: str, base_url: str) -> str:
    link = f"{base_url}/?user={phone}&name={urllib.parse.quote(name)}"
    msg = (
        f"📞 Incoming Awareness Call\n\n"
        f"Hello {name}! You have an important awareness message.\n\n"
        f"👉 Tap to Answer: {link}\n\n"
        f"🔊 Please turn up your volume."
    )
    return msg


def send_whatsapp(phone: str, message: str):
    """
    Opens WhatsApp Web send link in default browser.
    The phone number must include country code (no + or spaces).
    Example: 919876543210
    """
    encoded = urllib.parse.quote(message)
    url = f"https://wa.me/{phone}?text={encoded}"
    webbrowser.open(url)


def run(csv_path: str, base_url: str, batch_size: int, delay: int,
        start_from: int = 0, dry_run: bool = False):

    contacts = load_contacts(csv_path)
    total    = len(contacts)
    print(f"[+] Loaded {total} contacts from '{csv_path}'")
    print(f"[+] Base URL : {base_url}")
    print(f"[+] Batch    : {batch_size}  |  Delay: {delay}s  |  Start: {start_from}")
    print(f"[+] Dry run  : {dry_run}\n")

    sent = 0
    for i, contact in enumerate(contacts[start_from:], start=start_from + 1):
        name  = contact.get("Name",  contact.get("name",  f"User{i}"))
        phone = contact.get("Phone", contact.get("phone", ""))

        if not phone:
            print(f"  [{i}] SKIP — no phone number for {name}")
            continue

        # Remove non-digit chars
        phone_clean = "".join(c for c in phone if c.isdigit())

        message = build_message(name, phone_clean, base_url)
        link    = f"{base_url}/?user={phone_clean}&name={urllib.parse.quote(name)}"

        if dry_run:
            print(f"  [{i}] DRY RUN → {name} ({phone_clean})")
            print(f"        Link: {link}")
        else:
            print(f"  [{i}] Sending to {name} ({phone_clean})...")
            send_whatsapp(phone_clean, message)
            sent += 1

        # Batch pause
        if sent > 0 and sent % batch_size == 0:
            print(f"\n[~] Batch of {batch_size} sent. Pausing {delay}s...\n")
            time.sleep(delay)
        else:
            time.sleep(1.5)   # small gap between each message

    print(f"\n[✓] Done. Sent: {sent} / {total - start_from}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhatsApp Awareness Campaign Sender")
    parser.add_argument("--csv",       default="contacts.csv",    help="Path to contacts CSV")
    parser.add_argument("--base-url",  default=DEFAULT_BASE_URL,  help="Base URL of deployed app")
    parser.add_argument("--batch",     type=int, default=DEFAULT_BATCH,  help="Messages per batch")
    parser.add_argument("--delay",     type=int, default=DEFAULT_DELAY,  help="Seconds between batches")
    parser.add_argument("--start",     type=int, default=0,              help="Start from row index")
    parser.add_argument("--dry-run",   action="store_true",              help="Preview only, do not open browser")
    args = parser.parse_args()

    run(
        csv_path   = args.csv,
        base_url   = args.base_url,
        batch_size = args.batch,
        delay      = args.delay,
        start_from = args.start,
        dry_run    = args.dry_run,
    )
