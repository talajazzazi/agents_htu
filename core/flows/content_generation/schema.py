from pydantic import BaseModel
from typing import Dict, List, Optional

class ContentGenerationState(BaseModel):
   user_query: str = ""
   planner_output: Dict = {}
   text_generation_output: Dict = {}
   image_generation_output: Optional[Dict] = None
   final_output: Dict = {}
   whatsapp_send_output: Optional[List[str]] = None