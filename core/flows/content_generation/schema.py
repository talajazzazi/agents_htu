from pydantic import BaseModel
from typing import  Dict, Optional

class ContentGenerationState(BaseModel):
   user_query: str = ""
   planner_output: Dict = {}
   text_generation_output: Dict = {}
   image_generation_output: Optional[Dict] = None
   final_output: Dict = {}