from abc import ABC, abstractmethod
from typing import List

from .models import ProviderResult


class HighResolutionProvider(ABC):
    name = "high_resolution"

    @abstractmethod
    def acquire_pair(self, location_name: str, bbox: List[float], before_date: str, after_date: str, output_dir) -> ProviderResult:
        raise NotImplementedError
