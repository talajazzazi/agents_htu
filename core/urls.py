from django.urls import path
from core.views import generate_content, whatsapp_webhook

app_name = 'core'

urlpatterns = [
    path('api/generate-content/', generate_content, name='generate-content'),
    path('api/whatsapp/webhook/', whatsapp_webhook, name='whatsapp_webhook'),
]
