import React, { useState, useEffect, useRef, useCallback } from 'react';
import styles from './BuildingDetailModal.module.css';

export function BuildingDetailModal({ isOpen, onClose, detailCropSrc }) {
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);

  const panStartRef = useRef({ x: 0, y: 0, panX: 0, panY: 0 });
  const viewportRef = useRef(null);

  // Keyboard shortcut listener (Escape to close, +/- to zoom, 0 to reset)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === '+' || e.key === '=') setZoomLevel((z) => Math.min(4.0, Number((z + 0.5).toFixed(1))));
      if (e.key === '-' || e.key === '_') {
        setZoomLevel((z) => {
          const next = Math.max(1.0, Number((z - 0.5).toFixed(1)));
          if (next === 1.0) setPanOffset({ x: 0, y: 0 });
          return next;
        });
      }
      if (e.key === '0') {
        setZoomLevel(1.0);
        setPanOffset({ x: 0, y: 0 });
      }
    };

    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  // Reset zoom on open
  useEffect(() => {
    if (isOpen) {
      setZoomLevel(1.0);
      setPanOffset({ x: 0, y: 0 });
    }
  }, [isOpen]);

  // Mouse wheel zoom
  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 0.25 : -0.25;
    setZoomLevel((z) => {
      const next = Math.min(4.0, Math.max(1.0, Number((z + delta).toFixed(2))));
      if (next === 1.0) setPanOffset({ x: 0, y: 0 });
      return next;
    });
  }, []);

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => el.removeEventListener('wheel', handleWheel);
  }, [handleWheel, isOpen]);

  const handleMouseDown = (e) => {
    if (zoomLevel > 1.0) {
      setIsPanning(true);
      panStartRef.current = {
        x: e.clientX,
        y: e.clientY,
        panX: panOffset.x,
        panY: panOffset.y
      };
    }
  };

  const handleMouseMove = (e) => {
    if (isPanning && zoomLevel > 1.0) {
      const dx = e.clientX - panStartRef.current.x;
      const dy = e.clientY - panStartRef.current.y;
      const maxPan = (zoomLevel - 1) * 450;
      const newX = Math.max(-maxPan, Math.min(maxPan, panStartRef.current.panX + dx));
      const newY = Math.max(-maxPan, Math.min(maxPan, panStartRef.current.panY + dy));
      setPanOffset({ x: newX, y: newY });
    }
  };

  const handleMouseUp = () => {
    if (isPanning) setIsPanning(false);
  };

  if (!isOpen) return null;

  return (
    <div className={styles.backdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modalCard} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.titleGroup}>
            <span className={styles.badge}>0.6m Sub-Meter Tier</span>
            <h2 className={styles.title}>Building-Level Detail & Architectural Precision</h2>
            <p className={styles.subtitle}>
              MIHAN AIIMS Hospital Complex & Logistics SEZ — Comparison of 2019 Baseline, 2025 Construction, and Calibrated Change Mask
            </p>
          </div>

          <div className={styles.headerActions}>
            <div className={styles.modalZoomControl}>
              <button
                type="button"
                className={styles.zoomBtn}
                onClick={() =>
                  setZoomLevel((z) => {
                    const next = Math.max(1.0, Number((z - 0.5).toFixed(1)));
                    if (next === 1.0) setPanOffset({ x: 0, y: 0 });
                    return next;
                  })
                }
                disabled={zoomLevel <= 1.0}
                title="Zoom out"
              >
                −
              </button>
              <span className={styles.zoomPill}>{zoomLevel.toFixed(1)}x</span>
              <button
                type="button"
                className={styles.zoomBtn}
                onClick={() => setZoomLevel((z) => Math.min(4.0, Number((z + 0.5).toFixed(1))))}
                disabled={zoomLevel >= 4.0}
                title="Zoom in"
              >
                +
              </button>
              {zoomLevel > 1.0 && (
                <button
                  type="button"
                  className={styles.zoomResetBtn}
                  onClick={() => {
                    setZoomLevel(1.0);
                    setPanOffset({ x: 0, y: 0 });
                  }}
                  title="Reset zoom"
                >
                  Reset
                </button>
              )}
            </div>

            <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close detail view">
              ✕
            </button>
          </div>
        </div>

        <div
          className={`${styles.imageViewport} ${zoomLevel > 1.0 ? styles.canPan : ''} ${isPanning ? styles.isPanning : ''}`}
          ref={viewportRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <div
            className={styles.imageCanvasWrapper}
            style={{
              transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${zoomLevel})`
            }}
          >
            <img
              src={detailCropSrc || '/wayback_mihan_sameszn_detail_crop.png'}
              alt="0.6m High Resolution Detail Crop: 2019 vs 2025 vs Calibrated Overlay"
              className={styles.detailImage}
              draggable={false}
            />
          </div>

          {zoomLevel > 1.0 && (
            <div className={styles.panOverlayTip}>
              <span>🖱 Drag to Pan • Scroll to Zoom</span>
            </div>
          )}
        </div>

        <div className={styles.footerBar}>
          <div className={styles.footerNote}>
            <span className={styles.noteIcon}>ⓘ</span>
            <span>
              <strong>Sub-Meter Zoom Advantage:</strong> Zoom in up to <strong>4.0x</strong> to inspect individual AIIMS ward pavilions, dual-lane perimeter roads, and warehouse bays resolved with 0.6m precision.
            </span>
          </div>
          <button type="button" className={styles.dismissBtn} onClick={onClose}>
            Close Inspection
          </button>
        </div>
      </div>
    </div>
  );
}

export default BuildingDetailModal;
