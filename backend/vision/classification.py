"""
Structured Change Taxonomy & Multi-Type Classification Engine
Nagpur EarthWatch — Multimodal Urban & Environmental Change Intelligence

Defines standard change typologies across two major domains:
1. Urban / Infrastructure Change
2. Environmental / Land-Cover Change
"""

from typing import Dict, List, Any, Optional, NamedTuple
from enum import Enum


class ChangeDomain(str, Enum):
    INFRASTRUCTURE = "INFRASTRUCTURE"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    OTHER = "OTHER"


class ChangeType(str, Enum):
    # Infrastructure
    NEW_CONSTRUCTION = "NEW_CONSTRUCTION"
    BUILDING_EXPANSION = "BUILDING_EXPANSION"
    DEMOLITION = "DEMOLITION"
    ROAD_CONSTRUCTION = "ROAD_CONSTRUCTION"
    ROAD_WIDENING = "ROAD_WIDENING"
    PAVED_AREA_EXPANSION = "PAVED_AREA_EXPANSION"
    INDUSTRIAL_EXPANSION = "INDUSTRIAL_EXPANSION"
    EXCAVATION = "EXCAVATION"
    LAND_DEVELOPMENT = "LAND_DEVELOPMENT"

    # Environmental
    VEGETATION_LOSS = "VEGETATION_LOSS"
    VEGETATION_GAIN = "VEGETATION_GAIN"
    TREE_COVER_CHANGE = "TREE_COVER_CHANGE"
    LAND_CLEARING = "LAND_CLEARING"
    WATERBODY_CHANGE = "WATERBODY_CHANGE"
    WATERBODY_REDUCTION = "WATERBODY_REDUCTION"
    WATERBODY_EXPANSION = "WATERBODY_EXPANSION"
    OPEN_SPACE_CONVERSION = "OPEN_SPACE_CONVERSION"
    AGRICULTURAL_CHANGE = "AGRICULTURAL_CHANGE"
    SURFACE_DISTURBANCE = "SURFACE_DISTURBANCE"

    # Other / Fallback
    OTHER = "OTHER"
    UNCERTAIN = "UNCERTAIN"
    NO_SIGNIFICANT_CHANGE = "NO_SIGNIFICANT_CHANGE"


