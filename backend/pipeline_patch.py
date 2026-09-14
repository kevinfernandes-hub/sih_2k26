import cv2
import numpy as np
from typing import Tuple

def compute_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """ Computes Normalized Difference Water Index (NDWI) """
    green_f = green.astype(np.float32)
    nir_f = nir.astype(np.float32)
    # Avoid division by zero
    denominator = (green_f + nir_f)
    denominator[denominator == 0] = 1e-6
    ndwi = (green_f - nir_f) / denominator
    return ndwi

def compute_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """ Computes Normalized Difference Vegetation Index (NDVI) """
    red_f = red.astype(np.float32)
    nir_f = nir.astype(np.float32)
    denominator = (nir_f + red_f)
    denominator[denominator == 0] = 1e-6
    ndvi = (nir_f - red_f) / denominator
    return ndvi

def extract_water_mask(ndwi: np.ndarray, threshold: float = 0.0) -> np.ndarray:
    """ Creates binary mask of water bodies """
    mask = (ndwi > threshold).astype(np.uint8) * 255
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask

def extract_vegetation_mask(ndvi: np.ndarray, threshold: float = 0.2) -> np.ndarray:
    """ Creates binary mask of vegetation """
    mask = (ndvi > threshold).astype(np.uint8) * 255
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask
