import asyncio
import logging
import base64
from codeinterpreterapi import CodeInterpreterSession
from typing import Dict, Any

async def generate_visualization_response_async(query: str) -> Dict[str, Any]:
    logging.debug("Starting CodeInterpreterSession for query: %s", query)
    try:
        async with CodeInterpreterSession() as session:
            response = await session.agenerate_response(query)
            logging.debug("Received response from CodeInterpreterSession")

            if response.files:
                for file in response.files:
                    if file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        img_base64 = base64.b64encode(file.content).decode('utf-8')
                        logging.debug(f"Image converted to base64: {img_base64[:20]}...")
                        return {
                            "type": "visualization",
                            "status": "success",
                            "message": response.content,
                            "image": f"data:image/png;base64,{img_base64}"  # Add data URI prefix
                        }
            
            logging.debug("No image found in response")
            return {
                "type": "text",
                "status": "success",
                "content": response.content
            }
    except Exception as e:
        logging.error(f"Error in generate_visualization_response_async: {str(e)}")
        return {"type": "error", "status": "error", "content": str(e)}

def generate_visualization_response_sync(query: str) -> Dict[str, Any]:
    """Wrapper to run async function in sync context."""
    return asyncio.run(generate_visualization_response_async(query))