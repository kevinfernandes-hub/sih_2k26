import React from 'react';
import styles from './ImageComparisonViewer.module.css';

export function ViewModeToggle({
  viewMode,
  currentMode,
  onModeChange,
  selectedTier = '10m',
  isHighRes = false
}) {
  const activeMode = viewMode || currentMode || 'raw';

  return (
    <div className={styles.segmentedControl} role="group" aria-label="View Mode Toggle">
      <button
        type="button"
        className={`${styles.segmentBtn} ${activeMode === 'raw' ? styles.active : ''}`}
        onClick={() => onModeChange && onModeChange('raw')}
        title="View split swipe slider of baseline and comparison imagery"
      >
        ↔️ Raw Split
      </button>

      <button
        type="button"
        className={`${styles.segmentBtn} ${activeMode === 'color' ? styles.active : ''}`}
        onClick={() => onModeChange && onModeChange('color')}
        title="Calibrated optical change overlay"
      >
        🟧 Optical Footprint
      </button>

      <button
        type="button"
        className={`${styles.segmentBtn} ${activeMode === 'ssim' ? styles.active : ''}`}
        onClick={() => onModeChange && onModeChange('ssim')}
        title="Structural Similarity Index (SSIM) matrix detecting structural alterations"
      >
        🔲 SSIM Matrix
      </button>

      <button
        type="button"
        className={`${styles.segmentBtn} ${activeMode === 'veg' ? styles.active : ''}`}
        onClick={() => onModeChange && onModeChange('veg')}
        title="Excess Green (ExG) canopy loss and increment overlay"
      >
        🌿 Vegetation Dynamics
      </button>
    </div>
  );
}

export default ViewModeToggle;
