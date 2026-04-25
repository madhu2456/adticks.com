"""
AdTicks — Local filesystem storage service.

Replaces DigitalOcean Spaces with local folder storage.
Files are saved to settings.STORAGE_ROOT and served by the API.
"""

import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """High-level wrapper around local filesystem storage."""

    def __init__(self) -> None:
        self.root = Path(settings.STORAGE_ROOT)
        # Ensure root directory exists
        self.root.mkdir(parents=True, exist_ok=True)

    def _get_path(self, path: str) -> Path:
        """Helper to get a full Path object and ensure parent directories exist."""
        full_path = self.root / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return full_path

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def upload_json(self, path: str, data: dict[str, Any]) -> str:
        """Serialize *data* to JSON and save to *path*."""
        full_path = self._get_path(path)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as exc:
            logger.error("upload_json failed for %s: %s", path, exc)
            raise
        return self._public_url(path)

    def download_json(self, path: str) -> dict[str, Any]:
        """Read the JSON file at *path*."""
        full_path = self.root / path
        if not full_path.exists():
            logger.warning("download_json: file not found: %s", path)
            return {}
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error("download_json failed for %s: %s", path, exc)
            raise

    def upload_file(self, path: str, content: bytes) -> str:
        """Save raw *content* bytes to *path*."""
        full_path = self._get_path(path)
        try:
            with open(full_path, "wb") as f:
                f.write(content)
        except Exception as exc:
            logger.error("upload_file failed for %s: %s", path, exc)
            raise
        return self._public_url(path)

    def delete_file(self, path: str) -> None:
        """Delete the file at *path* (no-op if missing)."""
        full_path = self.root / path
        try:
            if full_path.exists():
                full_path.unlink()
        except Exception as exc:
            logger.error("delete_file failed for %s: %s", path, exc)
            raise

    # ------------------------------------------------------------------
    # Path builders
    # ------------------------------------------------------------------

    @staticmethod
    def ai_path(project_id: str, filename: str) -> str:
        return f"projects/{project_id}/ai/{filename}"

    @staticmethod
    def seo_path(project_id: str, filename: str) -> str:
        return f"projects/{project_id}/seo/{filename}"

    @staticmethod
    def gsc_path(project_id: str, filename: str) -> str:
        return f"projects/{project_id}/gsc/{filename}"

    @staticmethod
    def ads_path(project_id: str, filename: str) -> str:
        return f"projects/{project_id}/ads/{filename}"

    @staticmethod
    def exports_path(project_id: str, filename: str) -> str:
        return f"projects/{project_id}/exports/{filename}"

    @staticmethod
    def avatar_path(user_id: str, filename: str) -> str:
        return f"users/{user_id}/avatar/{filename}"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _public_url(self, path: str) -> str:
        """Return a public URL for the file served via FastAPI mount."""
        base = settings.BASE_URL.rstrip("/")
        # We'll mount it at /api/storage in main.py
        return f"{base}/api/storage/{path}"


# Singleton
storage = StorageService()
