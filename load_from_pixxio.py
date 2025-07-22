import requests
from PIL import Image
from io import BytesIO
import torch
import numpy as np

class LoadImageFromPixxioAPI:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_id": ("STRING", {"default": ""}),
                "api_key": ("STRING", {"default": ""}),
                "mediaspace_url": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "load_image"
    CATEGORY = "loaders"

    def load_image(self, file_id, api_key, mediaspace_url):
        if not file_id or not api_key or not mediaspace_url:
            raise ValueError("file_id, api_key, and mediaspace_url are required")
        # 1. Request the conversion/download link
        convert_url = f"https://{mediaspace_url}/api/v1/files/{file_id}/convert"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {
            "downloadType": "original",
            "responseType": "path",
        }

        try:
            resp = requests.get(convert_url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get download URL from Pixxio API: {str(e)}")
        data = resp.json()
        download_url = data.get("downloadURL")
        if not download_url:
            raise Exception("No downloadURL in Pixxio API response.")

        # 2. Download the image from the downloadURL
        try:
            img_resp = requests.get(download_url, timeout=30)
            img_resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download image from Pixxio: {str(e)}")

        try:
            image = Image.open(BytesIO(img_resp.content))
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            elif image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')
            
            image = np.array(image).astype(np.float32) / 255.0
            if image.ndim == 2:  # Grayscale
                image = np.expand_dims(image, axis=-1)
            image_tensor = torch.from_numpy(image)[None,]
            
            return (image_tensor,)
        except Exception as e:
            raise Exception(f"Failed to process image: {str(e)}")

NODE_CLASS_MAPPINGS = {
    "LoadImageFromPixxioAPI": LoadImageFromPixxioAPI,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromPixxioAPI": "Load Image from Pixx.io",
}
