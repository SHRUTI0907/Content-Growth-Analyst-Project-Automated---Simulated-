import anthropic
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

#using personas of people that can possibly simulate real life people -> People who can actually use Novamind
PERSONAS = [
    {
        "id": "burnt_out_art_director",
        "name": "The Burnt-Out Art Director",
        "description": (
            "Mid-level creative at a small agency (4-12 people). "
            "Genuinely talented but spends 40% of their week in revision loops, "
            "hunting down feedback in Slack, and reformatting the same deck for the fifth time. "
            "They didn't go to art school for this."
        ),
        "tone": (
            "Talk to them like a peer who gets it. Skip the cheerleading. "
            "Be specific about time saved and creative headspace recovered. "
            "A little dry humor is fine. They will appreciate it."
        )
    },
    {
        "id": "scrappy_founder",
        "name": "The Scrappy Founder",
        "description": (
            "Started the agency 2-4 years ago, probably still does sales, "
            "ops, and occasional design themselves. Revenue is real but margins are thin. "
            "Every tool they've tried has added complexity instead of removing it. "
            "They're skeptical but desperate."
        ),
        "tone": (
            "Be direct and honest. Lead with what it costs (time + money) to NOT automate. "
            "They care about ROI but will roll their eyes at buzzwords. "
            "Talk like someone who has run a small business, not someone who has studied one."
        )
    },
    {
        "id": "accidental_ops_person",
        "name": "The Accidental Ops Person",
        "description": (
            "Joined as a project manager or account coordinator, "
            "gradually became the person who 'handles the tools' because nobody else would. "
            "Not an engineer. Learns by doing. Keeps the agency from falling apart "
            "and gets very little credit for it."
        ),
        "tone": (
            "Practical and process-oriented. Show them exactly what changes in their day. "
            "No jargon. Acknowledge that they're already holding a lot together -- "
            "this should make their life easier, not give them another system to babysit."
        )
    }
]
def load_performance_context():
    """
    Reads past campaign performance and creates a short prompt context
    so future content generation can improve based on past results.
    """
    history_file = "performance_history.json"

    if not os.path.exists(history_file):
        return "No prior campaign history available."

    try:
        with open(history_file, "r") as f:
            history = json.load(f)
    except Exception:
        return "No readable campaign history available."

    if not history:
        return "No prior campaign history available."

    latest = history[-1]
    engagement = latest.get("engagement", [])

    if not engagement:
        return "No prior engagement data available."

    best = max(engagement, key=lambda x: x.get("click_to_open_rate", 0))
    worst = min(engagement, key=lambda x: x.get("click_to_open_rate", 0))

    return f"""
Previous campaign topic: {latest.get('topic', 'Unknown')}
Best-performing persona: {best.get('persona_name')} with CTOR {best.get('click_to_open_rate', 0)*100:.1f}%
Best-performing subject line: {best.get('subject', '')}

Lowest-performing persona: {worst.get('persona_name')} with CTOR {worst.get('click_to_open_rate', 0)*100:.1f}%
Lowest-performing subject line: {worst.get('subject', '')}

Use this to improve the next round:
- Keep what worked for the best-performing persona
- Improve specificity and relevance for the weakest-performing persona
- Avoid repeating the exact same framing across every campaign
""".strip()

def generate_blog_post(topic):
    print(f"\nGenerating blog post on: '{topic}'")
    print("Calling Claude -- this takes about 20 seconds...")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": f"""You are writing for NovaMind's blog. NovaMind is an early-stage startup
that helps small creative agencies stop duct-taping their workflows together.
Think Notion + Zapier + an AI layer, built specifically for agencies under 20 people.

The blog is read by people who are good at their jobs and tired of bad software.
Write like a smart person, not a content marketer.

Topic: "{topic}"

Rules:
- No words like "game-changing", "revolutionize", "unlock", "leverage", or "cutting-edge"
- No listicles with fake urgency
- No emdashes. Use a period or a comma instead.
- Be specific. Vague claims kill credibility.
- Opinions are fine. Hedging everything is not.
- The tone is: knowledgeable friend who works in the industry
- Name specific tools by name: Slack, Notion, Zapier, Google Drive, Asana, ClickUp, Figma, Canva, ChatGPT. Use them as examples, not abstract "tools."
- Make at least one claim that sounds slightly risky. Call out a category, a vendor type, or an approach directly. Example: "Most 'AI for agencies' tools are just ChatGPT with a nicer interface and a billing page."
- Add at least one specific, painful detail. The kind only someone who has lived it would write. Example: "the final doc is called FINAL_v3_ACTUAL_FINAL.docx somewhere in a shared Drive folder nobody maintains." Or: "Zapier throws a 429 error at 2am and nobody finds out until the client asks."
- Use sentence fragments when they land right. Not every sentence needs a verb.
- Vary paragraph length. Some short. Some not. Interrupt yourself once.
- Humans do not write in perfectly even paragraphs with clean transitions. Do not do that.

Format your response like this (use these exact headers):

TITLE: [title here]

OUTLINE:
- [point 1]
- [point 2]
- [point 3]
- [point 4]
- [point 5]

