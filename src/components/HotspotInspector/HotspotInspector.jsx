import React from 'react';
import styles from './HotspotInspector.module.css';

export function HotspotInspector({
  hotspots = [],
  selectedHotspotId,
  onSelectHotspot,
  onInspectHotspot,
  onInspectAll
}) {
  if (!hotspots || hotspots.length === 0) {
    return null;
  }

  const highPriorityCount = hotspots.filter((h) =>
    ['CRITICAL', 'HIGH'].includes(h.priority)
  ).length;

  return (
    <div className={styles.hotspotCard} aria-label="Candidate Spatial Hotspots">
      <div className={styles.headerRow}>
        <div className={styles.titleGroup}>
          <span className={styles.pulseDot}>●</span>
          <span className={styles.hotspotTitle}>AI Candidate Hotspots</span>
        </div>
        <span className={styles.badgeCount}>
          {highPriorityCount} High Priority
        </span>
      </div>

      <div className={styles.hotspotList}>
        {hotspots.map((h) => {
          const isSelected = selectedHotspotId === h.hotspot_id;
          const priorityClass =
            h.priority === 'CRITICAL'
              ? styles.critical
              : h.priority === 'HIGH'
              ? styles.high
              : h.priority === 'MEDIUM'
              ? styles.medium
              : styles.low;

          return (
            <div
              key={h.hotspot_id}
              className={`${styles.hotspotItem} ${isSelected ? styles.selectedItem : ''}`}
              onClick={() => onSelectHotspot && onSelectHotspot(h.hotspot_id)}
            >
              <div className={styles.itemTop}>
                <span className={styles.itemName}>{h.name}</span>
                <span className={`${styles.priorityPill} ${priorityClass}`}>
                  {h.priority}
                </span>
              </div>

              <div className={styles.itemMeta}>
                <span>{h.area_formatted}</span>
                <span>Δ {h.change_percent}%</span>
                <span>{h.change_type_label || 'Candidate'}</span>
              </div>

              <div className={styles.inspectBtnRow}>
                <button
                  type="button"
                  className={styles.inspectBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    onInspectHotspot && onInspectHotspot(h.hotspot_id);
                  }}
                  title="Run multi-scale Wayback high-resolution AI vision verification"
                >
                  <span>🔍</span>
                  <span>INSPECT WITH AI</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {hotspots.length > 1 && (
        <button
          type="button"
          className={styles.batchInspectBtn}
          onClick={onInspectAll}
        >
          ⚡ Batch Verify All Hotspots ({hotspots.length})
        </button>
      )}
    </div>
  );
}

export default HotspotInspector;