CHANGE_TYPE_METADATA: Dict[str, Dict[str, Any]] = {
    ChangeType.NEW_CONSTRUCTION.value: {
        "domain": ChangeDomain.INFRASTRUCTURE.value,
        "label": "New Construction",
        "description": "Appearance of new building foundations, structural envelopes, or completed roof structures.",
        "default_priority": "CRITICAL"
    },
    ChangeType.BUILDING_EXPANSION.value: {
        "domain": ChangeDomain.INFRASTRUCTURE.value,
        "label": "Building Expansion",
        "description": "Lateral footprint expansion, additional wings, or structural enlargement of existing buildings.",
        "default_priority": "HIGH"
    },
    ChangeType.DEMOLITION.value: {
        "domain": ChangeDomain.INFRASTRUCTURE.value,
        "label": "Demolition / Clearance",
        "description": "Removal or structural dismantling of previous buildings or infrastructure.",
        "default_priority": "HIGH"
    },
    ChangeType.ROAD_CONSTRUCTION.value: {
        "domain": ChangeDomain.INFRASTRUCTURE.value,
        "label": "Road Construction",
        "description": "Formation of new paved arterial roads, asphalt corridors, or access streets.",
        "default_priority": "HIGH"
    },
    ChangeType.ROAD_WIDENING.value: {
        "domain": ChangeDomain.INFRASTRUCTURE.value,
        "label": "Road Widening",
        "description": "Lateral expansion of road right-of-way, additional lanes, or median adjustments.",
        "default_priority": "MEDIUM"
    },
    ChangeType.PAVED_AREA_EXPANSION.value: {
        "domain": ChangeDomain.INFRASTRUCTURE.value,
        "label": "Paved Area Expansion",
        "description": "Expansion of concrete aprons, parking plazas, loading docks, or hardstanding surfaces.",
        "default_priority": "MEDIUM"
    },
    ChangeType.INDUSTRIAL_EXPANSION.value: {
        "domain": ChangeDomain.INFRASTRUCTURE.value,
        "label": "Industrial Expansion",
        "description": "Large-span industrial sheds, factory complexes, warehouses, or processing yards.",
        "default_priority": "CRITICAL"
    },
    ChangeType.EXCAVATION.value: {
        "domain": ChangeDomain.INFRASTRUCTURE.value,
        "label": "Excavation / Earthwork",
        "description": "Significant ground levelling, basement excavation, quarrying, or earth-moving operations.",
        "default_priority": "HIGH"
    },
    ChangeType.LAND_DEVELOPMENT.value: {
        "domain": ChangeDomain.INFRASTRUCTURE.value,
        "label": "Land Development",
        "description": "Conversion of natural or open land into structured development parcels with plot demarcation.",
        "default_priority": "HIGH"
    },
    ChangeType.VEGETATION_LOSS.value: {
        "domain": ChangeDomain.ENVIRONMENTAL.value,
        "label": "Vegetation Loss",
        "description": "Significant reduction in biomass, shrub cover, or green canopy.",
        "default_priority": "HIGH"
    },
    ChangeType.VEGETATION_GAIN.value: {
        "domain": ChangeDomain.ENVIRONMENTAL.value,
        "label": "Vegetation Gain",
        "description": "Regrowth, plantation, or increased green cover over open terrain.",
        "default_priority": "LOW"
    },
    ChangeType.TREE_COVER_CHANGE.value: {
        "domain": ChangeDomain.ENVIRONMENTAL.value,
        "label": "Tree Cover Reduction",
        "description": "Canopy removal or felling of mature tree clusters in urban corridors.",
        "default_priority": "HIGH"
    },
    ChangeType.LAND_CLEARING.value: {
        "domain": ChangeDomain.ENVIRONMENTAL.value,
        "label": "Land Clearing",
        "description": "Clearing of natural open space, topsoil scraping, or preparation for development.",
        "default_priority": "HIGH"
    },
    ChangeType.WATERBODY_CHANGE.value: {
        "domain": ChangeDomain.ENVIRONMENTAL.value,
        "label": "Waterbody Alteration",
        "description": "Noticeable morphological shift in pond, lake, or drainage channel boundaries.",
        "default_priority": "CRITICAL"
    },
    ChangeType.WATERBODY_REDUCTION.value: {
        "domain": ChangeDomain.ENVIRONMENTAL.value,
        "label": "Waterbody Reduction / Encroachment",
        "description": "Shrinkage or possible unapproved filling/encroachment of seasonal water retention zones.",
        "default_priority": "CRITICAL"
    },
    ChangeType.WATERBODY_EXPANSION.value: {
        "domain": ChangeDomain.ENVIRONMENTAL.value,
        "label": "Waterbody Expansion",
        "description": "Increased surface water retention or reservoir expansion.",
        "default_priority": "MEDIUM"
    },
    ChangeType.OPEN_SPACE_CONVERSION.value: {
        "domain": ChangeDomain.ENVIRONMENTAL.value,
        "label": "Open Space Conversion",
        "description": "Conversion of municipal green belts, open parks, or commons into built land.",
        "default_priority": "CRITICAL"
    },
    ChangeType.AGRICULTURAL_CHANGE.value: {
        "domain": ChangeDomain.ENVIRONMENTAL.value,
        "label": "Agricultural Conversion",
        "description": "Transformation of cultivable agricultural land to non-agricultural urban use.",
        "default_priority": "HIGH"
    },
    ChangeType.SURFACE_DISTURBANCE.value: {
        "domain": ChangeDomain.ENVIRONMENTAL.value,
        "label": "Surface Disturbance",
        "description": "Unclassified soil or optical disturbance requiring field confirmation.",
        "default_priority": "MEDIUM"
    },
    ChangeType.UNCERTAIN.value: {
        "domain": ChangeDomain.OTHER.value,
        "label": "Uncertain Evidence",
        "description": "Optical changes attributable to shadows, acquisition angles, or atmospheric variations.",
        "default_priority": "MEDIUM"
    },
    ChangeType.NO_SIGNIFICANT_CHANGE.value: {
        "domain": ChangeDomain.OTHER.value,
        "label": "No Significant Change",
        "description": "Surface texture and structural features remain stable across time baseline.",
        "default_priority": "LOW"
    }
}


def get_change_type_info(type_name: str) -> Dict[str, Any]:
    """Returns standardized metadata for a change type string."""
    clean_name = type_name.strip().upper().replace(" ", "_")
    return CHANGE_TYPE_METADATA.get(
        clean_name,
        {
            "domain": ChangeDomain.OTHER.value,
            "label": type_name.replace("_", " ").title(),
            "description": "Unclassified spatial change.",
            "default_priority": "MEDIUM"
        }
    )
