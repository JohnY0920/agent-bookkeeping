import asyncio
from app.config import settings

_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        import boto3
        kwargs = {
            "region_name": settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID or None,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY or None,
        }
        if settings.AWS_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL
        _s3_client = boto3.client("s3", **kwargs)
    return _s3_client


async def upload_file(local_path: str, destination_path: str) -> dict:
    """Upload a local file to S3 and return the s3:// storage path."""
    client = _get_s3_client()
    await asyncio.to_thread(
        client.upload_file, local_path, settings.S3_BUCKET, destination_path
    )
    return {
        "storage_path": f"s3://{settings.S3_BUCKET}/{destination_path}",
        "bucket": settings.S3_BUCKET,
        "path": destination_path,
    }


async def download_file(storage_path: str, local_path: str) -> dict:
    """Download a file from S3 to a local path."""
    path = storage_path.removeprefix(f"s3://{settings.S3_BUCKET}/")
    client = _get_s3_client()
    await asyncio.to_thread(
        client.download_file, settings.S3_BUCKET, path, local_path
    )
    return {"local_path": local_path, "storage_path": storage_path}


async def get_signed_url(storage_path: str, expiration_minutes: int = 60) -> dict:
    """Generate a time-limited pre-signed URL for temporary read access."""
    path = storage_path.removeprefix(f"s3://{settings.S3_BUCKET}/")
    client = _get_s3_client()
    url = await asyncio.to_thread(
        client.generate_presigned_url,
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": path},
        ExpiresIn=expiration_minutes * 60,
    )
    return {"signed_url": url, "expires_in_minutes": expiration_minutes}


async def delete_file(storage_path: str) -> dict:
    """Delete a file from S3."""
    path = storage_path.removeprefix(f"s3://{settings.S3_BUCKET}/")
    client = _get_s3_client()
    await asyncio.to_thread(
        client.delete_object, Bucket=settings.S3_BUCKET, Key=path
    )
    return {"deleted": True, "storage_path": storage_path}
