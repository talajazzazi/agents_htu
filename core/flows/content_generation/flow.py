import asyncio
from itertools import zip_longest
from crewai.flow import Flow, listen, start, router, or_
from django.conf import settings
from core.crews import TextGenerationCrew, ImageGeneratorCrew
from core.utils import render_markdown
from core.tools.whatsapp_twilio import send_whatsapp_messages
from .schema import ContentGenerationState
from core.tools import basic_llm
import json
import logging

logger = logging.getLogger(__name__)


class ContentGenerationFlow(Flow[ContentGenerationState]):

    @start()
    def get_social_media_content_type_tone(self):
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts social media platform, content type, and tone from user input.",
                },
                {
                    "role": "user",
                    "content": render_markdown(
                        template_name="social_media_content_type.md",
                        context={"user_query": self.state.user_query},
                        template_dir="../core/prompts",
                    ),
                },
            ]
            response = basic_llm.call(messages=messages)
            if isinstance(response, dict):
                self.state.planner_output = response
            else:
                self.state.planner_output = json.loads(response)

            return self.state.planner_output

        except Exception as e:
            logger.error(f"Error occurred: {e}")
            return {"error": str(e)}

    @router(get_social_media_content_type_tone)
    def routing(self):
        try:
            content_type = self.state.planner_output["content_type"]

            if content_type == "text_only":
                return "text_only"
            if content_type == "image_only":
                return "image_only"
            if content_type == "text_with_image":
                return "text_with_image"
        except Exception as e:
            logger.error(f"Error in routing: {e}")

    @listen("text_only")
    async def writing_post(self):

        result = await (
            TextGenerationCrew()
            .crew()
            .kickoff_async(
                inputs={
                    "user_query": self.state.user_query
                }
            )
        )

        try:
            result_str = result.raw
            result_json = json.loads(result_str)
            self.state.text_generation_output = result_json
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            self.state.text_generation_output = {"error": "Invalid JSON returned"}

    @listen("image_only")
    async def image_generator(self):

        result = await (
            ImageGeneratorCrew()
            .crew()
            .kickoff_async(
                inputs={
                    "user_query": self.state.user_query
                }
            )
        )

        try:
            result_str = result.raw
            result_json = json.loads(result_str)
            self.state.image_generation_output = result_json
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            self.state.image_generation_output = {"error": "Invalid JSON returned"}

    @listen("text_with_image")
    async def generate_both_text_and_image(self):

        text_task = asyncio.create_task(self.writing_post())
        image_task = asyncio.create_task(self.image_generator())

        await asyncio.gather(text_task, image_task)

    @listen(or_(generate_both_text_and_image, image_generator, writing_post))
    def final_result(self):
        try:
            final_output = {}

            if self.state.image_generation_output:
                final_output["image_generation_results"] = (
                    self.state.image_generation_output
                )

            if self.state.text_generation_output:
                final_output["text_generation_results"] = (
                    self.state.text_generation_output
                )

            reshaped = []
            images = final_output.get("image_generation_results", {}).get("images", [])
            texts = final_output.get("text_generation_results", {}).get("blogs", [])

            for img, txt in zip_longest(images, texts, fillvalue={}):
                reshaped.append(
                    {
                        "text": txt.get("content_of_blog") if txt else None,
                        "image": img.get("image_url") if img else None,
                    }
                )

            final_output["combined_results"] = reshaped

            self.state.final_output = final_output
            return final_output["combined_results"]

        except Exception as e:
            logger.error(f"Error: {e}")

    @listen(or_(writing_post, image_generator, generate_both_text_and_image))
    def whatsapp_send(self):
        """Send combined results via WhatsApp (Twilio) after any content generation."""
        try:
            to = settings.TWILIO_WHATSAPP_TO
            if not to:
                logger.info("WhatsApp send skipped: TWILIO_WHATSAPP_TO not set in settings/.env.")
                self.state.whatsapp_send_output = []
                return

            images = (self.state.image_generation_output or {}).get("images", [])
            texts = (self.state.text_generation_output or {}).get("blogs", [])

            messages = []
            for img, txt in zip_longest(images, texts, fillvalue={}):
                text = (txt or {}).get("content_of_blog", "") or ""
                image_url = (img or {}).get("image_url")
                if isinstance(text, str) and text.strip().lower().startswith("error"):
                    text = ""
                if isinstance(image_url, str) and image_url.strip().lower().startswith("error"):
                    image_url = None
                if not text and not image_url:
                    continue
                messages.append({"text": text or "", "image": image_url})

            if not messages:
                logger.info("WhatsApp send skipped: no valid text or image content.")
                self.state.whatsapp_send_output = []
                return

            sids = send_whatsapp_messages(to, messages)
            self.state.whatsapp_send_output = [f"Sent successfully (SID: {s})" for s in sids]
            logger.info("WhatsApp send completed: %s", self.state.whatsapp_send_output)
        except Exception as e:
            logger.exception("WhatsApp send failed: %s", e)
            self.state.whatsapp_send_output = [f"Error: {str(e)}"]

    def kickoff(
        self,
        user_query: str = None
    ):
        self.state.user_query = user_query
        super().kickoff()
        return self.state.final_output.get("combined_results", [])