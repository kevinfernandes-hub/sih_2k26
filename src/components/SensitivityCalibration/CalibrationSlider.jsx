import React from 'react';
import { calibrationCurve } from '../../data/calibration';
import styles from './SensitivityCalibration.module.css';

export function CalibrationSlider({ threshold, onThresholdChange }) {
  return (
    <div className={styles.trackContainer}>
      <div className={`${styles.tickRow} tabular-nums`} aria-hidden="true">
        {calibrationCurve.map((point) => (
          <span
            key={point.threshold}
            className={`${styles.tickItem} ${point.isDefault ? styles.defaultTick : ''}`}
            onClick={() => onThresholdChange(point.threshold)}
          >
            {point.threshold} ({point.changePercent.toFixed(2)}%{point.isDefault ? ' default' : ''})
          </span>
        ))}
      </div>

      <input
        type="range"
        className={styles.minimalRange}
        min={10}
        max={30}
        step={0.1}
        value={threshold}
        onChange={(e) => onThresholdChange(parseFloat(e.target.value))}
        aria-label="Detection Sensitivity Threshold"
        aria-valuemin={10}
        aria-valuemax={30}
        aria-valuenow={threshold}
      />
    </div>
  );
}
