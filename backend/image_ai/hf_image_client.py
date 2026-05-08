import os
import uuid
import io
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables once when module is imported
load_dotenv()

class HFImageClient:
    """
    Hugging Face image generation client with Supabase Cloud Storage support.
    """

    def __init__(self):
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN not found. Please check your .env file.")

        self.model_name = os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
        self.provider = os.getenv("HF_IMAGE_PROVIDER", "auto")

        self.client = InferenceClient(
            provider=self.provider,
            api_key=hf_token
        )
        
        # Supabase Config for Cloud Storage
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        self.bucket_name = os.getenv("SUPABASE_BUCKET", "career-images")

    def generate_image(self, prompt, output_dir=None):
        """
        Generate an image and upload to Supabase Cloud or save locally.
        """
        if not prompt or not prompt.strip():
            return {"success": False, "message": "Image prompt cannot be empty."}

        try:
            # 1. Generate Image from Hugging Face
            image = self.client.text_to_image(
                prompt=prompt.strip(),
                model=self.model_name
            )

            filename = f"career_image_{uuid.uuid4().hex}.png"
            
            # 2. Try Cloud Upload (Supabase)
            if self.supabase_url and self.supabase_key:
                try:
                    from supabase import create_client
                    supabase_client = create_client(self.supabase_url, self.supabase_key)
                    
                    # Convert PIL Image to Bytes for upload
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    
                    # Upload to Supabase Storage
                    response = supabase_client.storage.from_(self.bucket_name).upload(
                        path=filename,
                        file=img_byte_arr.getvalue(),
                        file_options={"content-type": "image/png"}
                    )
                    
                    # Get Public URL
                    public_url = supabase_client.storage.from_(self.bucket_name).get_public_url(filename)
                    
                    return {
                        "success": True,
                        "url": public_url,
                        "filename": filename,
                        "is_cloud": True
                    }
                except Exception as cloud_err:
                    print(f"⚠️ Supabase Upload Failed, falling back to local: {cloud_err}")

            # 3. Fallback to Local Storage
            if output_dir is None:
                current_file_dir = Path(__file__).resolve().parent
                backend_root = current_file_dir.parent
                output_dir = backend_root / "uploads" / "images"
            
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            image_path = output_dir / filename
            image.save(image_path)
            
            return {
                "success": True,
                "url": f"/generated-images/{filename}",
                "filename": filename,
                "is_cloud": False
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Image generation failed: {str(e)}"
            }

def generate_image(prompt: str, output_dir: str = None) -> str:
    """
    Convenience function for CareerMentorAgent.
    Returns a URL string (Cloud or Local).
    """
    try:
        client = HFImageClient()
        result = client.generate_image(prompt, output_dir)
        
        if result["success"]:
            return result["url"]
        else:
            return f"Error: {result['message']}"
    except Exception as e:
        return f"Error: {str(e)}"