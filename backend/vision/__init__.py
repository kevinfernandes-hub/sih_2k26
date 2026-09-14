"""
Nagpur EarthWatch — Multimodal Vision Subsystem
"""

from .classification import ChangeDomain, ChangeType, get_change_type_info
from .alignment import verify_and_align_geographic_footprints, AlignmentResult
from .segmentation import segment_change_polygons, calculate_polygon_area_m2, pixel_to_wgs84
from .change_model import (
    ChangeVisionModel,
    HeuristicMultimodalVisionModel,
    MultimodalChangeResult,
    get_default_vision_model
)
from .evidence import fuse_multi_source_evidence

__all__ = [
    "ChangeDomain",
    "ChangeType",
    "get_change_type_info",
    "verify_and_align_geographic_footprints",
    "AlignmentResult",
    "segment_change_polygons",
    "calculate_polygon_area_m2",
    "pixel_to_wgs84",
    "ChangeVisionModel",
    "HeuristicMultimodalVisionModel",
    "MultimodalChangeResult",
    "get_default_vision_model",
    "fuse_multi_source_evidence",
]
