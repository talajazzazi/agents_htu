from django.urls import path
from core.views import generate_content

app_name = 'core'

urlpatterns = [
    path('api/generate-content/', generate_content, name='generate-content'),
]
