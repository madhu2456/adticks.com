"""
AdTicks — DigitalOcean Spaces storage service.

Uses boto3 with an S3-compatible endpoint so the same code works for
any S3-compatible object store.

Folder conventions
------------------
adticks-data/
  projects/{project_id}/
    ai/
    seo/
    gsc/
    ads/
    exports/
"""

import json
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_client():
    """Return a boto3 S3 client configured for DigitalOcean Spaces."""
    return boto3.client(
        "s3",
        region_name="nyc3",
        endpoint_url=settings.DO_SPACES_ENDPOINT,
        aws_access_key_id=settings.DO_SPACES_KEY,
        aws_secret_access_key=settings.DO_SPACES_SECRET,
    )


class StorageService:
    """High-level wrapper around DigitalOcean Spaces / S3."""

    def __init__(self) -> None:
        self._bucket = settings.DO_SPACES_BUCKET

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def upload_json(self, path: str, data: dict[str, Any]) -> str:
        """
        Serialize *data* to JSON and upload to *path* inside the bucket.

        Returns the public URL of the uploaded object.
        """
        client = _get_client()
        body = json.dumps(data, default=str).encode("utf-8")
        try:
            client.put_object(
                Bucket=self._bucket,
                Key=path,
                Body=body,
                ContentType="application/json",
            )
        except ClientError as exc:
            logger.error("upload_json failed for %s: %s", path, exc)
            raise
        return self._public_url(path)

    def download_json(self, path: str) -> dict[str, Any]:
        """
        Download the object at *path* and deserialize it as JSON.

        Returns an empty dict if the object does not exist.
        """
        client = _get_client()
        try:
            response = client.get_object(Bucket=self._bucket, Key=path)
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("NoSuchKey", "404"):
                logger.warning("download_json: key not found: %s", path)
                return {}
            logger.error("download_json failed for %s: %s", path, exc)
            raise

    def upload_file(self, path: str, content: bytes) -> str:
        """
        Upload raw *content* bytes to *path* inside the bucket.

        Returns the public URL of the uploaded object.
        """
        client = _get_client()
        try:
            client.put_object(
                Bucket=self._bucket,
                Key=path,
                Body=content,
            )
        except ClientError as exc:
            logger.error("upload_file failed for %s: %s", path, exc)
            raise
        return self._public_url(path)

    def delete_file(self, path: str) -> None:
        """Delete the object at *path* from the bucket (no-op if missing)."""
        client = _get_client()
        try:
            client.delete_object(Bucket=self._bucket, Key=path)
        except ClientError as exc:
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

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _public_url(self, path: str) -> str:
        endpoint = settings.DO_SPACES_ENDPOINT.rstrip("/")
        return f"{endpoint}/{self._bucket}/{path}"


# Singleton
storage = StorageService()
