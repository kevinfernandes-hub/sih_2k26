def determine_analysis_mode(query: str) -> str:
    """
    Route a natural language query to the appropriate analysis engine mode.
    Maps to specific change algorithms required by the final product.
    """
    query_lower = query.lower()
    
    # Vegetation keywords
    if any(kw in query_lower for kw in ["vegetation", "deforestation", "forest", "tree", "clearance", "clearing"]):
        return "vegetation_change"
        
    # Water keywords
    if any(kw in query_lower for kw in ["water", "lake", "river", "pond", "reservoir", "drying"]):
        return "water_change"
        
    # Infrastructure keywords
    if any(kw in query_lower for kw in ["road", "highway", "bridge", "infrastructure"]):
        return "infrastructure_change"
        
    # Default to built-up change for urban/construction keywords
    return "built_up_change"

def extract_primary_modality(mode: str) -> str:
    """Return the primary spectral index or methodology used for the mode."""
    if mode == "vegetation_change":
        return "NDVI"
    if mode == "water_change":
        return "NDWI"
    return "Optical Difference"
