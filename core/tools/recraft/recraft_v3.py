import base64
import logging
import uuid
from io import BytesIO
from PIL import Image
from crewai.tools import tool
from openai import OpenAI
from core.tools.recraft.config import get_recraft_config
from django.conf import settings

from integrations.s3 import S3Client

logger = logging.getLogger(__name__)

@tool("recraft_v3")
def generat_image(prompt: str) -> str:
    """Generate image and upload it to S3"""

    recraft_config = get_recraft_config()
    client = OpenAI(
        base_url=recraft_config.base_url,
        api_key=recraft_config.recraft_api_key,
    )

    response = client.images.generate(
        prompt=prompt,
        style=recraft_config.style,
        n=recraft_config.number_of_images,
        size=recraft_config.size,
        response_format=recraft_config.response_format,
    )

    image_objects = response.data
    s3 = S3Client()
    s3_urls = []

    for i, img_obj in enumerate(image_objects, start=1):
        try:
            if img_obj.b64_json:
                image_bytes = base64.b64decode(img_obj.b64_json)
                image_data = BytesIO(image_bytes)

                image = Image.open(image_data).convert("RGB")
                png_buffer = BytesIO()
                image.save(png_buffer, format="PNG")
                png_buffer.seek(0)

                key = f"generated-images/image_{i}_{uuid.uuid4().hex}.png"

                s3_url = s3.upload_object(
                    file_obj=png_buffer,
                    bucket_name=settings.S3_BUCKET_NAME,
                    key=key,
                    content_type="image/png"
                )

                if s3_url:
                    s3_urls.append(s3_url)
                else:
                    logger.warning(f"Failed to upload image {i} to S3.")
            else:
                logger.warning(f"No image data found for image {i}")
        except Exception as e:
            logger.exception(f"Error processing image {i}: {e}")

    return "\n".join(s3_urls)
