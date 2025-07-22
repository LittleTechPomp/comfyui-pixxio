import requests
from PIL import Image
import torch
import numpy as np
import json
from io import BytesIO

class AutoUploadImageToPixxioCollection:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "api_key": ("STRING", {"default": ""}),
                "collection_id": ("INT", {"default": 0}),
                "mediaspace_url": ("STRING", {"default": ""}),
                "file_name": ("STRING", {"default": "comfyui_upload.jpg"}),
                "description": ("STRING", {"default": "Uploaded via ComfyUI"}),
                "keywords": ("STRING", {"default": "comfyui,pixxio,upload"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "upload_image"
    CATEGORY = "uploaders"

    def upload_image(self, image, api_key, collection_id, mediaspace_url, file_name, description, keywords):
        if not api_key or not mediaspace_url:
            raise ValueError("api_key and mediaspace_url are required")
        
        if collection_id <= 0:
            raise ValueError("collection_id must be a positive integer")
        # Robust tensor to PIL Image conversion
        def tensor_to_pil(image):
            if isinstance(image, torch.Tensor):
                arr = image.cpu().numpy()
                # Remove batch dimension if present
                if arr.ndim == 4 and arr.shape[0] == 1:
                    arr = arr[0]
                # Handle channel-first (C, H, W)
                if arr.ndim == 3 and arr.shape[0] in (1, 3, 4):
                    arr = np.transpose(arr, (1, 2, 0))
                # Convert [0,1] floats to [0,255] uint8
                if arr.dtype != np.uint8:
                    arr = np.clip(arr * 255, 0, 255).astype(np.uint8)
                # Remove alpha if present
                if arr.shape[2] == 4:
                    arr = arr[:, :, :3]
                return Image.fromarray(arr)
            raise Exception("Unsupported image format. Must be a torch.Tensor.")

        try:
            pil_image = tensor_to_pil(image)
        except Exception as e:
            print("Image conversion error:", e)
            raise

        # Save PIL image to bytes as JPEG
        img_bytes = BytesIO()
        pil_image.save(img_bytes, format="JPEG", quality=95)
        img_bytes.seek(0)

        url = f"https://{mediaspace_url}/api/v1/files"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        # Prepare Pixxio form data
        data = {
            "fileName": file_name,
            "description": description,
            "keywords": json.dumps([k.strip() for k in keywords.split(",") if k.strip()]),
            "collectionIDs": json.dumps([collection_id])
        }

        files = {
            "file": (file_name, img_bytes, "image/jpeg"),
        }

        try:
            response = requests.post(url, headers=headers, data=data, files=files, timeout=60)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_msg = f"Pixxio API error: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text}"
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to upload to Pixxio: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during upload: {str(e)}")
        return (image,)

NODE_CLASS_MAPPINGS = {
    "AutoUploadImageToPixxioCollection": AutoUploadImageToPixxioCollection,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AutoUploadImageToPixxioCollection": "Auto-Upload Image to Pixxio Collection",
}
