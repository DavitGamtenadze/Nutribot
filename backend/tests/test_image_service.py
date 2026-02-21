from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.config import Settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_png_bytes(width: int = 100, height: int = 100) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


def make_jpg_bytes(width: int = 100, height: int = 100) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(0, 255, 0)).save(buf, format="JPEG")
    return buf.getvalue()


def make_upload_file(data: bytes, filename: str = "test.png") -> MagicMock:
    f = MagicMock()
    f.filename = filename
    f.file = io.BytesIO(data)
    return f


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestImageServiceSaveUpload:
    """Tests for ImageService.save_upload()."""

    def test_valid_png_saves_and_returns_path(self, tmp_path) -> None:
        data = make_png_bytes()
        upload = make_upload_file(data, filename="test.png")

        with patch("app.services.image_service.get_settings") as mock_get_settings:
            mock_get_settings.return_value = Settings(upload_dir=str(tmp_path), max_upload_size_mb=10)
            from app.services.image_service import ImageService

            service = ImageService()
            result = service.save_upload(upload)

        assert result.startswith("/uploads/")
        assert result.endswith(".png")
        # UUID hex is 32 chars + dot + ext
        filename = result[len("/uploads/") :]
        assert len(filename) == 32 + 1 + 3  # e.g. <32hex>.png
        assert (tmp_path / filename).exists()

    def test_valid_jpg_saves_and_returns_path(self, tmp_path) -> None:
        data = make_jpg_bytes()
        upload = make_upload_file(data, filename="photo.jpg")

        with patch("app.services.image_service.get_settings") as mock_get_settings:
            mock_get_settings.return_value = Settings(upload_dir=str(tmp_path), max_upload_size_mb=10)
            from app.services.image_service import ImageService

            service = ImageService()
            result = service.save_upload(upload)

        assert result.startswith("/uploads/")
        assert result.endswith(".jpg")
        filename = result[len("/uploads/") :]
        assert (tmp_path / filename).exists()

    def test_unsupported_extension_raises(self, tmp_path) -> None:
        upload = make_upload_file(b"not an image", filename="test.exe")

        with patch("app.services.image_service.get_settings") as mock_get_settings:
            mock_get_settings.return_value = Settings(upload_dir=str(tmp_path), max_upload_size_mb=10)
            from app.services.image_service import ImageService

            service = ImageService()
            with pytest.raises(ValueError, match="Unsupported image format"):
                service.save_upload(upload)

    def test_oversized_file_raises(self, tmp_path) -> None:
        # Build data larger than 10 MB
        oversized_data = b"x" * (10 * 1024 * 1024 + 1)
        upload = make_upload_file(oversized_data, filename="big.png")

        with patch("app.services.image_service.get_settings") as mock_get_settings:
            mock_get_settings.return_value = Settings(upload_dir=str(tmp_path), max_upload_size_mb=10)
            from app.services.image_service import ImageService

            service = ImageService()
            with pytest.raises(ValueError, match="exceeds"):
                service.save_upload(upload)

    def test_large_image_gets_resized(self, tmp_path) -> None:
        data = make_png_bytes(width=2000, height=2000)
        upload = make_upload_file(data, filename="large.png")

        with patch("app.services.image_service.get_settings") as mock_get_settings:
            mock_get_settings.return_value = Settings(upload_dir=str(tmp_path), max_upload_size_mb=10)
            from app.services.image_service import ImageService

            service = ImageService()
            result = service.save_upload(upload)

        filename = result[len("/uploads/") :]
        saved_path = tmp_path / filename
        assert saved_path.exists()

        with Image.open(saved_path) as saved_img:
            assert max(saved_img.size) <= 1024
