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
    def save(self, key: str, file_bytes: bytes) -> str:
        raise NotImplementedError("S3Storage is not implemented in v1")

    def get_url(self, key: str) -> str:
        raise NotImplementedError("S3Storage is not implemented in v1")

    def delete(self, key: str) -> None:
        raise NotImplementedError("S3Storage is not implemented in v1")


def get_storage() -> StorageBackend:
    """Return the configured storage backend."""
    if settings.storage_backend == "disk":
        return DiskStorage(settings.media_root)
    return S3Storage()
