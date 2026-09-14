import io
import logging
from datetime import date, datetime
from typing import List, Optional, Tuple

import httpx
from PIL import Image
from sentinelhub import BBox, CRS

from backend.config import get_sh_config
from backend.pipeline import fetch_satellite_image, get_available_scene_dates

from .models import ImageryAsset, ProviderResult

LOGGER = logging.getLogger(__name__)
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"


class CopernicusProvider:
    name = "copernicus"

    def __init__(self, timeout: Tuple[float, float] = (15.0, 60.0)):
        self.timeout = timeout

    def _token(self) -> Optional[str]:
        config = get_sh_config()
        if not config.sh_client_id or not config.sh_client_secret:
            return None
        try:
            response = httpx.post(
                TOKEN_URL,
                data={"grant_type": "client_credentials", "client_id": config.sh_client_id, "client_secret": config.sh_client_secret},
                timeout=self.timeout,
            )
            if response.status_code != 200:
                LOGGER.warning("[COPERNICUS] Authentication failed with status %s", response.status_code)
                return None
            return response.json().get("access_token")
        except httpx.HTTPError as exc:
            LOGGER.warning("[COPERNICUS] Authentication request failed: %s", type(exc).__name__)
            return None

    @staticmethod
    def _closest_date(rows: List[dict], requested: str) -> Optional[dict]:
        if not rows:
            return None
        target = date.fromisoformat(requested[:10])
        usable = [row for row in rows if row.get("usable", True)] or rows
        return min(usable, key=lambda row: abs(date.fromisoformat(row["date"]) - target))

    def acquire_pair(self, bbox: List[float], before_date: str, after_date: str) -> ProviderResult:
        config = get_sh_config()
        if not config.sh_client_id or not config.sh_client_secret:
            LOGGER.warning("[COPERNICUS] Credentials missing")
            return ProviderResult(provider=self.name, status="unavailable", reason="Copernicus credentials missing")

        token = self._token()
        if not token:
            LOGGER.warning("[COPERNICUS] Authentication failed")
            return ProviderResult(provider=self.name, status="unavailable", reason="Copernicus authentication failed")

        try:
            LOGGER.info("[COPERNICUS] Searching scenes")
            box = BBox(tuple(bbox), crs=CRS.WGS84)
            scenes = get_available_scene_dates(config=config, bbox=box, start_date="2020-01-01", end_date="2030-01-01")
            before_scene = self._closest_date(scenes, before_date)
            after_scene = self._closest_date(scenes, after_date)
            if not before_scene or not after_scene:
                LOGGER.warning("[COPERNICUS] No suitable scene found")
                return ProviderResult(provider=self.name, status="unavailable", reason="Copernicus returned no suitable scene")

            LOGGER.info("[COPERNICUS] Before scene: %s", before_scene["date"])
            LOGGER.info("[COPERNICUS] After scene: %s", after_scene["date"])

            assets: List[ImageryAsset] = []
            for role, scene in (("before", before_scene), ("after", after_scene)):
                scene_date = scene["date"]
                LOGGER.info("[COPERNICUS] Downloading %s image (%s)", role, scene_date)
                image = fetch_satellite_image(
                    (f"{scene_date}T00:00:00Z", f"{scene_date}T23:59:59Z"),
                    box,
                    (600, 500),
                    config,
                )
                buffer = io.BytesIO()
                Image.fromarray(image).save(buffer, format="PNG")
                assets.append(ImageryAsset(
                    provider=self.name,
                    sensor="Sentinel-2 L2A",
                    resolution_m=10.0,
                    acquisition_date=date.fromisoformat(scene_date),
                    bbox=bbox,
                    local_path="",
                    cloud_cover=scene.get("cloud_cover"),
                    role=role,
                ).model_copy(update={"raw_bytes": buffer.getvalue()}))
            LOGGER.info("[COPERNICUS] Assets saved")
            return ProviderResult(provider=self.name, status="available", assets=assets)
        except Exception as exc:
            LOGGER.warning("[COPERNICUS] Imagery request failed: %s", type(exc).__name__)
            return ProviderResult(provider=self.name, status="unavailable", reason="Copernicus imagery request failed")
