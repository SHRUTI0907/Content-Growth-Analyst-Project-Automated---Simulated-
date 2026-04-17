from content_generator import run_pipeline
from hubspot_integration import run_hubspot_pipeline
from performance_analyzer import run_performance_pipeline


def main():
    topic = input("Enter a blog topic: ").strip()

    if not topic:
        print("Error: No topic entered.")
        return

    try:
        campaign, filename = run_pipeline(topic)
        run_hubspot_pipeline(campaign)
        report = run_performance_pipeline(campaign)

        print(f"Campaign ID: {campaign['campaign_id']}")
        print(f"Blog Title: {campaign['blog']['title']}")
        print(f"Saved campaign file: {filename}")

    except Exception as e:
        print(f"\nPipeline failed: {e}")


if __name__ == "__main__":
    main()