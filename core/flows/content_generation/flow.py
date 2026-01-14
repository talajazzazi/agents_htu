from crewai.flow import Flow, listen, start, router, or_
from core.crews import TextGenerationCrew
from core.utils import render_markdown
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

    @listen(or_(writing_post))
    def final_result(self):
        try:
            final_output = {}

            if self.state.text_generation_output:
                final_output["text_generation_results"] = (
                    self.state.text_generation_output
                )

            reshaped = []
            texts = final_output.get("text_generation_results", {}).get("blogs", [])

            for txt in texts:
                reshaped.append(
                    {
                        "text": txt.get("content_of_blog") if txt else None,
                    }
                )

            final_output["combined_results"] = reshaped

            self.state.final_output = final_output
            return final_output["combined_results"]

        except Exception as e:
            logger.error(f"Error: {e}")

    def kickoff(
        self,
        user_query: str = None
    ):
        self.state.user_query = user_query
        return super().kickoff()