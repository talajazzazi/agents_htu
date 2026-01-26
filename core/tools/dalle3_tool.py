from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from openai import OpenAI
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Dalle3ImageGeneratorInput(BaseModel):
    """Input schema for DALL-E 3 Image Generator tool."""
    prompt: str = Field(..., description="A detailed text description of the image to generate. Must be in English and under 1000 characters.")
    size: str = Field(default="1024x1024", description="Image size. Options: '1024x1024', '1792x1024', '1024x1792'. Default: '1024x1024'")
    quality: str = Field(default="standard", description="Image quality. Options: 'standard', 'hd'. Default: 'standard'")


class Dalle3ImageGenerator(BaseTool):
    """Tool for generating images using DALL-E 3."""
    
    name: str = "DALL-E 3 Image Generator"
    description: str = (
        "Generates an image using DALL-E 3 based on the provided prompt. "
        "Use safe, neutral, professional prompts (e.g. abstract illustrations, clean layouts). "
        "Returns the image URL, or an error. If you see CONTENT_POLICY_VIOLATION, retry with a simpler, more generic prompt."
    )
    args_schema: Type[BaseModel] = Dalle3ImageGeneratorInput

    def _run(self, prompt: str, size: str = "1024x1024", quality: str = "standard") -> str:
        """
        Generate an image using DALL-E 3.
        
        Args:
            prompt: A detailed text description of the image to generate.
            size: Image size. Options: "1024x1024", "1792x1024", "1024x1792". Default: "1024x1024"
            quality: Image quality. Options: "standard", "hd". Default: "standard"
        
        Returns:
            str: The URL of the generated image, or an error message if generation fails.
        """
        try:
            openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured in Django settings")

            client = OpenAI(api_key=openai_api_key)

            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )

            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                logger.info(f"Successfully generated image with DALL-E 3: {image_url}")
                return image_url
            else:
                error_msg = "No image data returned from OpenAI API"
                logger.error(error_msg)
                return f"Error: {error_msg}"
                
        except Exception as e:
            err_str = str(e)
            logger.error("DALL-E 3 error: %s", err_str)
            if "content_policy_violation" in err_str.lower() or "safety system" in err_str.lower():
                return (
                    "Error: CONTENT_POLICY_VIOLATION - The prompt was rejected by the safety system. "
                    "Retry with a simpler, more neutral, professional prompt (e.g. abstract illustration, "
                    "generic scenery, or a toned-down description avoiding any sensitive wording)."
                )
            return f"Error: {err_str}"


# Create an instance of the tool
dalle3_image_generator = Dalle3ImageGenerator()
