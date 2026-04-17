# NovaMind AI Marketing Pipeline

An end-to-end AI-powered marketing automation pipeline that takes a blog topic as input and generates a complete mini campaign — including a blog post, persona-segmented newsletters, HubSpot CRM integration, simulated email sending, and AI-driven performance analysis.

---

## Overview

This project connects content generation, personalization, CRM logging, and analytics into one automated workflow. Instead of a set of isolated scripts, everything runs as a sequential pipeline from a single entry point.

```
User enters topic → Blog post → Newsletters → HubSpot sync → Send simulation → Performance analysis → AI report
```

---

## Project Structure

```
novamind-pipeline/
│
├── main.py                    # Entry point — runs the full pipeline
├── content_generator.py       # Blog post + newsletter generation via Anthropic API
├── hubspot_integration.py     # CRM contact sync and campaign note logging
├── performance_analyzer.py    # Engagement metric simulation + AI analysis
│
├── data/
│   ├── campaign_registry.json # Master log of all campaigns
│   ├── send_log.json          # Simulated send records per persona
│   └── performance_history.json # Historical engagement metrics
│
└── reports/
    └── [campaign_id]_report.json  # Final AI-generated report per run
```

---

## How It Works

### Step 1 — Start the Pipeline (`main.py`)
Run the script and enter a blog topic when prompted. The topic drives the rest of the workflow. An empty input exits with an error. Otherwise, the three major stages run in sequence: content generation, HubSpot integration, and performance analysis.

### Step 2 — Generate the Blog Post (`content_generator.py`)
Uses the Anthropic API to generate a blog post positioning NovaMind as a tool for small creative agencies dealing with fragmented workflows (Slack, Notion, Zapier, Google Drive, Asana, ClickUp, Figma, Canva, ChatGPT). The prompt is written to produce opinionated, specific copy rather than generic output.

The raw response is parsed into three parts using a `parse_blog()` function:
- `title`
- `outline`
- `draft body`

### Step 3 — Generate Persona-Specific Newsletters
Three newsletter versions are generated, each tailored to a defined audience persona:

| Persona | Tone |
|---|---|
| Burnt-Out Art Director | Dry humor, creative frustration |
| Scrappy Founder | ROI-focused, direct |
| Accidental Ops Person | Practical, process-oriented |

Before generating, the system checks `performance_history.json` for the best and worst-performing personas from the previous campaign and feeds that context into the prompt. Each newsletter is parsed into `subject line`, `preview text`, and `body`.

### Step 4 — Save the Campaign
All content is packaged into a campaign object with:
- Campaign ID
- Topic + timestamp
- Blog content
- All three newsletter variants

Saved as a timestamped JSON file. A `campaign_registry.json` acts as a master log, storing a compact summary of every run instead of overwriting previous work.

### Step 5 — HubSpot Integration (`hubspot_integration.py`)
Three mock contacts matching the personas are created or updated in HubSpot. Each contact includes email, name, company, job title, and persona label.

A campaign note is then logged on each contact containing:
- Campaign ID
- Blog title
- Send date
- Persona segment
- Associated subject line

### Step 6 — Simulate Email Sending
Since this is a demo pipeline, newsletter distribution is simulated via `log_send_jobs()`. One send entry is written to `send_log.json` per newsletter version, storing campaign ID, persona ID, persona name, subject line, send time, and delivery mode.

### Step 7 — Simulate Engagement Metrics (`performance_analyzer.py`)
Realistic (but fake) engagement metrics are generated using persona-specific baseline ranges rather than fully random numbers:

| Persona | Behavior |
|---|---|
| Scrappy Founder | Lower open rate, higher click rate |
| Accidental Ops Person | Higher open rate |
| Burnt-Out Art Director | Moderate across the board |

Metrics tracked: `open_rate`, `click_rate`, `click_to_open_rate`, `unsubscribe_rate`. Results are appended to `performance_history.json`.

### Step 8 — Log Performance Back to HubSpot
A performance note is pushed to each persona's HubSpot contact record, containing all engagement metrics alongside the blog title and subject line. This closes the loop between content generation and analytics within the CRM.

### Step 9 — AI Performance Summary
Current metrics plus historical context are sent back to Claude with a prompt asking:
- Which persona performed best?
- Which metric matters most?
- What should change next time?
- What subject line should be tested for the lowest-performing segment?

The final output is saved as a JSON report with the campaign ID, topic, raw metrics, and AI analysis.

---

## Setup

### Requirements
```bash
pip install anthropic requests python-dotenv
```

### Environment Variables
Create a `.env` file in the root directory:
```
ANTHROPIC_API_KEY=your_key_here
HUBSPOT_API_KEY=your_key_here
```

### Run
```bash
python main.py
```

---

## Example Output

```
Enter a blog topic: AI in creative automation

[1/3] Generating blog post...
[2/3] Syncing to HubSpot...
[3/3] Running performance analysis...

Campaign saved: campaigns/campaign_20260414_183012.json
Report saved: reports/campaign_20260414_183012_report.json
```

---

## Notes
- HubSpot contacts are mock/simulated for demo purposes
- Engagement metrics are randomly sampled within persona-specific ranges
- The pipeline is designed to be run repeatedly — each run appends to history files rather than overwriting them
- A basic HubSpot connectivity test is included in `hubspot_integration.py`
