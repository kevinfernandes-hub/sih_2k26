import logging
from pathlib import Path
from typing import Dict, List, Optional

from .cache import ImageryCache
from .copernicus_provider import CopernicusProvider
from .maxar_provider import MaxarProvider
from .models import AcquisitionResult, ImageryAsset, ProviderResult
from .wayback_provider import WaybackProvider

LOGGER = logging.getLogger(__name__)


class ImageryAcquisitionService:
    def __init__(self, data_dir: Path, copernicus=None, highres_providers=None):
        self.cache = ImageryCache(Path(data_dir) / "acquired")
        self.copernicus = copernicus or CopernicusProvider()
        self.highres_providers = highres_providers or [MaxarProvider(), WaybackProvider()]

    def acquire_imagery(self, lat: float, lng: float, bbox: List[float], location_name: str, before_date: str, after_date: str, providers: Optional[List[str]] = None) -> AcquisitionResult:
        location = {"name": location_name, "lat": lat, "lng": lng, "bbox": bbox}
        cached = self.cache.get_cached_assets(location_name, lat, lng)
        pair = self.cache.get_pair(location_name, lat, lng, before_date, after_date)
        if pair.valid:
            return AcquisitionResult(success=True, location=location, providers_attempted=["cache"], assets=cached, cache_hit=True, ready_for_analysis=True)

        LOGGER.info("[IMAGERY] Request started for %s", location_name)
        assets: List[ImageryAsset] = list(cached)
        provider_results: Dict[str, ProviderResult] = {}
        errors: List[str] = []

        if not any(asset.provider == "copernicus" and asset.role == "before" for asset in assets) or not any(asset.provider == "copernicus" and asset.role == "after" for asset in assets):
            LOGGER.info("[COPERNICUS] Searching scenes")
            copernicus_result = self.copernicus.acquire_pair(bbox, before_date, after_date)
            provider_results[copernicus_result.provider] = copernicus_result
            if copernicus_result.status == "available":
                for asset in copernicus_result.assets:
                    if asset.raw_bytes is not None:
                        assets.append(self.cache.save_asset(location_name, lat, lng, asset, asset.raw_bytes))
            elif copernicus_result.reason:
                errors.append(f"Copernicus: {copernicus_result.reason}")

        highres_dir = self.cache.location_dir(location_name, lat, lng) / "highres"
        if not any(asset.provider == "arcgis_wayback" and asset.role == "before" for asset in assets) or not any(asset.provider == "arcgis_wayback" and asset.role == "after" for asset in assets):
            for provider in self.highres_providers:
                result = provider.acquire_pair(location_name, bbox, before_date, after_date, highres_dir)
                provider_results[result.provider] = result
                if result.status in {"available", "partial"}:
                    assets.extend(result.assets)
                if result.status == "available":
                    break
                if result.reason:
                    errors.append(f"{result.provider}: {result.reason}")

        sentinel_before = any(asset.provider == "copernicus" and asset.role == "before" for asset in assets)
        sentinel_after = any(asset.provider == "copernicus" and asset.role == "after" for asset in assets)
        highres_before = any(asset.provider in {"arcgis_wayback", "maxar"} and asset.role == "before" for asset in assets)
        highres_after = any(asset.provider in {"arcgis_wayback", "maxar"} and asset.role == "after" for asset in assets)
        ready = (sentinel_before and sentinel_after) or (highres_before and highres_after)
        self.cache.save_manifest(location_name, lat, lng, bbox, assets, status="ready" if ready else "failed")
        return AcquisitionResult(
            success=ready,
            location=location,
            providers_attempted=["copernicus", "maxar", "arcgis_wayback"],
            providers=provider_results,
            assets=assets,
            errors=errors,
            ready_for_analysis=ready,
        )

    def imagery_status(self, lat: float, lng: float, location_name: str, before_date: str, after_date: str) -> Dict:
        return self.cache.get_imagery_status(location_name, lat, lng, before_date, after_date)
