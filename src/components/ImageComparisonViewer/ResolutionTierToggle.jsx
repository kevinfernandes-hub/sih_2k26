import React from 'react';
import styles from './ImageComparisonViewer.module.css';

export function ResolutionTierToggle({ selectedTier = '10m', onTierChange, hasHighRes, hasHighResTier }) {
  const isHighResAvailable = Boolean(hasHighRes ?? hasHighResTier ?? true);

  return (
    <div className={styles.tierSegmentedControl} role="group" aria-label="Resolution Tier Toggle">
      <button
        type="button"
        className={`${styles.tierSegmentBtn} ${selectedTier === '10m' ? styles.tierActive : ''}`}
        onClick={() => onTierChange && onTierChange('10m')}
        title="10m spatial resolution from Copernicus Sentinel-2 (Multispectral L2A)"
      >
        <span className={styles.tierBadge}>10m</span>
        <span>Sentinel-2</span>
      </button>

      <button
        type="button"
        className={`${styles.tierSegmentBtn} ${selectedTier === '0.6m' ? styles.tierActive : ''} ${
          !isHighResAvailable ? styles.tierDisabled : ''
        }`}
        onClick={() => onTierChange && onTierChange('0.6m')}
        title="0.6m sub-meter optical resolution from High-Res Archive"
      >
        <span className={`${styles.tierBadge} ${isHighResAvailable ? styles.badgeHighRes : ''}`}>0.6m</span>
        <span>High-Res (~0.6m)</span>
        {!isHighResAvailable && <span className={styles.lockIcon}>🔒</span>}
      </button>
    </div>
  );
}

export default ResolutionTierToggle;
