import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables once when module is imported
load_dotenv()


class HFImageClient:
    """
    Hugging Face image generation client.

    This uses Hugging Face Inference Providers, so your deployed backend
    does not need its own GPU. Hugging Face/provider handles inference.
    """

    def __init__(self):
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN not found. Please check your .env file.")

        self.model_name = os.getenv(
            "HF_IMAGE_MODEL",
            "black-forest-labs/FLUX.1-schnell"
        )

        self.provider = os.getenv("HF_IMAGE_PROVIDER", "auto")

        self.client = InferenceClient(
            provider=self.provider,
            api_key=hf_token
        )

    def generate_image(self, prompt, output_dir):
        """
        Generate an image from text prompt and save it locally.
        Returns a dict with success status, filename and path.
        """

        if not prompt or not prompt.strip():
            return {
                "success": False,
                "message": "Image prompt cannot be empty.",
                "model": self.model_name,
                "provider": self.provider
            }

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            image = self.client.text_to_image(
                prompt=prompt.strip(),
                model=self.model_name
            )

            filename = f"career_image_{uuid.uuid4().hex}.png"
            image_path = output_dir / filename

            image.save(image_path)

            return {
                "success": True,
                "message": "Image generated successfully.",
                "filename": filename,
                "path": str(image_path),
                "model": self.model_name,
                "provider": self.provider
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Hugging Face image generation failed: {str(e)}",
                "model": self.model_name,
                "provider": self.provider
            }


def generate_image(prompt: str, output_dir: str = None) -> str:
    """
    Convenience function for CareerMentorAgent.
    Returns an image URL (string) that can be displayed directly.
    """
    # Use environment variable or default directory
    if output_dir is None:
        output_dir = os.getenv("IMAGE_OUTPUT_DIR", "backend/uploads/images")
    # Ensure it's an absolute path for main.py to serve
    output_dir = Path(output_dir).resolve()

    try:
        client = HFImageClient()
    except ValueError as e:
        return f"Error: {str(e)}"

    result = client.generate_image(prompt, output_dir)

    if not result["success"]:
        return f"Image generation failed: {result['message']}"

    # Build a relative URL that FastAPI can serve
    # Assumes /generated-images/ is mapped to the output_dir in main.py
    return f"/generated-images/{result['filename']}"