DRAFT:
[400-600 words. Real sentences. No bullet-point padding.]
"""
            }
        ]
    )

    return message.content[0].text


def generate_newsletter(topic, blog_draft, persona, performance_context):
    print(f"  Writing newsletter for: {persona['name']}")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        messages=[
            {
                "role": "user",
                "content": f"""You're writing a newsletter email for NovaMind.
NovaMind helps small creative agencies automate the parts of their workflow that shouldn't require a human.

This newsletter promotes a blog post about: "{topic}"

Here's a piece of the blog draft to pull from:
---
{blog_draft[:600]}
---

Past campaign performance context:
{performance_context}

Write a short email (150-200 words) for this specific reader:

Who they are: {persona['description']}
How to talk to them: {persona['tone']}

Rules:
- Do not start with "Hey [Name]" or any generic greeting
- Do not use the phrase "we're excited to share"
- No fake urgency ("don't miss out", "limited time")
- No emdashes. Use a period or comma instead.
- Sound like a specific person wrote this on a Tuesday morning, not a drip campaign
- Name specific tools by name when relevant: Slack, Notion, Zapier, Google Drive, Asana, ClickUp, ChatGPT
- One or two sentence fragments are fine. Skip the perfect transitions.
- End with a short, natural closing line. Not a call to action. Just a sentence that feels like a human ending an email.

Format:
SUBJECT: [subject line, make it specific, not clever for the sake of it]

PREVIEW: [one sentence that makes them want to open it]

BODY:
[the email]
"""
            }
        ]
    )

    return message.content[0].text


def parse_blog(raw_text):
    lines = raw_text.strip().split('\n')
    title = ""
    outline = []
    draft_lines = []
    current_section = None

    for line in lines:
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.strip() == "OUTLINE:":
            current_section = "outline"
        elif line.strip() == "DRAFT:":
            current_section = "draft"
        elif current_section == "outline" and line.strip().startswith("-"):
            outline.append(line.strip()[2:].strip())
        elif current_section == "draft":
            draft_lines.append(line)

    return title, outline, "\n".join(draft_lines).strip()


def parse_newsletter(raw_text):
    subject = ""
    preview = ""
    body_lines = []
    current_section = None

    for line in raw_text.strip().split('\n'):
        if line.startswith("SUBJECT:"):
            subject = line.replace("SUBJECT:", "").strip()
        elif line.startswith("PREVIEW:"):
            preview = line.replace("PREVIEW:", "").strip()
        elif line.strip() == "BODY:":
            current_section = "body"
        elif current_section == "body":
            body_lines.append(line)

    return subject, preview, "\n".join(body_lines).strip()
def update_campaign_registry(campaign, filename):
    """
    Keeps a master record of all campaigns.
    Makes the system feel like a real production pipeline.
    """

    registry_file = "campaign_registry.json"

    try:
        with open(registry_file, "r") as f:
            registry = json.load(f)
    except:
        registry = []

    record = {
        "campaign_id": campaign["campaign_id"],
        "topic": campaign["topic"],
        "blog_title": campaign["blog"]["title"],
        "created_at": campaign["created_at"],
        "campaign_file": filename,
        "send_status": "completed",
        "analytics_status": "simulated"
    }

    registry.append(record)

    with open(registry_file, "w") as f:
        json.dump(registry, f, indent=2)

    print(f"\nCampaign registry updated: {registry_file}")

def run_pipeline(topic):
    print("\n--- NovaMind Content Pipeline ---")
    print(f"Topic: {topic}")
    print(f"Started at: {datetime.now().strftime('%I:%M %p')}")
    print("-" * 35)

    # Generate the blog
    raw_blog = generate_blog_post(topic)
    title, outline, draft = parse_blog(raw_blog)

    word_count = len(draft.split())
    print(f"\nBlog done.")
    print(f"  Title: {title}")
    print(f"  Outline points: {len(outline)}")
    print(f"  Draft word count: {word_count}")

    if word_count < 350:
        print("  Note: draft came in short -- you may want to expand it manually.")

    # Load past performance insights
    performance_context = load_performance_context()
    print("\nLoaded past campaign insights.")
    print(performance_context)

    # Generate newsletters
    print("\nGenerating newsletter versions...")
    newsletters = []
    for persona in PERSONAS:
        raw = generate_newsletter(topic, draft, persona, performance_context)
        subject, preview, body = parse_newsletter(raw)
        newsletters.append({
            "persona_id": persona["id"],
            "persona_name": persona["name"],
            "subject": subject,
            "preview": preview,
            "body": body
        })

    print(f"\nAll three newsletter versions done.")

    # Build campaign object
    campaign = {
        "campaign_id": f"nm_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "topic": topic,
        "created_at": datetime.now().isoformat(),
        "status": "generated",
        "blog": {
            "title": title,
            "outline": outline,
            "draft": draft
        },
        "newsletters": newsletters
    }

    # Saving to file
    filename = f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(campaign, f, indent=2)

    update_campaign_registry(campaign, filename)

    print(f"\nSaved to: {filename}")
    print("\n--- Done ---")
    print(f"\nBlog title: {campaign['blog']['title']}")
    print("\nNewsletter subject lines:")
    for n in campaign['newsletters']:
        print(f"  [{n['persona_name']}]  {n['subject']}")

    return campaign, filename


if __name__ == "__main__":
    topic = input("\nWhat's the blog topic? ")
    campaign, filename = run_pipeline(topic)