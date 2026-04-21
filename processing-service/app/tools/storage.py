import asyncio
from datetime import timedelta
from app.config import settings

_client = None


def _get_gcs_client():
    global _client
    if _client is None:
        from google.cloud import storage
        _client = storage.Client(project=settings.GCS_PROJECT_ID)
    return _client


async def upload_file(local_path: str, destination_path: str) -> dict:
    """Upload a local file to GCS and return the gs:// storage path."""
    client = _get_gcs_client()
    bucket = client.bucket(settings.GCS_BUCKET)
    blob = bucket.blob(destination_path)
    await asyncio.to_thread(blob.upload_from_filename, local_path)
    return {
        "storage_path": f"gs://{settings.GCS_BUCKET}/{destination_path}",
        "bucket": settings.GCS_BUCKET,
        "path": destination_path,
    }


async def download_file(storage_path: str, local_path: str) -> dict:
    """Download a file from GCS to a local path."""
    path = storage_path.removeprefix(f"gs://{settings.GCS_BUCKET}/")
    client = _get_gcs_client()
    blob = client.bucket(settings.GCS_BUCKET).blob(path)
    await asyncio.to_thread(blob.download_to_filename, local_path)
    return {"local_path": local_path, "storage_path": storage_path}


async def get_signed_url(storage_path: str, expiration_minutes: int = 60) -> dict:
    """Generate a time-limited signed URL for temporary read access."""
    path = storage_path.removeprefix(f"gs://{settings.GCS_BUCKET}/")
    client = _get_gcs_client()
    blob = client.bucket(settings.GCS_BUCKET).blob(path)
    url = await asyncio.to_thread(
        blob.generate_signed_url,
        expiration=timedelta(minutes=expiration_minutes),
        method="GET",
    )
    return {"signed_url": url, "expires_in_minutes": expiration_minutes}
