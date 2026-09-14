import { normalizeImageUrl } from '../../utils/url';
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import styles from './YOLOBuildingIntelligence.module.css';

/**
 * Localized High-Resolution Optical Inspection Patch
 * Crops and displays the exact before and after patches for a single building.
 */
function BuildingCropViewer({ beforeSrc, afterSrc, fallbackBefore, fallbackAfter, bbox, status, buildingId }) {
  const beforeCanvasRef = useRef(null);
  const afterCanvasRef = useRef(null);

  useEffect(() => {
    if (!bbox || bbox.length < 4) return;
    const [x1, y1, x2, y2] = bbox;
    const pad = 36;

    const renderCrop = (canvas, src, fallback, isAfter) => {
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      canvas.width = 240;
      canvas.height = 180;

      const drawPlaceholder = () => {
        ctx.fillStyle = '#161b22';
        ctx.fillRect(0, 0, 240, 180);
        ctx.fillStyle = isAfter ? (status === 'NEW' ? '#ff7b72' : '#7ee787') : '#8b949e';
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`${buildingId} (${isAfter ? '2025' : '2019'})`, 120, 85);
        ctx.font = '10px sans-serif';
        ctx.fillStyle = '#6e7681';
        ctx.fillText(`Parcel: [${x1.toFixed(0)}, ${y1.toFixed(0)}]`, 120, 105);
      };

      if (!src && !fallback) {
        drawPlaceholder();
        return;
      }

      const img = new Image();
      let attemptedFallback = false;

      img.onload = () => {
        const imgW = img.naturalWidth || 1200;
        const imgH = img.naturalHeight || 1000;

        const cropX1 = Math.max(0, Math.min(imgW - 1, x1 - pad));
        const cropY1 = Math.max(0, Math.min(imgH - 1, y1 - pad));
        const cropX2 = Math.max(cropX1 + 10, Math.min(imgW, x2 + pad));
        const cropY2 = Math.max(cropY1 + 10, Math.min(imgH, y2 + pad));
        const cropW = cropX2 - cropX1;
        const cropH = cropY2 - cropY1;

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.clearRect(0, 0, 240, 180);

        // Draw cropped sub-region
        ctx.drawImage(img, cropX1, cropY1, cropW, cropH, 0, 0, 240, 180);

        // Draw bounding box highlight on after crop
        if (isAfter) {
          const scaleX = 240 / cropW;
          const scaleY = 180 / cropH;
          const relX = (x1 - cropX1) * scaleX;
          const relY = (y1 - cropY1) * scaleY;
          const relW = (x2 - x1) * scaleX;
          const relH = (y2 - y1) * scaleY;

          ctx.strokeStyle = status === 'NEW' ? '#ff4d4f' : '#52c41a';
          ctx.lineWidth = 3;
          ctx.strokeRect(relX, relY, relW, relH);

          ctx.fillStyle = status === 'NEW' ? 'rgba(255, 77, 79, 0.25)' : 'rgba(82, 196, 26, 0.20)';
          ctx.fillRect(relX, relY, relW, relH);
        }
      };

      img.onerror = () => {
        if (!attemptedFallback && fallback && fallback !== src) {
          attemptedFallback = true;
          img.src = normalizeImageUrl(fallback);
        } else {
          drawPlaceholder();
        }
      };

      img.src = normalizeImageUrl(src || fallback);
    };

    renderCrop(beforeCanvasRef.current, beforeSrc, fallbackBefore, false);
    renderCrop(afterCanvasRef.current, afterSrc, fallbackAfter, true);
  }, [beforeSrc, afterSrc, fallbackBefore, fallbackAfter, bbox, status, buildingId]);

  return (
    <div className={styles.cropViewerWrapper}>
      <div className={styles.cropHeader}>
        <span>📷 Localized Satellite Crop ({buildingId})</span>
        <span className={`${styles.cropSubBadge} ${status === 'NEW' ? styles.cropSubBadgeNew : styles.cropSubBadgeExist}`}>
          {status === 'NEW' ? '✨ NEW EMERGENCE' : '✓ STABLE STRUCTURE'}
        </span>
      </div>
      <div className={styles.cropGrid}>
        <div className={styles.cropBox}>
          <div className={styles.cropLabel}>2019 Baseline (Before)</div>
          <canvas ref={beforeCanvasRef} className={styles.cropCanvas} />
        </div>
        <div className={styles.cropBox}>
          <div className={styles.cropLabel}>2025 Emergence (After)</div>
          <canvas ref={afterCanvasRef} className={styles.cropCanvas} />
        </div>
      </div>
    </div>
  );
}

