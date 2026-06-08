import os
from abc import ABC, abstractmethod

from backend.config import settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, file_bytes: bytes) -> str:
        """Persist file_bytes at the given key. Returns the storage key."""
        ...

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Return a resolvable path or URL for the given key."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the file at the given key."""
        ...


class DiskStorage(StorageBackend):
    def __init__(self, media_root: str) -> None:
        self._root = media_root

    def save(self, key: str, file_bytes: bytes) -> str:
        dest = os.path.join(self._root, key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(file_bytes)
        return key

    def get_url(self, key: str) -> str:
        return os.path.join(self._root, key)

    def delete(self, key: str) -> None:
        path = os.path.join(self._root, key)
        if os.path.exists(path):
            os.remove(path)


class S3Storage(StorageBackend):
    def __init__(self) -> None:
        import boto3
        from botocore.config import Config

        missing = [
            name for name, val in {
                "B2_ENDPOINT_URL": settings.b2_endpoint_url,
                "B2_ACCESS_KEY_ID": settings.b2_access_key_id,
                "B2_SECRET_ACCESS_KEY": settings.b2_secret_access_key,
                "B2_BUCKET_NAME": settings.b2_bucket_name,
            }.items()
            if not val
        ]
        if missing:
            raise ValueError(
                f"STORAGE_BACKEND=s3 requires these env vars: {', '.join(missing)}"
            )

        self._bucket = settings.b2_bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.b2_endpoint_url,
            aws_access_key_id=settings.b2_access_key_id,
            aws_secret_access_key=settings.b2_secret_access_key,
            config=Config(signature_version="s3v4"),
        )

    def save(self, key: str, file_bytes: bytes) -> str:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=file_bytes)
        return key

    def get_url(self, key: str) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=3600,
        )

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)


def get_storage() -> StorageBackend:
    """Return the configured storage backend."""
    if settings.storage_backend == "s3":
        return S3Storage()
    return DiskStorage(settings.media_root)
