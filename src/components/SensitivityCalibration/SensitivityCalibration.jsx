import React from 'react';
import { CalibrationSlider } from './CalibrationSlider';
import { interpolateSensitivity } from '../../data/calibration';
import styles from './SensitivityCalibration.module.css';

export function SensitivityCalibration({ threshold, onThresholdChange }) {
  const currentDelta = interpolateSensitivity(threshold).toFixed(2);

  return (
    <footer className={styles.bar} aria-label="Detection Sensitivity Controls">
      <div className={styles.labelGroup}>
        <span className={styles.title}>Detection Sensitivity</span>
        <span className={styles.subtitle}>Calibrated threshold standard (20.0 default)</span>
      </div>

      <div className={styles.sliderSection}>
        <CalibrationSlider threshold={threshold} onThresholdChange={onThresholdChange} />
      </div>

      <div className={`${styles.readoutGroup} tabular-nums`}>
        <div className={styles.readoutItem}>
          <span className={styles.readoutLabel}>Threshold</span>
          <span className={styles.readoutValue}>{threshold.toFixed(1)}</span>
        </div>
        <div className={styles.readoutItem}>
          <span className={styles.readoutLabel}>Calibrated Area Delta</span>
          <span className={styles.readoutValue} style={{ color: 'var(--accent-primary)' }}>
            {currentDelta}%
          </span>
        </div>
        <button
          type="button"
          className={styles.resetBtn}
          onClick={() => onThresholdChange(20.0)}
          title="Reset to 20.0 calibrated default"
        >
          Reset
        </button>
      </div>
    </footer>
  );
}