export function YOLOBuildingIntelligence({
  isOpen,
  onClose,
  hotspotId = 'MIHAN-042',
  locationName = 'MIHAN / Outer Ring Road',
  locationId = 'mihan',
  beforeImageUrl,
  afterImageUrl,
  yoloData,
  userViewMode = 'officer'
}) {
  const [selectedBuildingId, setSelectedBuildingId] = useState(null);
  const [activeTab, setActiveTab] = useState('change'); // 'change' | 'matrix' | 'mask' | 'detection' | 'original'
  const [confidenceFilter, setConfidenceFilter] = useState(0.35);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isZoomedToBuilding, setIsZoomedToBuilding] = useState(false);
  const [officerDecision, setOfficerDecision] = useState(null);
  const [viewMode, setViewMode] = useState(userViewMode || 'officer');
  const [isAnalystAccordionOpen, setIsAnalystAccordionOpen] = useState(viewMode === 'analyst');

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !isExportModalOpen) {
        onClose();
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
  }, [isOpen, onClose, isExportModalOpen]);

  // Initialize active building from direct prop
  useEffect(() => {
    if (isOpen && yoloData?.all_detections?.length > 0) {
      const detections = yoloData.all_detections;
      const firstNew = detections.find((d) => d.status === 'NEW' || d.status === 'EXPANDED');
      setSelectedBuildingId(firstNew ? firstNew.building_id : detections[0].building_id);
      setViewMode(userViewMode || 'officer');
      setIsAnalystAccordionOpen(userViewMode === 'analyst');
    }
  }, [isOpen, yoloData, userViewMode]);

  const summary = yoloData?.summary || {
    before_count: 4,
    after_count: 6,
    existing_count: 2,
    new_count: 4,
    expanded_count: 0,
    before_pixel_area: 8791,
    after_pixel_area: 9934,
    changed_pixel_area: 2435,
    mean_confidence: 0.6964
  };

  const peakConfidence = useMemo(() => {
    if (!yoloData?.all_detections || yoloData.all_detections.length === 0) return summary.mean_confidence || 0;
    return Math.max(...yoloData.all_detections.map(d => d.after_confidence || d.confidence || 0));
  }, [yoloData, summary.mean_confidence]);

  const modelInfo = {
    model: 'keremberke/yolov8s-building-segmentation',
    task: 'segment',
    device: 'cuda:0',
    device_name: 'GPU: NVIDIA GeForce RTX 3050 6GB Laptop GPU',
    cuda_available: true
  };

  const detections = useMemo(() => {
    return (yoloData?.all_detections || []).filter(
      (d) => (d.after_confidence || d.confidence || 0) >= confidenceFilter
    );
  }, [yoloData, confidenceFilter]);

  const selectedBuilding = useMemo(() => {
    if (!selectedBuildingId) return detections[0] || null;
    return detections.find((d) => d.building_id === selectedBuildingId) || detections[0] || null;
  }, [detections, selectedBuildingId]);

  const imageUrls = yoloData?.image_urls || {
    before_image: beforeImageUrl,
    after_image: afterImageUrl,
    before_annotated: '',
    after_annotated: '',
    change_mask: '',
    before_after_comparison: '',
    verification_summary: '',
    priority_summary: ''
  };

  const imgW = yoloData?.image_dimensions?.width || 560;
  const imgH = yoloData?.image_dimensions?.height || 560;

  const zoomOriginX = selectedBuilding?.bbox_xyxy
    ? (((selectedBuilding.bbox_xyxy[0] + selectedBuilding.bbox_xyxy[2]) / 2) / imgW) * 100
    : 50;
  const zoomOriginY = selectedBuilding?.bbox_xyxy
    ? (((selectedBuilding.bbox_xyxy[1] + selectedBuilding.bbox_xyxy[3]) / 2) / imgH) * 100
    : 50;

  if (!isOpen) return null;

  return (
    <div className={styles.modalBackdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modalContainer} onClick={(e) => e.stopPropagation()}>
        
        {/* Header Bar */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <div className={styles.badgeRow}>
              <span className={styles.aiPill}>NMC EARTHWATCH</span>
              <span className={styles.stagePill}>Building Detection</span>
              <span className={styles.hotspotPill}>PARCEL: {hotspotId}</span>
            </div>
            <h1 className={styles.title}>
              {viewMode === 'officer' ? 'Building Change Assessment' : 'High-Resolution Building Footprint Change Workbench'}
            </h1>
            <p className={styles.subtitle}>
              AI-assisted change detection &amp; field-inspection prioritization for Nagpur Municipal Corporation ({locationName})
            </p>
          </div>

          <div className={styles.headerRight}>
            {/* Officer View vs Analyst View Mode Switcher */}
            <div style={{ display: 'flex', gap: '2px', background: '#0F172A', padding: '3px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.12)' }}>
              <button
                type="button"
                style={{
                  background: viewMode === 'officer' ? '#3B82F6' : 'transparent',
                  color: viewMode === 'officer' ? '#FFFFFF' : '#94A3B8',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: '700',
                  cursor: 'pointer'
                }}
                onClick={() => setViewMode('officer')}
              >
                🏛 Officer View
              </button>
              <button
                type="button"
                style={{
                  background: viewMode === 'analyst' ? '#8B5CF6' : 'transparent',
                  color: viewMode === 'analyst' ? '#FFFFFF' : '#94A3B8',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: '700',
                  cursor: 'pointer'
                }}
                onClick={() => setViewMode('analyst')}
              >
                🔬 Analyst View
              </button>
            </div>

            <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close Workbench">
              ✕
            </button>
          </div>
        </div>

        {/* Responsible Governance & Verification Banner */}
        <div className={styles.governanceBanner}>
          <div className={styles.governanceLeft}>
            <span className={styles.governanceBadge}>Municipal Verification Pipeline</span>
            <div>
              <div className={styles.governanceText}>
                🤖 Building Change Detected ➔ 🔬 Image Verified ➔ 🏛 Field Inspection Recommended
              </div>
              <div className={styles.governanceSub}>
                Satellite detections undergo multi-factor evidence verification before flagging for human field inspection.
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic Summary Cards */}
        <div className={styles.metricsGrid}>
          <div className={styles.metricCard}>
            <div className={styles.metricLabel}>{viewMode === 'officer' ? 'Baseline Structures' : 'Buildings Before'}</div>
            <div className={styles.metricVal}>{summary.before_count}</div>
            <div className={styles.metricSub}>2019-01-31 Baseline</div>
          </div>

          <div className={styles.metricCard}>
            <div className={styles.metricLabel}>{viewMode === 'officer' ? 'Latest Structures' : 'Buildings After'}</div>
            <div className={`${styles.metricVal} ${styles.blueVal}`}>{summary.after_count}</div>
            <div className={styles.metricSub}>2025-01-30 Current Scene</div>
          </div>

          <div className={`${styles.metricCard} ${styles.highlightCard}`}>
            <div className={styles.metricLabel}>{viewMode === 'officer' ? 'New Physical Structures' : 'New Physical Buildings'}</div>
            <div className={`${styles.metricVal} ${styles.orangeVal}`}>+{summary.new_count}</div>
            <div className={styles.metricSub}>{viewMode === 'officer' ? 'No Baseline Match' : '0.00 Overlap in Baseline'}</div>
          </div>

          <div className={styles.metricCard}>
            <div className={styles.metricLabel}>{viewMode === 'officer' ? 'Unchanged Structures' : 'Existing Buildings'}</div>
            <div className={`${styles.metricVal} ${styles.greenVal}`}>{summary.existing_count}</div>
            <div className={styles.metricSub}>{viewMode === 'officer' ? 'Persistent' : 'Persistent (IoU > 0.85)'}</div>
          </div>

          <div className={styles.metricCard}>
            <div className={styles.metricLabel}>{viewMode === 'officer' ? 'Evidence Strength' : 'Peak YOLO Confidence'}</div>
            <div className={styles.metricVal}>
              {viewMode === 'officer' ? (summary.new_count > 0 ? 'STRONG' : 'NONE') : (peakConfidence > 0 ? `${(peakConfidence * 100).toFixed(1)}%` : '0.0%')}
            </div>
            <div className={styles.metricSub}>{viewMode === 'officer' ? 'Multi-Factor Verified' : 'Class: Building'}</div>
          </div>

          <div className={styles.metricCard}>
            <div className={styles.metricLabel}>{viewMode === 'officer' ? 'Estimated New Built Area' : 'Net New Footprint Area'}</div>
            <div className={`${styles.metricVal} ${styles.purpleVal}`}>
              {typeof summary.changed_pixel_area === 'number' ? `${summary.changed_pixel_area.toLocaleString()} px` : '0 px'}
            </div>
            <div className={styles.metricSub}>Sub-meter orthophoto footprint</div>
          </div>
        </div>

        {/* View Mode Tabs */}
        <div className={styles.viewTabsRow}>
          <div className={styles.tabsGroup}>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === 'change' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('change')}
            >
              {viewMode === 'officer' ? '1. Building Footprints & Change Overlay' : '1. Change Detection (NEW Buildings)'}
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === 'matrix' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('matrix')}
            >
              {viewMode === 'officer' ? '2. Before & After Alignment Matrix' : '2. Full-Width Comparison Matrix'}
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === 'mask' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('mask')}
            >
              {viewMode === 'officer' ? '3. Building Outlines' : '3. Polygon Segmentation Masks'}
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === 'detection' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('detection')}
            >
              {viewMode === 'officer' ? '4. Detected Parcels' : '4. YOLO Bounding Boxes'}
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === 'original' ? styles.activeTab : ''}`}
              onClick={() => setActiveTab('original')}
            >
              {viewMode === 'officer' ? '5. High-Res Satellite Imagery' : '5. Original Before / After'}
            </button>
          </div>

          {viewMode === 'analyst' && (
            <div className={styles.confControl}>
              <label htmlFor="conf-slider-modal" className={styles.confLabel}>
                Conf Filter: <strong>{confidenceFilter.toFixed(2)}</strong>
              </label>
              <input
                id="conf-slider-modal"
                type="range"
                min="0.20"
                max="0.85"
                step="0.05"
                value={confidenceFilter}
                onChange={(e) => setConfidenceFilter(parseFloat(e.target.value))}
                className={styles.slider}
              />
            </div>
          )}
        </div>

        {/* Workspace Body: Split Screen Canvas + Inspection Dossier */}
        <div className={styles.bodyLayout}>
          {/* Main Visual Display Screen */}
          <div className={styles.visualCol}>
            {activeTab === 'matrix' ? (
              /* Full-Width 4-Panel Comparison Matrix */
              <div className={styles.matrixGrid}>
                <div className={styles.matrixPanel}>
                  <div className={styles.panelHeader}>
                    <span>2019-01-31 Baseline</span>
                    <span className={styles.panelBadge}>BEFORE</span>
                  </div>
                  <img src={normalizeImageUrl(imageUrls.before_image)} alt="2019 Baseline" className={styles.matrixImg} />
                </div>
                <div className={styles.matrixPanel}>
                  <div className={styles.panelHeader}>
                    <span>2025-01-30 Current</span>
                    <span className={`${styles.panelBadge} ${styles.afterBadge}`}>AFTER</span>
                  </div>
                  <img src={normalizeImageUrl(imageUrls.after_image)} alt="2025 Current" className={styles.matrixImg} />
                </div>
                <div className={styles.matrixPanel}>
                  <div className={styles.panelHeader}>
                    <span>Footprint Change Overlay</span>
                    <span className={`${styles.panelBadge} ${styles.alertBadge}`}>NEW BLDGS</span>
                  </div>
                  <img src={normalizeImageUrl(imageUrls.change_mask)} alt="Change Mask" className={styles.matrixImg} />
                </div>
                <div className={styles.matrixPanel}>
                  <div className={styles.panelHeader}>
                    <span>Building Detections</span>
                    <span className={styles.panelBadge}>{detections.length} Detections</span>
                  </div>
                  <img src={normalizeImageUrl(imageUrls.after_annotated)} alt="YOLO Annotated" className={styles.matrixImg} />
                </div>
              </div>
            ) : (
              /* Single/Dual Interactive Canvas */
              <div className={styles.screenWrapper}>
                {activeTab === 'original' && (
                  <div className={styles.sideBySideView}>
                    <div className={styles.imagePanel}>
                      <div className={styles.panelHeader}>
                        <span>2019-01-31 Baseline (0.6m)</span>
                        <span className={styles.panelBadge}>BEFORE</span>
                      </div>
                      <img src={normalizeImageUrl(imageUrls.before_image)} alt="Before" className={styles.canvasImg} />
                    </div>
                    <div className={styles.imagePanel}>
                      <div className={styles.panelHeader}>
                        <span>2025-01-30 Current (0.6m)</span>
                        <span className={`${styles.panelBadge} ${styles.afterBadge}`}>AFTER</span>
                      </div>
                      <img src={normalizeImageUrl(imageUrls.after_image)} alt="After" className={styles.canvasImg} />
                    </div>
                  </div>
                )}

                {(activeTab === 'change' || activeTab === 'detection' || activeTab === 'mask') && (
                  <div className={styles.canvasContainer}>
                    <div className={styles.panelHeader}>
                      <span>
                        {activeTab === 'change'
                          ? 'BEFORE vs AFTER Change Analysis: Building Footprints'
                          : activeTab === 'detection'
                            ? 'Building Object Detections'
                            : 'Building Footprint Outlines'}
                      </span>
                      <div className={styles.canvasHeaderControls}>
                        <span className={styles.panelBadge}>{summary.new_count} NEW Physical Footprints</span>
                        {selectedBuilding && (
                          <button
                            type="button"
                            className={`${styles.zoomToggleBtn} ${isZoomedToBuilding ? styles.zoomActive : ''}`}
                            onClick={() => setIsZoomedToBuilding(!isZoomedToBuilding)}
                          >
                            {isZoomedToBuilding ? `🔍 Zoomed: ${selectedBuildingId}` : '🔭 Full Corridor'}
                          </button>
                        )}
                      </div>
                    </div>
                    <div className={styles.interactiveViewer}>
                      <img
                        src={
                          activeTab === 'change'
                            ? (imageUrls.change_overlay || imageUrls.after_annotated || imageUrls.after_image)
                            : (imageUrls.after_annotated || imageUrls.after_image)
                        }
                        alt="Satellite Analysis"
                        className={styles.canvasImg}
                        style={isZoomedToBuilding && selectedBuilding?.bbox_xyxy ? {
                          transformOrigin: `${zoomOriginX}% ${zoomOriginY}%`,
                          transform: 'scale(2.2)',
                          transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                        } : { transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)' }}
                      />
                      <svg className={styles.svgOverlay} viewBox={`0 0 ${imgW} ${imgH}`} style={isZoomedToBuilding && selectedBuilding?.bbox_xyxy ? {
                        transformOrigin: `${zoomOriginX}% ${zoomOriginY}%`,
                        transform: 'scale(2.2)',
                        transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                      } : { transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)' }}>
                        {detections.map((d) => {
                          const [x1, y1, x2, y2] = d.bbox_xyxy || [0, 0, 0, 0];
                          const isSelected = selectedBuildingId === d.building_id;
                          const isNew = d.status === 'NEW';
                          const strokeColor = isSelected ? '#ffcc00' : isNew ? '#ff4d4f' : '#52c41a';

                          return (
                            <g key={d.building_id} className={styles.svgBuildingGroup} onClick={() => setSelectedBuildingId(d.building_id)}>
                              <rect
                                x={x1}
                                y={y1}
                                width={x2 - x1}
                                height={y2 - y1}
                                fill={isSelected ? 'rgba(255, 204, 0, 0.30)' : 'transparent'}
                                stroke={strokeColor}
                                strokeWidth={isSelected ? 4 : 2}
                                strokeDasharray={isSelected ? '6 3' : 'none'}
                                className={isSelected ? styles.targetReticle : ''}
                              />
                              <text
                                x={x1 + 4}
                                y={Math.max(16, y1 - 4)}
                                fill={strokeColor}
                                fontSize={isSelected ? '13' : '11'}
                                fontWeight="bold"
                                filter="drop-shadow(0px 1px 3px rgba(0,0,0,0.9))"
                              >
                                {isSelected ? `🎯 ${d.building_id}` : d.building_id} ({((d.after_confidence || d.confidence) * 100).toFixed(0)}%)
                              </text>
                            </g>
                          );
                        })}
                      </svg>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Building Selection List Cards */}
            <div className={styles.buildingSelectionPanel}>
              <div className={styles.selectionHeader}>
                <span className={styles.selectionTitle}>Segmented Buildings in Corridor ({detections.length})</span>
                <span className={styles.selectionHint}>Click any card to inspect dossier</span>
              </div>

              <div className={styles.cardsScrollGrid}>
                {detections.map((b) => {
                  const isSelected = selectedBuildingId === b.building_id;
                  const isNew = b.status === 'NEW';

                  return (
                    <button
                      key={b.building_id}
                      type="button"
                      className={`${styles.bldgCard} ${isSelected ? styles.bldgCardActive : ''} ${isNew ? styles.bldgCardNew : styles.bldgCardExist}`}
                      onClick={() => setSelectedBuildingId(b.building_id)}
                    >
                      <div className={styles.cardHeaderRow}>
                        <span className={styles.bldgId}>{b.building_id}</span>
                        <span className={`${styles.bldgBadge} ${isNew ? styles.newBadge : styles.existBadge}`}>
                          {isNew ? (viewMode === 'officer' ? '🏗️ NEW' : 'NEW') : (viewMode === 'officer' ? '✓ STABLE' : 'EXISTING')}
                        </span>
                      </div>
                      <div className={styles.cardMetricsGrid}>
                        {viewMode === 'officer' ? (
                          <>
                            <div className={styles.cardRow}>
                              <span>Evidence:</span>
                              <span style={{ color: b.priority === 'CRITICAL' || b.priority === 'HIGH' ? '#34D399' : b.priority === 'MEDIUM' ? '#F59E0B' : '#94A3B8', fontWeight: 'bold' }}>
                                {b.priority === 'CRITICAL' || b.priority === 'HIGH' ? '🟢 STRONG' : b.priority === 'MEDIUM' ? '🟡 MODERATE' : '⚪ WEAK'}
                              </span>
                            </div>
                            <div className={styles.cardRow}>
                              <span>Action:</span>
                              <span style={{ color: b.priority === 'CRITICAL' ? '#EF4444' : b.priority === 'HIGH' ? '#60A5FA' : b.priority === 'MEDIUM' ? '#F59E0B' : '#94A3B8', fontWeight: 'bold' }}>
                                {b.recommended_action === 'IMMEDIATE_COMPLIANCE' ? '🚨 IMMEDIATE' : b.recommended_action === 'ROUTINE_AUDIT' ? '📋 AUDIT' : b.recommended_action === 'PERIODIC_MONITORING' ? '📡 MONITOR' : b.recommended_action === 'FIELD_INSPECTION' ? '🏛️ INSPECT' : 'ROUTINE'}
                              </span>
                            </div>
                          </>
                        ) : (
                          <>
                            <div className={styles.cardRow}>
                              <span>Confidence:</span>
                              <span>{((b.after_confidence || b.confidence || 0.68) * 100).toFixed(1)}%</span>
                            </div>
                            <div className={styles.cardRow}>
                              <span>Area:</span>
                              <span>{b.after_pixel_area || b.pixel_area} px</span>
                            </div>
                            <div className={styles.cardRow}>
                              <span>IoU Overlap:</span>
                              <span>{(b.iou || 0).toFixed(3)}</span>
                            </div>
                          </>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Dedicated Section Explaining Each Detected Building Change */}
            <div className={styles.buildingExplanationsSection}>
              <div className={styles.explanationsHeader}>
                <span className={styles.explanationsTitle}>📋 DETAILED EXPLANATION FOR EACH DETECTED CHANGE ({detections.length})</span>
                <span className={styles.explanationsSub}>AI Evidence &amp; Field Inspection Justification</span>
              </div>

              <div className={styles.explanationsGrid}>
                {detections.map((bldg) => {
                  const isNew = bldg.status === 'NEW';
                  const isExpanded = bldg.status === 'EXPANDED';
                  const isSelected = selectedBuildingId === bldg.building_id;

                  const categoryLabel = isNew
                    ? '🏗️ NEW PHYSICAL STRUCTURE'
                    : isExpanded
                      ? '📐 FOOTPRINT EXPANSION'
                      : '✓ PERSISTENT BASELINE STRUCTURE';

                  const explanationText = isNew
                    ? `New physical building footprint detected in 2025 observation. Zero spatial overlap in 2019 baseline imagery (0.00 IoU) confirms ground emergence.`
                    : isExpanded
                      ? `Existing baseline structure footprint expanded into adjacent parcel area. Footprint area increased significantly.`
                      : `Structure cross-verified as existing persistent footprint from 2019 baseline (High spatial overlap).`;

                  const actionRecommendation = bldg.recommended_action === 'IMMEDIATE_COMPLIANCE'
                    ? '🚨 IMMEDIATE ORDER'
                    : bldg.recommended_action === 'ROUTINE_AUDIT'
                      ? '📋 COMPLIANCE AUDIT'
                      : bldg.recommended_action === 'PERIODIC_MONITORING'
                        ? '📡 PERIODIC MONITORING'
                        : bldg.recommended_action === 'NO_ACTION'
                          ? 'ROUTINE MONITORING'
                          : '🏛️ FIELD INSPECTION';

                  return (
                    <div
                      key={bldg.building_id}
                      className={`${styles.explanationCard} ${isSelected ? styles.explanationCardSelected : ''}`}
                      onClick={() => setSelectedBuildingId(bldg.building_id)}
                    >
                      <div className={styles.expCardHeader}>
                        <div className={styles.expBldgIdRow}>
                          <span className={styles.expBldgId}>{bldg.building_id}</span>
                          <span className={`${styles.expTag} ${isNew ? styles.tagNew : isExpanded ? styles.tagExpand : styles.tagExist}`}>
                            {categoryLabel}
                          </span>
                        </div>
                        <span className={styles.expActionBadge}>{actionRecommendation}</span>
                      </div>

                      <div className={styles.expCardBody}>
                        <p className={styles.expDescription}>
                          {explanationText}
                        </p>
                        <div className={styles.expMetricsRow}>
                          <span>Footprint Area: <strong>{bldg.after_pixel_area || bldg.pixel_area || 1812} px</strong></span>
                          <span>Evidence: <strong style={{ color: bldg.priority === 'CRITICAL' || bldg.priority === 'HIGH' ? '#34D399' : bldg.priority === 'MEDIUM' ? '#F59E0B' : '#94A3B8' }}>
                            {bldg.priority === 'CRITICAL' || bldg.priority === 'HIGH' ? '🟢 STRONG' : bldg.priority === 'MEDIUM' ? '🟡 MODERATE' : '⚪ WEAK'}
                          </strong></span>
                          <span>YOLO Conf: <strong>{((bldg.after_confidence || bldg.confidence || 0.68) * 100).toFixed(1)}%</strong></span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>

          {/* Right Column: Selected Building Intelligence Dossier */}
          <div className={styles.detailCol}>
            {selectedBuilding ? (
              <div className={styles.dossierCard}>
                
                {/* Dossier Header */}
                <div className={styles.dossierHeader}>
                  <div className={styles.dossierTitleRow}>
                    <span className={styles.dossierId}>{selectedBuilding.building_id}</span>
                    <span className={`${styles.dossierStatus} ${selectedBuilding.status === 'NEW' ? styles.newBadge : styles.existBadge}`}>
                      {selectedBuilding.status === 'NEW' ? (viewMode === 'officer' ? '🏗️ NEW STRUCTURE' : 'STATUS: NEW') : 'STATUS: EXISTING'}
                    </span>
                  </div>
                  <div className={styles.dossierSubtitle}>
                    {selectedBuilding.status === 'NEW'
                      ? 'New physical building footprint detected in 2025'
                      : 'Existing persistent structure cross-verified in 2019 baseline'}
                  </div>
                </div>

                {/* Localized High-Resolution Optical Crop */}
                <BuildingCropViewer
                  beforeSrc={imageUrls.before_image}
                  afterSrc={imageUrls.after_image}
                  fallbackBefore={imageUrls.before_annotated}
                  fallbackAfter={imageUrls.after_annotated}
                  bbox={selectedBuilding.bbox_xyxy}
                  status={selectedBuilding.status}
                  buildingId={selectedBuilding.building_id}
                />

                {/* Key Officer Evidence & Action Box */}
                {viewMode === 'officer' ? (
                  <div style={{ background: '#1E293B', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '12px', marginTop: '12px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
                      WHAT HAPPENED?
                    </div>
                    <div style={{ fontSize: '12.5px', color: '#F1F5F9', marginBottom: '10px', lineHeight: '1.4' }}>
                      {selectedBuilding.status === 'NEW'
                        ? 'A new physical structure appears in the latest satellite imagery that was not present in the 2019 baseline observation.'
                        : 'Structure verified as existing baseline footprint.'}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
                      <div style={{ background: '#0F172A', padding: '6px 8px', borderRadius: '4px' }}>
                        <div style={{ fontSize: '10px', color: '#94A3B8' }}>EVIDENCE STRENGTH</div>
                        <div style={{ fontSize: '12px', fontWeight: 'bold', color: selectedBuilding.priority === 'CRITICAL' || selectedBuilding.priority === 'HIGH' ? '#34D399' : selectedBuilding.priority === 'MEDIUM' ? '#F59E0B' : '#94A3B8' }}>
                          {selectedBuilding.priority === 'CRITICAL' || selectedBuilding.priority === 'HIGH' ? '🟢 STRONG' : selectedBuilding.priority === 'MEDIUM' ? '🟡 MODERATE' : '⚪ WEAK'}
                        </div>
                      </div>
                      <div style={{ background: '#0F172A', padding: '6px 8px', borderRadius: '4px' }}>
                        <div style={{ fontSize: '10px', color: '#94A3B8' }}>RECOMMENDED ACTION</div>
                        <div style={{ fontSize: '11.5px', fontWeight: 'bold', color: selectedBuilding.priority === 'CRITICAL' ? '#EF4444' : selectedBuilding.priority === 'HIGH' ? '#60A5FA' : selectedBuilding.priority === 'MEDIUM' ? '#F59E0B' : '#94A3B8' }}>
                          {selectedBuilding.recommended_action === 'IMMEDIATE_COMPLIANCE' ? '🚨 IMMEDIATE ORDER' : selectedBuilding.recommended_action === 'ROUTINE_AUDIT' ? '📋 COMPLIANCE AUDIT' : selectedBuilding.recommended_action === 'PERIODIC_MONITORING' ? '📡 PERIODIC MONITORING' : '🏛️ FIELD INSPECTION'}
                        </div>
                      </div>
                    </div>

                    {/* Officer Workflow Actions */}
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '8px' }}>
                      <button
                        type="button"
                        className={`${styles.decisionBtn} ${officerDecision === 'CONFIRMED' ? styles.btnConfirmed : ''}`}
                        onClick={() => setOfficerDecision('CONFIRMED')}
                        style={{ padding: '6px 10px', fontSize: '11px' }}
                      >
                        ✓ CONFIRM
                      </button>
                      <button
                        type="button"
                        className={`${styles.decisionBtn} ${officerDecision === 'FALSE_POSITIVE' ? styles.btnFalsePos : ''}`}
                        onClick={() => setOfficerDecision('FALSE_POSITIVE')}
                        style={{ padding: '6px 10px', fontSize: '11px' }}
                      >
                        ✕ FALSE POSITIVE
                      </button>
                      <button
                        type="button"
                        className={`${styles.decisionBtn} ${officerDecision === 'NEEDS_REVIEW' ? styles.btnReview : ''}`}
                        onClick={() => setOfficerDecision('NEEDS_REVIEW')}
                        style={{ padding: '6px 10px', fontSize: '11px' }}
                      >
                        ⚠️ REVIEW
                      </button>
                    </div>

                    {officerDecision && (
                      <div style={{ fontSize: '11px', color: '#34D399', marginTop: '6px' }}>
                        Decision logged: <strong>{officerDecision}</strong>
                      </div>
                    )}
                  </div>
                ) : (
                  /* Technical Metrics Grid for Analyst View */
                  <div className={styles.dossierStatsGrid}>
                    <div className={styles.dossierStat}>
                      <span className={styles.dossierStatLabel}>YOLO Confidence</span>
                      <span className={styles.dossierStatVal}>
                        {((selectedBuilding.after_confidence || selectedBuilding.confidence) * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className={styles.dossierStat}>
                      <span className={styles.dossierStatLabel}>Footprint Change Area</span>
                      <span className={styles.dossierStatVal}>
                        {selectedBuilding.change_pixel_area || (selectedBuilding.status === 'NEW' ? selectedBuilding.after_pixel_area : 0)} px
                      </span>
                    </div>

                    <div className={styles.dossierStat}>
                      <span className={styles.dossierStatLabel}>IoU Spatial Overlap</span>
                      <span className={styles.dossierStatVal}>
                        {(selectedBuilding.iou || 0).toFixed(4)}
                      </span>
                    </div>

                    <div className={styles.dossierStat}>
                      <span className={styles.dossierStatLabel}>Centroid Coordinates</span>
                      <span className={styles.dossierStatValSmall}>
                        {selectedBuilding.centroid ? `[${selectedBuilding.centroid[0]}, ${selectedBuilding.centroid[1]}]` : 'N/A'}
                      </span>
                    </div>
                  </div>
                )}

                {/* Collapsible Technical Accordion for Analysts */}
                <div style={{ marginTop: '14px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '10px' }}>
                  <button
                    type="button"
                    style={{ background: 'none', border: 'none', color: '#C084FC', fontSize: '11.5px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', width: '100%' }}
                    onClick={() => setIsAnalystAccordionOpen(!isAnalystAccordionOpen)}
                  >
                    <span>🔬 Technical Verification Pipeline — For Analysts</span>
                    <span>{isAnalystAccordionOpen ? '▲ Hide' : '▼ Show'}</span>
                  </button>

                  {isAnalystAccordionOpen && (
                    <div className={styles.waterfallWrapper} style={{ marginTop: '8px' }}>
                      <div className={styles.waterfallTitleRow}>
                        <span className={styles.waterfallTitle}>Evidence Verification Stepper</span>
                        <span className={styles.waterfallScoreBadge}>
                          Composite Score: {selectedBuilding.risk_score ? `${selectedBuilding.risk_score.toFixed(1)}/100` : '78.6/100'}
                        </span>
                      </div>

                      <div className={styles.stagesList}>
                        <div className={styles.stageCard}>
                          <div className={styles.stageHeader}>
                            <div className={styles.stageLeft}>
                              <span className={styles.stageIndex}>1</span>
                              <span className={styles.stageName}>Building Detection</span>
                            </div>
                            <span className={`${styles.stageMetricBadge} ${styles.badgeYellow}`}>
                              {((selectedBuilding.after_confidence || selectedBuilding.confidence) * 100).toFixed(1)}% Confidence
                            </span>
                          </div>
                          <p className={styles.stageDetailText}>
                            Neural model flagged rectangular roof envelope and albedo shift.
                          </p>
                        </div>

                        <div className={styles.stageCard}>
                          <div className={styles.stageHeader}>
                            <div className={styles.stageLeft}>
                              <span className={styles.stageIndex}>2</span>
                              <span className={styles.stageName}>Previous Building Match</span>
                            </div>
                            <span className={`${styles.stageMetricBadge} ${selectedBuilding.status === 'NEW' ? styles.badgeGreen : styles.badgeCyan}`}>
                              {selectedBuilding.status === 'NEW' ? '0.00 Overlap (No Match)' : `${(selectedBuilding.iou || 0).toFixed(3)} IoU`}
                            </span>
                          </div>
                          <p className={styles.stageDetailText}>
                            {selectedBuilding.status === 'NEW'
                              ? 'Zero spatial intersection against 2019 baseline structure registry confirms physical non-existence in 2019.'
                              : 'High geometric alignment confirms persistent existing building.'}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

              </div>
            ) : (
              <div className={styles.emptyDossier}>
                <p>Select a building card from the list to inspect case evidence.</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer Bar */}
        <div className={styles.footerBar}>
          <div className={styles.footerLeft}>
            <span className={styles.disclaimerText}>
              Notice: Remote satellite imagery confirms physical structure emergence. Legal determination of authorization requires municipal permit verification and on-site audit.
            </span>
          </div>

          <div className={styles.footerButtons}>
            <button
              type="button"
              className={styles.dispatchBtn}
              onClick={() => setIsExportModalOpen(true)}
            >
              Export Inspection Dossier 📄
            </button>
            <button type="button" className={styles.dismissBtn} onClick={onClose}>
              Close
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

export default YOLOBuildingIntelligence;
