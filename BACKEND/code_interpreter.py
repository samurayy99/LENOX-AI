import asyncio
import logging
from codeinterpreterapi import CodeInterpreterSession
from typing import Dict, Any

def execute_code_snippet(code_snippet: str, data: Dict[str, Any]) -> Dict:
    """Execute user-defined code snippet for data analysis."""
    local_vars = {'data': data}
    exec(code_snippet, {}, local_vars)
    return local_vars.get('result', {})

async def generate_visualization_response(query: str):
    """Generate visualization using code interpreter."""
    async with CodeInterpreterSession() as session:
        response = await session.agenerate_response(query)
        return response

async def generate_visualization_response_async(query: str):
    """Generate visualization using code interpreter asynchronously."""
    logging.debug("Starting CodeInterpreterSession for query: %s", query)
    async with CodeInterpreterSession() as session:
        response = await session.agenerate_response(query)
        logging.debug("Received response from CodeInterpreterSession")

        # Extracting the image data if it is available in the response
        if hasattr(response, 'files') and response.files:
            image_displayed = False
            for file in response.files:
                # Display the image using the show_image method
                if hasattr(file, 'show_image'):
                    logging.debug("Displaying image from response file")
                    file.show_image()
                    image_displayed = True
            if image_displayed:
                logging.debug("Image displayed successfully")
                return {"status": "success", "message": response.content}
            else:
                logging.error("Response does not contain a plot figure.")
                raise ValueError("Response does not contain a plot figure.")
        else:
            logging.error("Response does not contain a plot figure.")
            raise ValueError("Response does not contain a plot figure.")

def generate_visualization_response_sync(query: str):
    """Wrapper to run async function in sync context."""
    return asyncio.run(generate_visualization_response_async(query))