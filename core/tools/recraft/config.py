from dataclasses import dataclass
from django.conf import settings

@dataclass
class RecraftConfig:
    base_url: str
    recraft_api_key: str
    style: str
    number_of_images: int
    size: str
    response_format: str

def get_recraft_config() -> RecraftConfig:
    return RecraftConfig(
        base_url=settings.BASE_URI,
        recraft_api_key=settings.RECRAFT_API_KEY,
        style=settings.STYLE,
        number_of_images=int(settings.NUMBER_OF_IMAGES),
        size=settings.SIZE,
        response_format=settings.RESPONSE_FORMAT,
    )
