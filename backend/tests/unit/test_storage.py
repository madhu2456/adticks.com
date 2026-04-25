import json
from pathlib import Path
from unittest.mock import mock_open, patch

from app.core.storage import StorageService

def test_storage_service_init(monkeypatch):
    """Test StorageService initializes root directory."""
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        service = StorageService()
        assert service.root is not None
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

def test_upload_json():
    """Test upload_json serializes and writes data."""
    service = StorageService()
    service.root = Path("/tmp/mock_root")
    data = {"test": "data"}
    
    m_open = mock_open()
    with patch("builtins.open", m_open), \
         patch("pathlib.Path.mkdir"):
        url = service.upload_json("test_dir/test.json", data)
        
        m_open.assert_called_once()
        handle = m_open()
        handle.write.assert_called()
        # Verify URL is constructed correctly
        assert url.endswith("test_dir/test.json")

def test_download_json():
    """Test download_json reads and deserializes data."""
    service = StorageService()
    service.root = Path("/tmp/mock_root")
    data = {"test": "data"}
    
    m_open = mock_open(read_data=json.dumps(data))
    with patch("builtins.open", m_open), \
         patch("pathlib.Path.exists", return_value=True):
        result = service.download_json("test_dir/test.json")
        assert result == data

def test_download_json_not_found():
    """Test download_json returns empty dict if file doesn't exist."""
    service = StorageService()
    service.root = Path("/tmp/mock_root")
    
    with patch("pathlib.Path.exists", return_value=False):
        result = service.download_json("test_dir/test.json")
        assert result == {}
