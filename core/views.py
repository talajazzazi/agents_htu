import json
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from core.flows.content_generation.flow import ContentGenerationFlow

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
