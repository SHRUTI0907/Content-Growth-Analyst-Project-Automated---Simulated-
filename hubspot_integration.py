import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

HUBSPOT_TOKEN = os.getenv("HUBSPOT_API_KEY")

BASE_URL = "https://api.hubapi.com"

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

# Mock contacts, Fake persona (making it look realistic though)
MOCK_CONTACTS = [
    {
        "email": "jordan.kim@studioloupe.com",
        "firstname": "Jordan",
        "lastname": "Kim",
        "persona": "burnt_out_art_director",
        "persona_label": "Burnt-Out Art Director",
        "company": "Studio Loupe",
        "jobtitle": "Senior Art Director"
    },
    {
        "email": "priya.nair@fieldworkagency.co",
        "firstname": "Priya",
        "lastname": "Nair",
        "persona": "scrappy_founder",
        "persona_label": "Scrappy Founder",
        "company": "Fieldwork Agency",
        "jobtitle": "Founder & Creative Director"
    },
    {
        "email": "dan.okafor@monday-creative.io",
        "firstname": "Dan",
        "lastname": "Okafor",
        "persona": "accidental_ops_person",
        "persona_label": "Accidental Ops Person",
        "company": "Monday Creative",
        "jobtitle": "Project Manager"
    }
]


def create_or_update_contact(contact):
    """
    Create a contact in HubSpot, or update them if they already exist.
    We store the persona in a field called 'jobtitle' since free HubSpot
    accounts don't allow custom properties without extra setup.
    """

    payload = {
    "properties": {
        "email": contact["email"],
        "firstname": contact["firstname"],
        "lastname": contact["lastname"],
        "company": contact["company"],
        "jobtitle": contact["jobtitle"],
        "persona_segment": contact["persona"]
    }
}

    # First try to create
    response = requests.post(
        f"{BASE_URL}/crm/v3/objects/contacts",
        headers=HEADERS,
        json=payload
    )

    if response.status_code == 201:
        contact_id = response.json()["id"]
        print(f"  Created: {contact['firstname']} {contact['lastname']} ({contact['persona_label']})")
        return contact_id

    elif response.status_code == 409:
        # If contact exists, update then
        existing = requests.get(
            f"{BASE_URL}/crm/v3/objects/contacts/{contact['email']}?idProperty=email",
            headers=HEADERS
        )
        contact_id = existing.json()["id"]

        requests.patch(
            f"{BASE_URL}/crm/v3/objects/contacts/{contact_id}",
            headers=HEADERS,
            json=payload
        )
        print(f"  Updated: {contact['firstname']} {contact['lastname']} ({contact['persona_label']})")
        return contact_id

    else:
        print(f"  Failed to create {contact['firstname']}: {response.status_code} {response.text}")
        return None


def log_campaign_to_hubspot(campaign, contact_ids):
    """
    Log the campaign as a note on each contact in HubSpot.
    This gives us a paper trail of who got which newsletter.
    """

    blog_title = campaign["blog"]["title"]
    campaign_id = campaign["campaign_id"]
    send_date = datetime.now().strftime("%Y-%m-%d")

    # Summarizing what was sent
    note_body = (
        f"NovaMind Campaign Log\n"
        f"---------------------\n"
        f"Campaign ID: {campaign_id}\n"
        f"Blog title: {blog_title}\n"
        f"Send date: {send_date}\n"
        f"Status: newsletter distributed"
    )

    print(f"\nLogging campaign to HubSpot contacts...")

    for i, contact in enumerate(MOCK_CONTACTS):
        contact_id = contact_ids[i]
        if not contact_id:
            continue

        # Find which newsletter version this persona received
        newsletter = next(
            (n for n in campaign["newsletters"] if n["persona_id"] == contact["persona"]),
            None
        )

        if newsletter:
            full_note = (
                f"{note_body}\n"
                f"Persona segment: {contact['persona_label']}\n"
                f"Newsletter subject: {newsletter['subject']}"
            )
        else:
            full_note = note_body

        # Create the note, associated with the contact
        note_payload = {
            "properties": {
                "hs_note_body": full_note,
                "hs_timestamp": datetime.now().isoformat() + "Z"
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 202
                        }
                    ]
                }
            ]
        }

        note_response = requests.post(
            f"{BASE_URL}/crm/v3/objects/notes",
            headers=HEADERS,
            json=note_payload
        )

        if note_response.status_code == 201:
            print(f"  Logged note for: {contact['firstname']} {contact['lastname']}")
        else:
            print(f"  Note failed for {contact['firstname']}: {note_response.status_code} {note_response.text}")


def run_hubspot_pipeline(campaign):
    """
    Main function -- creates contacts, tags them by persona,
    and logs the campaign against each one.
    """

    print("\n--- HubSpot Integration ---")
    print(f"Campaign: {campaign['campaign_id']}")
    print(f"Setting up {len(MOCK_CONTACTS)} contacts...\n")

    # create and/or update contacts acc to prev ones
    contact_ids = []
    for contact in MOCK_CONTACTS:
        contact_id = create_or_update_contact(contact)
        contact_ids.append(contact_id)

    print(f"\nAll contacts synced to HubSpot.")

    # Log the campaign against each contact
    log_campaign_to_hubspot(campaign, contact_ids)
    log_send_jobs(campaign)
    print("\nHubSpot sync complete.")
    print(f"Check your contacts at: https://app.hubspot.com/contacts/")

    return contact_ids
def log_send_jobs(campaign):
    """
    Simulates sending newsletters to each persona segment.
    Stores structured send logs for tracking.
    """

    print("\nSimulating newsletter distribution...")

    send_log_file = "send_log.json"

    # Load exisintg logs
    try:
        with open(send_log_file, "r") as f:
            send_logs = json.load(f)
    except:
        send_logs = []

    for newsletter in campaign["newsletters"]:
        record = {
            "campaign_id": campaign["campaign_id"],
            "persona_id": newsletter["persona_id"],
            "persona_name": newsletter["persona_name"],
            "subject": newsletter["subject"],
            "send_time": datetime.now().isoformat(),
            "delivery_mode": "simulated_send"
        }

        send_logs.append(record)

        print(f"  Sent to {newsletter['persona_name']}")
        print(f"    Subject: {newsletter['subject']}")

    # Save 
    with open(send_log_file, "w") as f:
        json.dump(send_logs, f, indent=2)

    print(f"\nSend log updated: {send_log_file}")

# Test this file, as a separate entity
if __name__ == "__main__":
    import glob

    # Most recent campaign file

    campaign_files = sorted(glob.glob("campaign_*.json"))
    if not campaign_files:
        print("No campaign files found. Run content_generator.py first.")
    else:
        latest = campaign_files[-1]
        print(f"Loading campaign from: {latest}")
        with open(latest) as f:
            campaign = json.load(f)
        run_hubspot_pipeline(campaign)