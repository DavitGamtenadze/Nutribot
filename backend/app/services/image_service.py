from __future__ import annotations

import io
import uuid

from fastapi import UploadFile
from PIL import Image

from app.config import get_settings

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"}
OPENAI_SUPPORTED_FORMATS = {"PNG", "JPEG", "GIF", "WEBP"}


class ImageService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def save_upload(self, file: UploadFile) -> str:
        filename = file.filename or "upload"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported image format '.{ext}'. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

        max_bytes = self._settings.max_upload_size_mb * 1024 * 1024
        data = file.file.read()
        if len(data) > max_bytes:
            raise ValueError(f"Image exceeds {self._settings.max_upload_size_mb}MB limit")

        img = Image.open(io.BytesIO(data))

        # Resize if longest side > 1024px
        max_side = 1024
        if max(img.size) > max_side:
            ratio = max_side / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # Convert to OpenAI-supported format if needed
        if img.format not in OPENAI_SUPPORTED_FORMATS:
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            save_format = "JPEG"
            out_ext = "jpg"
        else:
            save_format = img.format
            out_ext = ext

        uid = uuid.uuid4().hex
        out_filename = f"{uid}.{out_ext}"
        out_path = f"{self._settings.upload_dir}/{out_filename}"

        buf = io.BytesIO()
        img.save(buf, format=save_format, quality=85)
        buf.seek(0)

        with open(out_path, "wb") as f:
            f.write(buf.read())

        return f"/uploads/{out_filename}"
