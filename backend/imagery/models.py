from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ImageryAsset(BaseModel):
    provider: str
    sensor: str
    resolution_m: float
    acquisition_date: date
    bbox: List[float]
    local_path: str
    width: int = 0
    height: int = 0
    cloud_cover: Optional[float] = None
    available: bool = True
    role: str = ""
    raw_bytes: Optional[bytes] = Field(default=None, exclude=True)


class ImageryPair(BaseModel):
    before: Optional[ImageryAsset] = None
    after: Optional[ImageryAsset] = None
    provider: str = ""
    resolution_m: float = 0.0
    valid: bool = False


class ProviderResult(BaseModel):
    provider: str
    status: str
    assets: List[ImageryAsset] = Field(default_factory=list)
    reason: Optional[str] = None


class AcquisitionResult(BaseModel):
    success: bool
    location: Dict[str, Any]
    providers_attempted: List[str] = Field(default_factory=list)
    providers: Dict[str, ProviderResult] = Field(default_factory=dict)
    assets: List[ImageryAsset] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    cache_hit: bool = False
    ready_for_analysis: bool = False

    def public_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")
