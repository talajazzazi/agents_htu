from pydantic import BaseModel
from typing import  Dict

class ContentGenerationState(BaseModel):
    user_query: str = ""
    planner_output: Dict = {}
    text_generation_output: Dict = {}
    final_output: Dict = {}