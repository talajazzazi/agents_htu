"""
user input = {{user_query}}
Extract the social media platform(s) from the user prompt.
If no platform is specified, use 'Facebook' as default platform.

Determine the content type (text_with_image, image_only, or text_only) based on the user prompt and platform:
- If the platform is not Instagram and the user explicitly requests a text-only blog (without an image), assign 'text_only' to content_type.
- Otherwise, assign 'text_only' as the default content type.

The JSON object output must be  in the following format(please don't write json in the response):
{
    "social_media_platform": "",  # Ensure this field is populated
    "content_type": "",  # Ensure this field is populated
}
"""