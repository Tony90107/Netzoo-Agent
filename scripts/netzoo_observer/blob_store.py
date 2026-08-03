"""Object-store boundary for sanitized observer attachments."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class BlobStore(Protocol):
    def put(self, object_key: str, content: bytes, content_type: str) -> None: ...

    def get(self, object_key: str) -> bytes: ...

    def delete(self, object_key: str) -> None: ...


class MemoryBlobStore:
    """Deterministic backend for tests and local process demos."""

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def put(self, object_key: str, content: bytes, content_type: str) -> None:
        del content_type
        self._objects[object_key] = bytes(content)

    def get(self, object_key: str) -> bytes:
        return self._objects[object_key]

    def delete(self, object_key: str) -> None:
        self._objects.pop(object_key, None)


class FileSystemBlobStore:
    """Private local backend used when an S3 service is not configured."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(mode=0o700, parents=True, exist_ok=True)

    def _path(self, object_key: str) -> Path:
        path = (self._root / object_key).resolve()
        if self._root not in path.parents:
            raise ValueError("object key escaped the blob root")
        return path

    def put(self, object_key: str, content: bytes, content_type: str) -> None:
        del content_type
        path = self._path(object_key)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_bytes(content)
        path.chmod(0o600)

    def get(self, object_key: str) -> bytes:
        return self._path(object_key).read_bytes()

    def delete(self, object_key: str) -> None:
        self._path(object_key).unlink(missing_ok=True)


class S3BlobStore:
    """S3-compatible backend; credentials remain in the SDK credential chain."""

    def __init__(self, client, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def put(self, object_key: str, content: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=object_key,
            Body=content,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )

    def get(self, object_key: str) -> bytes:
        result = self._client.get_object(Bucket=self._bucket, Key=object_key)
        return result["Body"].read()

    def delete(self, object_key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=object_key)


__all__ = ["BlobStore", "FileSystemBlobStore", "MemoryBlobStore", "S3BlobStore"]
