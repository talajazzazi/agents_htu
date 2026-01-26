import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.flows.content_generation.flow import ContentGenerationFlow


def main():
    flow = ContentGenerationFlow()
    result = flow.kickoff(
        user_query="Create a professional LinkedIn text and image about AI in healthcare"
    )
    
    print("\n" + "=" * 60)
    print("📝 GENERATED POSTS")
    print("=" * 60)
    
    if result:
        for i, post in enumerate(result, 1):
            print(f"\n--- Post {i} ---")
            text = post.get("text")
            image = post.get("image")

            if text:
                print(f"Text: {text}")
            if image:
                print(f"Image URL: {image}")

            if not text and not image:
                print("No content")
            print()
    else:
        print("No posts generated.")
    
    print("=" * 60)
    wa_out = getattr(flow.state, "whatsapp_send_output", None)
    if wa_out is not None:
        print("\n" + "=" * 60)
        print("📱 WHATSAPP SEND")
        print("=" * 60)
        for i, msg in enumerate(wa_out, 1):
            print(f"  {i}. {msg}")
        print("=" * 60)

if __name__ == "__main__":
    main()
