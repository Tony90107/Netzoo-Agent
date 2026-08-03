"""Runtime assembly used by Uvicorn and the Compose deployment."""

from __future__ import annotations

import os
from pathlib import Path

from .api import create_app
from .blob_store import FileSystemBlobStore, S3BlobStore
from .database import Base, create_database_engine, create_session_factory
from .repository import ObserverRepository
from .settings import CollectorSettings


def create_runtime_app():
    settings = CollectorSettings.from_environment()
    engine = create_database_engine(settings.database_url)
    Base.metadata.create_all(engine)
    repository = ObserverRepository(create_session_factory(engine))

    endpoint = os.environ.get("NETZOO_OBSERVER_OBJECT_ENDPOINT", "").strip()
    if endpoint:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=os.environ.get("NETZOO_OBSERVER_OBJECT_REGION", "us-east-1"),
            aws_access_key_id=os.environ["NETZOO_OBSERVER_OBJECT_ACCESS_KEY"],
            aws_secret_access_key=os.environ["NETZOO_OBSERVER_OBJECT_SECRET_KEY"],
        )
        try:
            client.head_bucket(Bucket=settings.object_store_bucket)
        except ClientError:
            client.create_bucket(Bucket=settings.object_store_bucket)
        blob_store = S3BlobStore(client, settings.object_store_bucket)
    else:
        blob_root = Path(
            os.environ.get(
                "NETZOO_OBSERVER_BLOB_ROOT",
                ".netzoo/observer-blobs",
            )
        )
        blob_store = FileSystemBlobStore(blob_root)
    return create_app(settings, repository, blob_store)


app = create_runtime_app()


__all__ = ["app", "create_runtime_app"]
