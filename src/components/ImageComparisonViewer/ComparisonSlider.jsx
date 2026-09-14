import React from 'react';
import styles from './ImageComparisonViewer.module.css';

export function ComparisonSlider({ positionPct, onKeyDown, onPointerDown, onTouchStart }) {
  const handleMouseDown = (e) => {
    e.stopPropagation();
    if (onPointerDown) onPointerDown(e);
  };

  const handleTouch = (e) => {
    e.stopPropagation();
    if (onTouchStart) onTouchStart(e);
  };

  return (
    <div
      className={styles.sliderDivider}
      style={{ left: `${positionPct}%` }}
      role="slider"
      aria-label="Before and After Satellite Image Split Slider"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(positionPct)}
      tabIndex={0}
      onKeyDown={onKeyDown}
      onMouseDown={handleMouseDown}
      onTouchStart={handleTouch}
    >
      <div className={styles.sliderHandle} title="Drag to compare before & after">
        <svg viewBox="0 0 24 24">
          <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6 1.41-1.41z" />
        </svg>
      </div>
    </div>
  );
}
