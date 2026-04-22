"""Unit tests for StorageService (app.core.storage), mocking boto3."""
import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.core.storage import StorageService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_no_such_key_error():
    """Return a ClientError that looks like a NoSuchKey response."""
    return ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
        "GetObject",
    )


def _make_404_error():
    """Return a ClientError that looks like a 404 response."""
    return ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "GetObject",
    )


# ---------------------------------------------------------------------------
# upload_json
# ---------------------------------------------------------------------------

def test_upload_json_returns_url_containing_path():
    """upload_json returns a public URL that contains the object path."""
    service = StorageService()
    mock_client = MagicMock()

    with patch("app.core.storage._get_client", return_value=mock_client):
        url = service.upload_json("projects/proj-1/ai/result.json", {"key": "value"})

    mock_client.put_object.assert_called_once()
    assert "projects/proj-1/ai/result.json" in url


def test_upload_json_puts_correct_content_type():
    """upload_json sets ContentType to application/json."""
    service = StorageService()
    mock_client = MagicMock()

    with patch("app.core.storage._get_client", return_value=mock_client):
        service.upload_json("some/path.json", {"a": 1})

    call_kwargs = mock_client.put_object.call_args.kwargs
    assert call_kwargs.get("ContentType") == "application/json"


def test_upload_json_serializes_data():
    """upload_json encodes the data dict as JSON bytes."""
    service = StorageService()
    mock_client = MagicMock()
    data = {"score": 0.42, "brand": "Optivio"}

    with patch("app.core.storage._get_client", return_value=mock_client):
        service.upload_json("path.json", data)

    body_bytes = mock_client.put_object.call_args.kwargs["Body"]
    assert json.loads(body_bytes.decode("utf-8")) == data


def test_upload_json_raises_on_client_error():
    """upload_json re-raises ClientError from boto3."""
    service = StorageService()
    mock_client = MagicMock()
    mock_client.put_object.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Forbidden"}}, "PutObject"
    )

    with patch("app.core.storage._get_client", return_value=mock_client):
        with pytest.raises(ClientError):
            service.upload_json("path.json", {})


# ---------------------------------------------------------------------------
# download_json
# ---------------------------------------------------------------------------

def test_download_json_returns_parsed_data_on_success():
    """download_json deserializes the response body on a successful get."""
    service = StorageService()
    mock_client = MagicMock()
    payload = {"visibility_score": 0.55, "industry": "SaaS"}
    mock_client.get_object.return_value = {
        "Body": BytesIO(json.dumps(payload).encode("utf-8"))
    }

    with patch("app.core.storage._get_client", return_value=mock_client):
        result = service.download_json("projects/proj-1/ai/data.json")

    assert result == payload


def test_download_json_returns_empty_dict_on_no_such_key():
    """download_json returns {} when the key does not exist (NoSuchKey)."""
    service = StorageService()
    mock_client = MagicMock()
    mock_client.get_object.side_effect = _make_no_such_key_error()

    with patch("app.core.storage._get_client", return_value=mock_client):
        result = service.download_json("missing/key.json")

    assert result == {}


def test_download_json_returns_empty_dict_on_404():
    """download_json returns {} when the key is missing (404 code)."""
    service = StorageService()
    mock_client = MagicMock()
    mock_client.get_object.side_effect = _make_404_error()

    with patch("app.core.storage._get_client", return_value=mock_client):
        result = service.download_json("missing/key.json")

    assert result == {}


def test_download_json_raises_on_other_client_error():
    """download_json re-raises unexpected ClientErrors."""
    service = StorageService()
    mock_client = MagicMock()
    mock_client.get_object.side_effect = ClientError(
        {"Error": {"Code": "InternalError", "Message": "Server error"}}, "GetObject"
    )

    with patch("app.core.storage._get_client", return_value=mock_client):
        with pytest.raises(ClientError):
            service.download_json("some/path.json")


# ---------------------------------------------------------------------------
# upload_file
# ---------------------------------------------------------------------------

def test_upload_file_calls_put_object():
    """upload_file calls put_object with the raw bytes."""
    service = StorageService()
    mock_client = MagicMock()
    content = b"binary content here"

    with patch("app.core.storage._get_client", return_value=mock_client):
        url = service.upload_file("projects/proj-1/exports/report.pdf", content)

    mock_client.put_object.assert_called_once()
    call_kwargs = mock_client.put_object.call_args.kwargs
    assert call_kwargs["Body"] == content
    assert "projects/proj-1/exports/report.pdf" in url


def test_upload_file_returns_url_with_path():
    """upload_file return value contains the object path."""
    service = StorageService()
    mock_client = MagicMock()

    with patch("app.core.storage._get_client", return_value=mock_client):
        url = service.upload_file("projects/p/exports/file.csv", b"data")

    assert "projects/p/exports/file.csv" in url


# ---------------------------------------------------------------------------
# Path builders
# ---------------------------------------------------------------------------

def test_ai_path_format():
    """ai_path returns correctly formatted storage path."""
    assert StorageService.ai_path("proj-1", "scan.json") == "projects/proj-1/ai/scan.json"


def test_seo_path_format():
    """seo_path returns correctly formatted storage path."""
    assert StorageService.seo_path("proj-1", "audit.json") == "projects/proj-1/seo/audit.json"


def test_gsc_path_format():
    """gsc_path returns correctly formatted storage path."""
    assert StorageService.gsc_path("proj-1", "gsc.json") == "projects/proj-1/gsc/gsc.json"


def test_ads_path_format():
    """ads_path returns correctly formatted storage path."""
    assert StorageService.ads_path("proj-1", "ads.json") == "projects/proj-1/ads/ads.json"


def test_exports_path_format():
    """exports_path returns correctly formatted storage path."""
    assert (
        StorageService.exports_path("proj-1", "report.pdf")
        == "projects/proj-1/exports/report.pdf"
    )


def test_path_builders_include_project_id():
    """All path builders embed the project_id in the result."""
    pid = "abc-123"
    for builder in [
        StorageService.ai_path,
        StorageService.seo_path,
        StorageService.gsc_path,
        StorageService.ads_path,
        StorageService.exports_path,
    ]:
        path = builder(pid, "file.json")
        assert pid in path
