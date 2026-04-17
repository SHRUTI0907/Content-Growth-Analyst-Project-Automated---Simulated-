import os
import json
import random
import requests
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
HUBSPOT_TOKEN = os.getenv("HUBSPOT_API_KEY")
HUBSPOT_HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

PERFORMANCE_LOG = "performance_history.json"

# Each persona has realistic baseline engagement tendencies.
# These inform the simulated metrics -- not purely random.
PERSONA_BASELINES = {
    "burnt_out_art_director": {
        "open_rate_range": (0.38, 0.58),   # emotionally resonant subject lines, opens well
        "click_rate_range": (0.08, 0.18),   # selective -- clicks if it feels worth it
        "unsubscribe_rate_range": (0.005, 0.02)
    },
    "scrappy_founder": {
        "open_rate_range": (0.28, 0.45),   # busy, skeptical, opens less
        "click_rate_range": (0.12, 0.25),  # but when they do open, they click through
        "unsubscribe_rate_range": (0.01, 0.03)
    },
    "accidental_ops_person": {
        "open_rate_range": (0.42, 0.62),   # checks everything, high open rate
        "click_rate_range": (0.10, 0.20),  # moderate clicks
        "unsubscribe_rate_range": (0.003, 0.015)
    }
}
def fetch_real_engagement(campaign):
    """
    Placeholder for production email analytics.
    In a real deployment, this would fetch campaign performance
    from HubSpot, SendGrid, Mailchimp, or another provider.
    """
    raise NotImplementedError(
        "Real email analytics integration is not enabled in this demo."
    )


def get_campaign_performance(campaign, mode="simulated"):
    """
    Returns campaign engagement data using either:
    - simulated mode for demo/testing
    - real mode for live provider integrations
    """
    if mode == "simulated":
        return simulate_engagement(campaign)
    elif mode == "real":
        return fetch_real_engagement(campaign)
    else:
        raise ValueError(f"Unsupported performance mode: {mode}")

def simulate_engagement(campaign):
    """
    Generate realistic (but fake) engagement metrics for each newsletter.
    In a real system, these would come from HubSpot's email analytics API.
    The ranges are persona-informed -- not just random noise.
    """

    print("\nSimulating engagement data...")
    print("(In production, this would pull from HubSpot's email analytics API)")

    results = []
    for newsletter in campaign["newsletters"]:
        persona_id = newsletter["persona_id"]
        baseline = PERSONA_BASELINES.get(persona_id, {
            "open_rate_range": (0.20, 0.40),
            "click_rate_range": (0.05, 0.15),
            "unsubscribe_rate_range": (0.005, 0.02)
        })

        open_rate = round(random.uniform(*baseline["open_rate_range"]), 3)
        click_rate = round(random.uniform(*baseline["click_rate_range"]), 3)
        unsubscribe_rate = round(random.uniform(*baseline["unsubscribe_rate_range"]), 4)

        # Click-to-open rate -- a more honest signal than raw click rate
        ctor = round(click_rate / open_rate, 3) if open_rate > 0 else 0

        result = {
            "persona_id": persona_id,
            "persona_name": newsletter["persona_name"],
            "subject": newsletter["subject"],
            "open_rate": open_rate,
            "click_rate": click_rate,
            "click_to_open_rate": ctor,
            "unsubscribe_rate": unsubscribe_rate,
            "simulated": True
        }

        results.append(result)
        print(f"  {newsletter['persona_name']}")
        print(f"    Open rate:   {open_rate*100:.1f}%")
        print(f"    Click rate:  {click_rate*100:.1f}%")
        print(f"    CTOR:        {ctor*100:.1f}%")
        print(f"    Unsub rate:  {unsubscribe_rate*100:.2f}%")

    return results


def save_to_history(campaign, engagement_results):
    """
    Append this campaign's performance to a running history file.
    This lets us compare across campaigns over time.
    """

    record = {
        "campaign_id": campaign["campaign_id"],
        "topic": campaign["topic"],
        "blog_title": campaign["blog"]["title"],
        "date": datetime.now().isoformat(),
        "engagement": engagement_results
    }

    # Load existing history if it exists
    history = []
    if os.path.exists(PERFORMANCE_LOG):
        with open(PERFORMANCE_LOG) as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    history.append(record)

    with open(PERFORMANCE_LOG, "w") as f:
        json.dump(history, f, indent=2)

    print(f"\nPerformance saved to: {PERFORMANCE_LOG}")
    print(f"Total campaigns in history: {len(history)}")
    return history


