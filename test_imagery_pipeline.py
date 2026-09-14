import io
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.config import get_sh_config
from backend.imagery.acquisition_service import ImageryAcquisitionService
from backend.imagery.cache import ImageryCache
from backend.imagery.copernicus_provider import CopernicusProvider
from backend.imagery.maxar_provider import MaxarProvider
from backend.imagery.models import ImageryAsset, ProviderResult
from backend.imagery.wayback_provider import WaybackProvider
from backend.main import app, imagery_service


def get_real_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="blue").save(buf, format="PNG")
    return buf.getvalue()


def test_copernicus_credentials_missing(monkeypatch):
    monkeypatch.setenv("SH_CLIENT_ID", "")
    monkeypatch.setenv("SH_CLIENT_SECRET", "")
    provider = CopernicusProvider()
    result = provider.acquire_pair([79.0, 21.0, 79.1, 21.1], "2022-02-22", "2025-02-26")
    assert result.status == "unavailable"
    assert "credentials missing" in result.reason.lower()


def test_copernicus_authentication_failed(monkeypatch):
    monkeypatch.setenv("SH_CLIENT_ID", "dummy_id")
    monkeypatch.setenv("SH_CLIENT_SECRET", "dummy_secret")

    with patch("httpx.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_post.return_value = mock_resp

        provider = CopernicusProvider()
        result = provider.acquire_pair([79.0, 21.0, 79.1, 21.1], "2022-02-22", "2025-02-26")
        assert result.status == "unavailable"
        assert "authentication failed" in result.reason.lower()


def test_copernicus_no_scenes(monkeypatch):
    monkeypatch.setenv("SH_CLIENT_ID", "dummy_id")
    monkeypatch.setenv("SH_CLIENT_SECRET", "dummy_secret")

    with patch.object(CopernicusProvider, "_token", return_value="fake_token"):
        with patch("backend.imagery.copernicus_provider.get_available_scene_dates", return_value=[]):
            provider = CopernicusProvider()
            result = provider.acquire_pair([79.0, 21.0, 79.1, 21.1], "2022-02-22", "2025-02-26")
            assert result.status == "unavailable"
            assert "no suitable scene" in result.reason.lower()


def test_cache_location_isolation(tmp_path):
    cache = ImageryCache(tmp_path)
    loc_id1 = cache.location_id("Itwari", 21.1458, 79.0882)
    loc_id2 = cache.location_id("Itwari", 21.1500, 79.0900)
    assert loc_id1 != loc_id2
    assert "itwari" in loc_id1


def test_cache_manifest_and_assets(tmp_path):
    cache = ImageryCache(tmp_path)
    asset = ImageryAsset(
        provider="copernicus",
        sensor="Sentinel-2 L2A",
        resolution_m=10.0,
        acquisition_date="2022-02-22",
        bbox=[79.0, 21.0, 79.1, 21.1],
        local_path="",
        role="before"
    )
    png_data = get_real_png_bytes()
    saved = cache.save_asset("Itwari", 21.1458, 79.0882, asset, png_data)
    assert os.path.exists(saved.local_path)

    manifest_path = cache.save_manifest("Itwari", 21.1458, 79.0882, [79.0, 21.0, 79.1, 21.1], [saved], status="ready")
    assert manifest_path.is_file()

    cached = cache.get_cached_assets("Itwari", 21.1458, 79.0882)
    assert len(cached) == 1
    assert cached[0].provider == "copernicus"


def test_maxar_provider_unconfigured(tmp_path, monkeypatch):
    monkeypatch.delenv("MAXAR_API_KEY", raising=False)
    monkeypatch.delenv("MAXAR_CLIENT_ID", raising=False)
    monkeypatch.delenv("MAXAR_CLIENT_SECRET", raising=False)

    maxar = MaxarProvider()
    result = maxar.acquire_pair("Itwari", [79.0, 21.0, 79.1, 21.1], "2022-02-22", "2025-02-26", tmp_path)
    assert result.status == "unavailable"
    assert result.reason == "credentials_not_configured"


def test_acquisition_service_copernicus_success_highres_fail(tmp_path):
    mock_copernicus = MagicMock()
    png_data = get_real_png_bytes()
    asset_before = ImageryAsset(
        provider="copernicus",
        sensor="Sentinel-2 L2A",
        resolution_m=10.0,
        acquisition_date="2022-02-22",
        bbox=[79.0, 21.0, 79.1, 21.1],
        local_path="",
        role="before",
        raw_bytes=png_data
    )
    asset_after = ImageryAsset(
        provider="copernicus",
        sensor="Sentinel-2 L2A",
        resolution_m=10.0,
        acquisition_date="2025-02-26",
        bbox=[79.0, 21.0, 79.1, 21.1],
        local_path="",
        role="after",
        raw_bytes=png_data
    )
    mock_copernicus.acquire_pair.return_value = ProviderResult(
        provider="copernicus", status="available", assets=[asset_before, asset_after]
    )

    mock_maxar = MagicMock()
    mock_maxar.acquire_pair.return_value = ProviderResult(provider="maxar", status="unavailable", reason="credentials_not_configured")

    mock_wayback = MagicMock()
    mock_wayback.acquire_pair.return_value = ProviderResult(provider="arcgis_wayback", status="unavailable", reason="no_wayback_coverage")

    service = ImageryAcquisitionService(tmp_path, copernicus=mock_copernicus, highres_providers=[mock_maxar, mock_wayback])

    res = service.acquire_imagery(21.1458, 79.0882, [79.0, 21.0, 79.1, 21.1], "Itwari AOI", "2022-02-22", "2025-02-26")

    assert res.success is True
    assert res.ready_for_analysis is True
    assert len(res.assets) == 2


def test_api_acquire_imagery_endpoint():
    client = TestClient(app)
    with patch("backend.main.geocode_location", return_value=(21.1458, 79.0882, "Itwari Test AOI")):
        with patch.object(imagery_service, "acquire_imagery") as mock_acq:
            mock_acq.return_value = MagicMock(
                public_dict=lambda: {
                    "success": True,
                    "cache_hit": False,
                    "ready_for_analysis": True,
                    "providers": {"copernicus": {"status": "available"}},
                    "assets": []
                }
            )
            response = client.post("/api/acquire-imagery", json={
                "location_name": "Itwari Test AOI",
                "lat": 21.1458,
                "lng": 79.0882,
                "before_date": "2022-02-22",
                "after_date": "2025-02-26"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["ready_for_analysis"] is True


def test_api_imagery_status_endpoint():
    client = TestClient(app)
    with patch("backend.main.geocode_location", return_value=(21.1458, 79.0882, "Itwari Test AOI")):
        with patch.object(imagery_service, "imagery_status", return_value={
            "metadata_indexed": True,
            "sentinel2": {"status": "available", "before": True, "after": True},
            "high_resolution": {"status": "available", "before": True, "after": True},
            "ready_for_analysis": True
        }):
            response = client.get("/api/imagery-status", params={
                "location_name": "Itwari Test AOI",
                "lat": 21.1458,
                "lng": 79.0882
            })
            assert response.status_code == 200
            data = response.json()
            assert data["metadata_indexed"] is True
            assert data["sentinel2"]["status"] == "available"
            assert data["ready_for_analysis"] is True
