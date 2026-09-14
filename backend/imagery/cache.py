import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from PIL import Image

from .models import ImageryAsset, ImageryPair


class ImageryCache:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def location_id(location_name: str, lat: float, lng: float) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", location_name.lower()).strip("-")
        digest = hashlib.sha256(f"{lat:.6f}:{lng:.6f}".encode()).hexdigest()[:10]
        return f"{normalized[:48] or 'aoi'}-{digest}"

    def location_dir(self, location_name: str, lat: float, lng: float) -> Path:
        return self.root / self.location_id(location_name, lat, lng)

    def manifest_path(self, location_name: str, lat: float, lng: float) -> Path:
        return self.location_dir(location_name, lat, lng) / "manifest.json"

    def _read_manifest(self, path: Path) -> Dict[str, Any]:
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return {}

    def get_cached_assets(self, location_name: str, lat: float, lng: float) -> List[ImageryAsset]:
        manifest = self._read_manifest(self.manifest_path(location_name, lat, lng))
        assets: List[ImageryAsset] = []
        for raw in manifest.get("assets", []):
            path = self.root / manifest.get("location_id", self.location_id(location_name, lat, lng)) / raw.get("path", "")
            if not path.is_file():
                continue
            try:
                assets.append(ImageryAsset(**{**raw, "local_path": str(path)}))
            except Exception:
                continue
        return assets

    def save_asset(self, location_name: str, lat: float, lng: float, asset: ImageryAsset, data: bytes) -> ImageryAsset:
        location_dir = self.location_dir(location_name, lat, lng)
        role_dir = location_dir / ("sentinel2" if asset.provider == "copernicus" else "highres")
        role_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{asset.role or 'scene'}_{asset.acquisition_date.isoformat()}.png"
        path = role_dir / filename
        
        # Write to temporary file
        temp_path = path.with_suffix('.tmp')
        temp_path.write_bytes(data)
        
        # Verify file size
        if temp_path.stat().st_size == 0:
            temp_path.unlink(missing_ok=True)
            raise ValueError("Downloaded image is empty (0 bytes).")
            
        try:
            with Image.open(temp_path) as image:
                image.verify()
            # Image.verify() closes the file. We must reopen to get size correctly if needed, 
            # though verify() often populates size. Reopening is safer.
            with Image.open(temp_path) as image:
                asset.width, asset.height = image.size
                if asset.width <= 0 or asset.height <= 0:
                    raise ValueError(f"Invalid image dimensions: {asset.width}x{asset.height}")
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            raise ValueError(f"Image validation failed: {str(e)}")
            
        # Atomic rename
        temp_path.replace(path)
        asset.local_path = str(path)
        return asset

    def save_manifest(self, location_name: str, lat: float, lng: float, bbox: List[float], assets: Iterable[ImageryAsset], status: str = "partial") -> Path:
        location_id = self.location_id(location_name, lat, lng)
        path = self.root / location_id / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = []
        for asset in assets:
            raw = asset.model_dump(mode="json")
            raw["path"] = str(Path(asset.local_path).relative_to(path.parent))
            raw.pop("local_path", None)
            serialized.append(raw)
        path.write_text(json.dumps({
            "location": location_name,
            "location_id": location_id,
            "lat": lat,
            "lng": lng,
            "bbox": bbox,
            "status": status,
            "assets": serialized,
        }, indent=2))
        return path

    def get_pair(self, location_name: str, lat: float, lng: float, before_date: str, after_date: str) -> ImageryPair:
        assets = self.get_cached_assets(location_name, lat, lng)
        before = next((a for a in assets if a.role == "before" and a.provider == "copernicus"), None)
        after = next((a for a in assets if a.role == "after" and a.provider == "copernicus"), None)
        if not (before and after):
            before = next((a for a in assets if a.role == "before" and a.provider in {"arcgis_wayback", "maxar"}), None)
            after = next((a for a in assets if a.role == "after" and a.provider in {"arcgis_wayback", "maxar"}), None)
            provider = before.provider if before else "arcgis_wayback"
            res = before.resolution_m if before else 0.6
        else:
            provider = "copernicus"
            res = 10.0
        return ImageryPair(before=before, after=after, provider=provider, resolution_m=res, valid=bool(before and after))

    def has_temporal_pair(self, location_name: str, lat: float, lng: float, before_date: str, after_date: str) -> bool:
        return self.get_pair(location_name, lat, lng, before_date, after_date).valid

    def invalidate_asset(self, location_name: str, lat: float, lng: float, provider: Optional[str] = None) -> bool:
        location_dir = self.location_dir(location_name, lat, lng)
        if not location_dir.exists():
            return False
        if provider:
            manifest_path = self.manifest_path(location_name, lat, lng)
            manifest = self._read_manifest(manifest_path)
            assets = manifest.get("assets", [])
            remaining = []
            for asset in assets:
                if asset.get("provider") == provider:
                    rel_path = asset.get("path", "")
                    file_path = location_dir / rel_path
                    if file_path.is_file():
                        file_path.unlink(missing_ok=True)
                else:
                    remaining.append(asset)
            manifest["assets"] = remaining
            manifest_path.write_text(json.dumps(manifest, indent=2))
        else:
            import shutil
            shutil.rmtree(location_dir, ignore_errors=True)
        return True

    def get_imagery_status(self, location_name: str, lat: float, lng: float, before_date: str, after_date: str) -> Dict[str, Any]:
        assets = self.get_cached_assets(location_name, lat, lng)
        sentinel = [a for a in assets if a.provider == "copernicus"]
        highres = [a for a in assets if a.provider in {"arcgis_wayback", "maxar"}]
        sentinel_before = any(a.role == "before" for a in sentinel)
        sentinel_after = any(a.role == "after" for a in sentinel)
        highres_before = any(a.role == "before" for a in highres)
        highres_after = any(a.role == "after" for a in highres)
        ready = (sentinel_before and sentinel_after) or (highres_before and highres_after)
        return {
            "metadata_indexed": True,
            "sentinel2": {"status": "available" if sentinel_before and sentinel_after else "partial" if sentinel else "not_staged", "before": sentinel_before, "after": sentinel_after},
            "high_resolution": {"status": "available" if highres_before and highres_after else "partial" if highres else "not_staged", "before": highres_before, "after": highres_after},
            "ready_for_analysis": ready,
            "assets": [a.model_dump(mode="json") for a in assets],
        }
