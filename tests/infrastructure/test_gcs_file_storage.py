from unittest.mock import Mock, patch

from app.infrastructure.adapters.gcs_file_storage import GoogleCloudStorageAdapter


def _build_adapter(make_public: bool) -> tuple[GoogleCloudStorageAdapter, Mock, Mock]:
    """Construye un adaptador GCS con clientes y blobs falsos para pruebas."""
    
    fake_blob = Mock()
    fake_blob.public_url = "https://storage.googleapis.com/bucket/path/to/file.jpg"

    fake_bucket = Mock()
    fake_bucket.blob.return_value = fake_blob

    fake_client = Mock()
    fake_client.bucket.return_value = fake_bucket

    with patch(
        "app.infrastructure.adapters.gcs_file_storage.storage.Client",
        return_value=fake_client,
    ):
        adapter = GoogleCloudStorageAdapter(
            bucket_name="bucket",
            project_id="project-id",
            make_public=make_public,
        )

    return adapter, fake_bucket, fake_blob


def test_upload_blocking_returns_gs_url_when_not_public() -> None:
    """Verifica que el adaptador GCS devuelve la URL gs:// cuando make_public es False."""
    
    adapter, _, fake_blob = _build_adapter(make_public=False)

    result = adapter._upload_blocking(
        object_name="incidents/evidence/incidents/123/file.jpg",
        content_type="image/jpeg",
        data=b"image-bytes",
    )

    fake_blob.upload_from_string.assert_called_once_with(
        b"image-bytes",
        content_type="image/jpeg",
    )
    fake_blob.make_public.assert_not_called()
    assert result.file_url == "gs://bucket/incidents/evidence/incidents/123/file.jpg"


def test_upload_blocking_returns_public_url_when_public_enabled() -> None:
    """Verifica que el adaptador GCS devuelve la URL pública cuando make_public es True."""
    
    adapter, _, fake_blob = _build_adapter(make_public=True)

    result = adapter._upload_blocking(
        object_name="incidents/evidence/incidents/123/file.jpg",
        content_type="image/jpeg",
        data=b"image-bytes",
    )

    fake_blob.upload_from_string.assert_called_once_with(
        b"image-bytes",
        content_type="image/jpeg",
    )
    fake_blob.make_public.assert_called_once()
    assert result.file_url == "https://storage.googleapis.com/bucket/path/to/file.jpg"
