import os
from typing import List

from .highres_provider import HighResolutionProvider
from .models import ProviderResult


class MaxarProvider(HighResolutionProvider):
    name = "maxar"

    def acquire_pair(self, location_name: str, bbox: List[float], before_date: str, after_date: str, output_dir) -> ProviderResult:
        configured = any(os.environ.get(key, "").strip() for key in ("MAXAR_API_KEY", "MAXAR_CLIENT_ID", "MAXAR_CLIENT_SECRET"))
        if not configured:
            return ProviderResult(provider=self.name, status="unavailable", reason="credentials_not_configured")
        return ProviderResult(provider=self.name, status="unavailable", reason="provider_adapter_not_configured")
