"""MinIO client for object storage operations."""

from minio import Minio
from minio.error import S3Error
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Optional
import logging

from src.config import get_settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """Client for interacting with MinIO object storage."""

    def __init__(self):
        """Initialize MinIO client."""
        settings = get_settings()
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise

    def upload_file(self, file_path: Path, object_name: str) -> str:
        """Upload a file to MinIO.

        Args:
            file_path: Path to local file
            object_name: Name for object in MinIO

        Returns:
            Object name in MinIO
        """
        try:
            self.client.fput_object(
                self.bucket,
                object_name,
                str(file_path)
            )
            logger.info(f"Uploaded {file_path} to {self.bucket}/{object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise

    def upload_fileobj(self, file_obj: BinaryIO, object_name: str, length: int = -1) -> str:
        """Upload a file object to MinIO.

        Args:
            file_obj: File-like object to upload
            object_name: Name for object in MinIO
            length: Size of data in bytes (-1 for unknown)

        Returns:
            Object name in MinIO
        """
        try:
            self.client.put_object(
                self.bucket,
                object_name,
                file_obj,
                length=length
            )
            logger.info(f"Uploaded file object to {self.bucket}/{object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Error uploading file object: {e}")
            raise

    def download_file(self, object_name: str, file_path: Path) -> Path:
        """Download a file from MinIO.

        Args:
            object_name: Name of object in MinIO
            file_path: Local path to save file

        Returns:
            Path to downloaded file
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            self.client.fget_object(
                self.bucket,
                object_name,
                str(file_path)
            )
            logger.info(f"Downloaded {self.bucket}/{object_name} to {file_path}")
            return file_path
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise

    def get_file_bytes(self, object_name: str) -> bytes:
        """Get file content as bytes.

        Args:
            object_name: Name of object in MinIO

        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error reading file: {e}")
            raise

    def get_object_url(self, object_name: str) -> str:
        """Get presigned URL for object.

        Args:
            object_name: Name of object in MinIO

        Returns:
            Presigned URL
        """
        try:
            settings = get_settings()
            protocol = "https" if settings.minio_secure else "http"
            return f"{protocol}://{settings.minio_endpoint}/{self.bucket}/{object_name}"
        except S3Error as e:
            logger.error(f"Error generating URL: {e}")
            raise

    def object_exists(self, object_name: str) -> bool:
        """Check if object exists.

        Args:
            object_name: Name of object in MinIO

        Returns:
            True if object exists
        """
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False

    def delete_object(self, object_name: str):
        """Delete an object.

        Args:
            object_name: Name of object to delete
        """
        try:
            self.client.remove_object(self.bucket, object_name)
            logger.info(f"Deleted {self.bucket}/{object_name}")
        except S3Error as e:
            logger.error(f"Error deleting object: {e}")
            raise