def log_performance_to_hubspot(campaign, engagement_results):
    """
    Write a performance summary note back to each contact in HubSpot.
    Closes the loop -- the CRM now knows how each segment performed.
    """

    print("\nLogging performance back to HubSpot...")

    # Pull contacts we created earlier
    response = requests.get(
        "https://api.hubapi.com/crm/v3/objects/contacts?limit=10",
        headers=HUBSPOT_HEADERS
    )

    if response.status_code != 200:
        print(f"Could not fetch contacts: {response.status_code}")
        return

    contacts = response.json().get("results", [])

    # Match contacts by email domain to our mock contacts
    our_emails = {
        "burnt_out_art_director": "jordan.kim@studioloupe.com",
        "scrappy_founder": "priya.nair@fieldworkagency.co",
        "accidental_ops_person": "dan.okafor@monday-creative.io"
    }

    for result in engagement_results:
        persona_id = result["persona_id"]
        target_email = our_emails.get(persona_id)

        # Find matching contact
        matched = next(
            (c for c in contacts if c["properties"].get("email") == target_email),
            None
        )

        if not matched:
            print(f"  Contact not found for {persona_id}, skipping")
            continue

        contact_id = matched["id"]
        note_body = (
            f"Performance Report -- {campaign['campaign_id']}\n"
            f"--------------------------------------\n"
            f"Blog: {campaign['blog']['title']}\n"
            f"Persona: {result['persona_name']}\n"
            f"Subject line: {result['subject']}\n\n"
            f"Open rate:          {result['open_rate']*100:.1f}%\n"
            f"Click rate:         {result['click_rate']*100:.1f}%\n"
            f"Click-to-open:      {result['click_to_open_rate']*100:.1f}%\n"
            f"Unsubscribe rate:   {result['unsubscribe_rate']*100:.2f}%\n"
            f"Data type:          simulated"
        )

        note_payload = {
            "properties": {
                "hs_note_body": note_body,
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

        note_resp = requests.post(
            "https://api.hubapi.com/crm/v3/objects/notes",
            headers=HUBSPOT_HEADERS,
            json=note_payload
        )

        if note_resp.status_code == 201:
            print(f"  Performance note logged for: {result['persona_name']}")
        else:
            print(f"  Failed for {result['persona_name']}: {note_resp.status_code}")


def generate_ai_analysis(campaign, engagement_results, history):
    """
    Feed the engagement data to Claude and get a real analysis back --
    what worked, what didn't, and what to do differently next time.
    """

    print("\nAsking Claude to analyze performance...")

    # Build a clean summary of this campaign's numbers
    metrics_summary = ""
    for r in engagement_results:
        metrics_summary += (
            f"\n{r['persona_name']}:\n"
            f"  Subject: {r['subject']}\n"
            f"  Open rate: {r['open_rate']*100:.1f}%\n"
            f"  Click rate: {r['click_rate']*100:.1f}%\n"
            f"  Click-to-open: {r['click_to_open_rate']*100:.1f}%\n"
            f"  Unsubscribe rate: {r['unsubscribe_rate']*100:.2f}%\n"
        )

    # Include historical context if we have it
    history_note = ""
    if len(history) > 1:
        history_note = f"\nThis is campaign #{len(history)} in our history. Previous topics: "
        history_note += ", ".join([h["topic"] for h in history[:-1]])

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        messages=[
            {
                "role": "user",
                "content": f"""You're analyzing newsletter performance for NovaMind, an AI startup 
targeting small creative agencies.

Campaign topic: "{campaign['topic']}"
Blog title: "{campaign['blog']['title']}"
{history_note}

Engagement data by persona:
{metrics_summary}

Write a short performance analysis (150-200 words). Be direct and specific.
- Which persona performed best and why (based on their profile)
- Which metric is most worth paying attention to and why
- One concrete recommendation for the next campaign's content or targeting
- One subject line idea for the next email to the lowest-performing persona

Do not use bullet points. Write in plain paragraphs like an analyst would in a Slack message to their team.
Do not start with "Overall" or "In summary".
"""
            }
        ]
    )

    analysis = message.content[0].text
    print("\n--- AI Performance Analysis ---")
    print(analysis)
    return analysis


def run_performance_pipeline(campaign):
    print("\n--- Performance Analysis Pipeline ---")
    print("Performance mode: simulated")

    # ✅ Correct call
    engagement_results = get_campaign_performance(campaign, mode="simulated")

    history = save_to_history(campaign, engagement_results)

    log_performance_to_hubspot(campaign, engagement_results)

    analysis = generate_ai_analysis(campaign, engagement_results, history)

    report = {
        "campaign_id": campaign["campaign_id"],
        "blog_title": campaign["blog"]["title"],
        "topic": campaign["topic"],
        "generated_at": datetime.now().isoformat(),
        "engagement": engagement_results,
        "ai_analysis": analysis
    }

    report_file = f"report_{campaign['campaign_id']}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nFull report saved to: {report_file}")
    print("\n--- Done ---")

    return report

    return report

if __name__ == "__main__":
    import glob

    campaign_files = sorted(glob.glob("campaign_*.json"))
    if not campaign_files:
        print("No campaign files found. Run content_generator.py first.")
    else:
        latest = campaign_files[-1]
        print(f"Loading: {latest}")
        with open(latest) as f:
            campaign = json.load(f)
        run_performance_pipeline(campaign)