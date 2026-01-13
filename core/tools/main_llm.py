from django.conf import settings
from crewai import  LLM

basic_llm=LLM(
        model=settings.OPENAI_MODEL,
        temperature=0,
        api_key= settings.OPENAI_API_KEY
    )