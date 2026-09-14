from datetime import date
from pathlib import Path
from typing import List

from PIL import Image

from backend.wayback_live import fetch_live_wayback_tier

from .highres_provider import HighResolutionProvider
from .models import ImageryAsset, ProviderResult


class WaybackProvider(HighResolutionProvider):
    name = "arcgis_wayback"

    def acquire_pair(self, location_name: str, bbox: List[float], before_date: str, after_date: str, output_dir: Path) -> ProviderResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            result = fetch_live_wayback_tier(
                bbox=bbox,
                output_dir=output_dir,
                base_url="",
                before_target=before_date,
                after_target=after_date,
                zoom=17,
            )
            if not result:
                return ProviderResult(provider=self.name, status="unavailable", reason="no_wayback_coverage")
            assets = []
            for role, filename, scene_date in (("before", "wayback_before.png", result.get("beforeDate", before_date)), ("after", "wayback_after.png", result.get("afterDate", after_date))):
                path = output_dir / filename
                if not path.is_file():
                    continue
                with Image.open(path) as image:
                    width, height = image.size
                assets.append(ImageryAsset(
                    provider=self.name,
                    sensor="ArcGIS World Imagery Wayback",
                    resolution_m=0.6,
                    acquisition_date=date.fromisoformat(scene_date[:10]),
                    bbox=bbox,
                    local_path=str(path),
                    width=width,
                    height=height,
                    role=role,
                ))
            if len(assets) != 2:
                return ProviderResult(provider=self.name, status="partial" if assets else "unavailable", assets=assets, reason="incomplete_wayback_pair")
            return ProviderResult(provider=self.name, status="available", assets=assets)
        except Exception:
            return ProviderResult(provider=self.name, status="unavailable", reason="wayback_request_failed")
