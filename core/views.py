import json
import logging
import os
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from core.flows.content_generation.flow import ContentGenerationFlow
from core.tools.whatsapp_twilio import send_whatsapp_message

logger = logging.getLogger(__name__)


@api_view(['POST'])
def generate_content(request):
    """
    API endpoint for generating social media content (text and/or images).
    
    Accepts POST requests with a user_query parameter.
    Returns generated content including text posts and images.
    
    Request body (JSON):
    {
        "user_query": "Create a professional LinkedIn post about AI in healthcare"
    }
    
    Returns:
    {
        "success": true,
        "data": [
            {
                "text": "Generated blog post content...",
                "image": "https://..."
            }
        ],
        "message": "Content generated successfully"
    }
    """
    try:
        # Get user_query from request data
        user_query = request.data.get('user_query')
        
        if not user_query:
            return Response(
                {
                    "success": False,
                    "error": "user_query is required",
                    "message": "Please provide a user_query in the request body"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize and run the flow
        flow = ContentGenerationFlow()
        
        # Run the flow synchronously (kickoff handles async internally)
        result = flow.kickoff(user_query=user_query)
        
        # Format the response
        if result:
            return Response(
                {
                    "success": True,
                    "data": result,
                    "message": "Content generated successfully"
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "success": False,
                    "data": [],
                    "message": "No content was generated"
                },
                status=status.HTTP_200_OK
            )
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}")
        return Response(
            {
                "success": False,
                "error": "Invalid JSON in response",
                "message": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error generating content: {e}", exc_info=True)
        return Response(
            {
                "success": False,
                "error": str(e),
                "message": "An error occurred while generating content"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def process_twilio_incoming_message(request):
    """
    Extract incoming WhatsApp message from Twilio webhook POST.
    Returns: (from_number, message_text)
    """
    num_media = int(request.POST.get("NumMedia", 0))
    msg_text = request.POST.get('Body', '').strip()
    

    from_num = request.POST.get('From', '').replace('whatsapp:', '')
    return from_num, msg_text


def _validate_twilio_request(request):
    """Validate Twilio request signature (optional, can disable for testing)."""
    if os.getenv("DISABLE_TWILIO_VALIDATION", "false").lower() == "true":
        return True
    
    try:
        from twilio.request_validator import RequestValidator
        from django.conf import settings
        
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        signature = request.META.get("HTTP_X_TWILIO_SIGNATURE", "")
        form_data = dict(request.POST.items())
        
        # Build full URL using request path (avoids reverse lookup issues)
        scheme = request.META.get("HTTP_X_FORWARDED_PROTO", request.scheme)
        host = request.META.get("HTTP_X_FORWARDED_HOST", request.get_host())
        url = f"{scheme}://{host}{request.path}"
        
        return validator.validate(url, form_data, signature)
    except Exception as e:
        logger.warning(f"Twilio validation failed: {e}")
        return False


@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_webhook(request):
    """
    Twilio webhook endpoint for receiving WhatsApp messages.
    When a user sends a WhatsApp message, this endpoint:
    1. Extracts the message and sender
    2. Runs the content generation flow
    3. Sends results back to the sender via WhatsApp
    """
    try:
        # Optional: validate Twilio signature
        if not _validate_twilio_request(request):
            logger.warning("Twilio request validation failed")
            # Continue anyway for development/testing
        
        # Extract incoming message
        from_number, message_text = process_twilio_incoming_message(request)
        
        if not message_text:
            logger.info("Received empty WhatsApp message, ignoring.")
            return HttpResponse("OK", status=200)
        
        logger.info(f"Received WhatsApp message from {from_number}: {message_text[:100]}...")
        
        # Run the flow with the incoming message
        flow = ContentGenerationFlow()
        # Set the recipient so whatsapp_send sends back to the sender
        flow.state.whatsapp_to = from_number
        result = flow.kickoff(user_query=message_text)
        
        # Check if WhatsApp send succeeded
        whatsapp_output = getattr(flow.state, "whatsapp_send_output", None)
        if whatsapp_output:
            logger.info(f"WhatsApp response sent to {from_number}: {whatsapp_output}")
        else:
            # Fallback: send manually if flow didn't send
            logger.warning("Flow didn't send WhatsApp response, sending manually...")
            if result:
                for item in result:
                    text = item.get("text", "")
                    image = item.get("image")
                    if text or image:
                        send_whatsapp_message(
                            to=from_number,
                            text=text or "Generated content",
                            image_url=image
                        )
        
        return HttpResponse("OK", status=200)
        
    except Exception as e:
        logger.exception(f"Error processing WhatsApp webhook: {e}")
        # Try to send error message back to user
        try:
            from_number = request.POST.get('From', '').replace('whatsapp:', '')
            if from_number:
                send_whatsapp_message(
                    to=from_number,
                    text=f"Sorry, an error occurred: {str(e)}"
                )
        except:
            pass
        return HttpResponse("Error", status=500)
