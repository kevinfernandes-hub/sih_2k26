import React, { useState, useEffect, useRef } from 'react';
import { useDraggable } from '../../hooks/useDraggable';
import { MapContainer, TileLayer, Rectangle, Tooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import styles from './ImageComparisonViewer.module.css';

/**
 * Normalizes image URLs to relative paths to prevent cross-origin issues
 */
const normalizeImageUrl = (url) => {
  if (!url || typeof url !== 'string') return '';
  if (url.includes('/static/')) return '/static/' + url.split('/static/')[1];
  if (url.includes('/outputs/')) return '/outputs/' + url.split('/outputs/')[1];
  if (url.includes('/public/')) return '/public/' + url.split('/public/')[1];
  return url;
};

// Map View updater component to dynamically set bounds
function MapBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length === 2) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
  return null;
}

export function ImageComparisonViewer({
  pipelineState,
  onSelectCandidate,
  onSelectHotspot
}) {
  const { stage, candidates, selectedCandidate, locationData, hotspots, selectedHotspot } = pipelineState;

  const [selectedTier, setSelectedTier] = useState('10m');
  const [viewMode, setViewMode] = useState('raw'); // 'raw' | 'color' | 'ssim' | 'veg'
  const [cursorCoords, setCursorCoords] = useState('N/A');
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [showHotspotBoxes, setShowHotspotBoxes] = useState(true);

  const panStartRef = useRef({ x: 0, y: 0, panX: 0, panY: 0 });
  const canvasBeforeRef = useRef(null);
  const canvasAfterRef = useRef(null);
  
  const hasImagery = stage === 'investigation' && selectedHotspot && selectedHotspot.before_image && selectedHotspot.after_image;
  const isAnalysisComplete = stage === 'investigation';
  const showMap = ['idle', 'verifying', 'hotspots_ready', 'error'].includes(stage);

  const {
    value: sliderPos,
    setValue: setSliderPos,
    isDragging: isSliderDragging,
    containerRef,
    handlePointerDown: handleSliderPointerDown,
    handleTouchStart: handleSliderTouchStart
  } = useDraggable({ initialValue: 50, min: 2, max: 98 });

  useEffect(() => {
    setZoomLevel(1.0);
    setPanOffset({ x: 0, y: 0 });
  }, [locationData?.location_id, selectedTier]);

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.5, 4.0));
  const handleZoomOut = () => {
    setZoomLevel((prev) => {
      const next = Math.max(prev - 0.5, 1.0);
      if (next === 1.0) setPanOffset({ x: 0, y: 0 });
      return next;
    });
  };
  const handleResetZoom = () => {
    setZoomLevel(1.0);
    setPanOffset({ x: 0, y: 0 });
  };

  const handleMouseDown = (e) => {
    if (e.target.closest(`.${styles.sliderDivider}`) || e.target.closest(`.${styles.floatingControls}`) || showMap) {
      return;
    }
    if (zoomLevel <= 1.0) return;
    setIsPanning(true);
    panStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      panX: panOffset.x,
      panY: panOffset.y
    };
  };

  const handleMouseMove = (e) => {
    if (isSliderDragging || showMap) return;

    if (isPanning && zoomLevel > 1.0) {
      const dx = e.clientX - panStartRef.current.x;
      const dy = e.clientY - panStartRef.current.y;
      const maxPan = (zoomLevel - 1) * 350;
      setPanOffset({
        x: Math.max(-maxPan, Math.min(maxPan, panStartRef.current.panX + dx)),
        y: Math.max(-maxPan, Math.min(maxPan, panStartRef.current.panY + dy))
      });
    }

    if (!containerRef.current || !hasImagery) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const pctX = Math.max(0, Math.min(1, x / rect.width));
    const pctY = Math.max(0, Math.min(1, y / rect.height));

    const lat = locationData?.lat || 21.0542;
    const lng = locationData?.lng || 79.0518;
    const latSpan = 0.048;
    const lngSpan = 0.048;
    const curLat = lat + latSpan / 2 - pctY * latSpan;
    const curLng = lng - lngSpan / 2 + pctX * lngSpan;

    setCursorCoords(`${curLat.toFixed(4)}° N, ${curLng.toFixed(4)}° E`);
  };

  const handleMouseUp = () => setIsPanning(false);

  // Canvas drawing loop
  useEffect(() => {
    if (showMap) return;

    const canvasBefore = canvasBeforeRef.current;
    const canvasAfter = canvasAfterRef.current;
    if (!canvasBefore || !canvasAfter) return;

    const ctxBefore = canvasBefore.getContext('2d');
    const ctxAfter = canvasAfter.getContext('2d');
    if (!ctxBefore || !ctxAfter) return;

    const dpr = typeof window !== 'undefined' ? Math.min(window.devicePixelRatio || 1, 2) : 1;
    const width = containerRef.current ? containerRef.current.clientWidth : 800;
    const height = containerRef.current ? containerRef.current.clientHeight : 540;

    if (!hasImagery) return undefined;

    canvasBefore.width = width * dpr;
    canvasBefore.height = height * dpr;
    canvasBefore.style.width = `${width}px`;
    canvasBefore.style.height = `${height}px`;

    canvasAfter.width = width * dpr;
    canvasAfter.height = height * dpr;
    canvasAfter.style.width = `${width}px`;
    canvasAfter.style.height = `${height}px`;

    const beforeSrc = selectedHotspot?.before_image || '';
    const afterSrc = selectedHotspot?.after_image || '';
    
    let overlaySrc = null;
    if (isAnalysisComplete) {
      if (viewMode === 'color') overlaySrc = selectedHotspot?.color_overlay || '';
      else if (viewMode === 'ssim') overlaySrc = selectedHotspot?.ssim_overlay || '';
      else if (viewMode === 'veg') overlaySrc = selectedHotspot?.color_overlay || ''; // Fallback
    }

    ctxBefore.fillStyle = '#0F172A';
    ctxBefore.fillRect(0, 0, width * dpr, height * dpr);
    ctxAfter.fillStyle = '#0F172A';
    ctxAfter.fillRect(0, 0, width * dpr, height * dpr);

    const applyTransform = (ctx) => {
      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.translate(width / 2 + panOffset.x, height / 2 + panOffset.y);
      ctx.scale(zoomLevel, zoomLevel);
      ctx.translate(-width / 2, -height / 2);
    };

    const drawBoxes = (ctx) => {
      if (!showHotspotBoxes || !hotspots || hotspots.length === 0) return;
      const lat = selectedHotspot?.lat || 21.0542;
      const lng = selectedHotspot?.lng || 79.0518;
      const padding = 0.024;
      const west = lng - padding;
      const south = lat - padding;
      const east = lng + padding;
      const north = lat + padding;

      hotspots.forEach((h) => {
        const isSelected = selectedHotspot?.hotspot_id === h.hotspot_id;
        const [h_min_lon, h_min_lat, h_max_lon, h_max_lat] = h.bbox_wgs84 || [
          h.longitude - 0.005,
          h.latitude - 0.005,
          h.longitude + 0.005,
          h.latitude + 0.005
        ];

        const x1 = ((h_min_lon - west) / (east - west + 1e-7)) * width;
        const x2 = ((h_max_lon - west) / (east - west + 1e-7)) * width;
        const y1 = ((north - h_max_lat) / (north - south + 1e-7)) * height;
        const y2 = ((north - h_min_lat) / (north - south + 1e-7)) * height;

        const bx = Math.min(x1, x2);
        const by = Math.min(y1, y2);
        const bw = Math.max(20, Math.abs(x2 - x1));
        const bh = Math.max(20, Math.abs(y2 - y1));

        ctx.strokeStyle = isSelected ? '#EF4444' : '#EA580C';
        ctx.lineWidth = isSelected ? 2.5 : 1.5;
        ctx.setLineDash([5, 3]);
        ctx.strokeRect(bx, by, bw, bh);
        ctx.setLineDash([]);

        ctx.fillStyle = isSelected ? '#EF4444' : '#EA580C';
        ctx.fillRect(bx, Math.max(0, by - 16), 72, 16);
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 9.5px monospace';
        ctx.fillText(h.hotspot_id || 'HOTSPOT', bx + 4, Math.max(12, by - 4));
      });
    };

    let isSubscribed = true;

    const renderImages = async () => {
      try {
        const imgBefore = new Image();
        imgBefore.crossOrigin = 'anonymous';
        imgBefore.src = normalizeImageUrl(beforeSrc);

        const imgAfter = new Image();
        imgAfter.crossOrigin = 'anonymous';
        imgAfter.src = normalizeImageUrl(afterSrc);

        const imgOverlay = overlaySrc ? new Image() : null;
        if (imgOverlay) {
          imgOverlay.crossOrigin = 'anonymous';
          imgOverlay.src = normalizeImageUrl(overlaySrc);
        }

        const loadPromises = [
          new Promise((resolve) => { imgBefore.onload = resolve; imgBefore.onerror = resolve; }),
          new Promise((resolve) => { imgAfter.onload = resolve; imgAfter.onerror = resolve; })
        ];
        if (imgOverlay) {
          loadPromises.push(new Promise((resolve) => { imgOverlay.onload = resolve; imgOverlay.onerror = resolve; }));
        }
        await Promise.all(loadPromises);

        if (!isSubscribed) return;

        applyTransform(ctxBefore);
        if (imgBefore.width > 0) ctxBefore.drawImage(imgBefore, 0, 0, width, height);
        ctxBefore.restore();

        applyTransform(ctxAfter);
        if (imgAfter.width > 0) ctxAfter.drawImage(imgAfter, 0, 0, width, height);
        
        if (imgOverlay && imgOverlay.width > 0) {
          ctxAfter.globalCompositeOperation = 'source-over';
          ctxAfter.globalAlpha = 0.65;
          ctxAfter.drawImage(imgOverlay, 0, 0, width, height);
          ctxAfter.globalAlpha = 1.0;
        }
        drawBoxes(ctxAfter);
        ctxAfter.restore();
      } catch (err) {
        console.warn('Canvas render fallback:', err);
      }
    };

    renderImages();
    return () => { isSubscribed = false; };
  }, [
    locationData?.location_id,
    selectedTier,
    viewMode,
    zoomLevel,
    panOffset,
    showHotspotBoxes,
    hotspots,
    selectedHotspot,
    hasImagery,
    isAnalysisComplete,
    showMap
  ]);

  const renderEmptyState = () => (
    <div className={styles.emptyStateContainer}>
      <div className={styles.emptyGrid}></div>
      <div className={styles.emptyContent}>
        <div className={styles.emptyIcon}>🌎</div>
        <div className={styles.emptyTitle}>EARTHWATCH ENGINE READY</div>
        <div className={styles.emptyDesc}>Enter a semantic query to identify candidate regions, acquire multi-temporal imagery, and perform targeted change analysis.</div>
      </div>
    </div>
  );

  const renderLoadingState = (message) => (
    <div className={styles.loadingContainer}>
      <div className={styles.loadingSpinner}></div>
      <div className={styles.loadingText}>{message}</div>
    </div>
  );

  const getHotspotBounds = () => {
    if (!hotspots || hotspots.length === 0) return null;
    let minLat = 90, maxLat = -90, minLng = 180, maxLng = -180;
    hotspots.forEach(c => {
      const [west, south, east, north] = c.bbox || [79.11, 21.115, 79.155, 21.155];
      minLat = Math.min(minLat, south);
      maxLat = Math.max(maxLat, north);
      minLng = Math.min(minLng, west);
      maxLng = Math.max(maxLng, east);
    });
    return [[minLat, minLng], [maxLat, maxLng]];
  };

  const getReadableName = (candidate) => {
    let name = candidate.location_name || candidate.scene_id || candidate.tile_id || 'Unknown Region';
    if (name.includes('_')) {
      const parts = name.split('_');
      if (parts.length > 1) name = parts[1];
    }
    return name;
  };

  const renderMapState = () => {
    const bounds = getHotspotBounds();
    return (
      <div style={{width: '100%', height: '100%', background: '#0a0d14'}}>
        <MapContainer 
          bounds={bounds || [[21.1, 79.1], [21.2, 79.2]]} 
          style={{ height: '100%', width: '100%', background: '#0a0d14' }}
          zoomControl={false}
          attributionControl={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          {bounds && <MapBounds bounds={bounds} />}
          
          {(hotspots || []).map((c, idx) => {
            const isSelected = selectedHotspot && selectedHotspot.hotspot_id === c.hotspot_id;
            const [west, south, east, north] = c.bbox;
            const tileBounds = [[south, west], [north, east]];
            return (
              <Rectangle 
                key={c.hotspot_id || idx} 
                bounds={tileBounds} 
                pathOptions={{ 
                  color: isSelected ? '#3b82f6' : '#64748b', 
                  weight: isSelected ? 3 : 1, 
                  fillOpacity: isSelected ? 0.2 : 0.05 
                }}
                eventHandlers={{
                  click: () => onSelectHotspot(c)
                }}
              >
                <Tooltip permanent direction="bottom" opacity={0.9} offset={[0, 0]}>
                  <div style={{background: '#0a0d14', color: '#fff', padding: '2px 4px', border: '1px solid #334155', borderRadius: '4px', fontSize: 10, fontFamily: 'monospace'}}>
                    #{String(idx + 1).padStart(2, '0')} {getReadableName(c)}
                  </div>
                </Tooltip>
              </Rectangle>
            );
          })}
        </MapContainer>
        {stage === 'acquiring' && (
          <div className={styles.loadingContainer} style={{position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(10, 13, 20, 0.7)', zIndex: 1000}}>
            <div className={styles.loadingSpinner}></div>
            <div className={styles.loadingText}>Acquiring Multi-Temporal Imagery Scenes...</div>
          </div>
        )}
      </div>
    );
  };

  return (
    <section className={styles.viewerStage}>
      <div className={styles.stageTopBar}>
        <div className={styles.locationTitleGroup}>
          <h2 className={styles.locationHeading}>
            {selectedCandidate ? getReadableName(selectedCandidate) : (selectedHotspot?.location_name || 'GLOBAL COVERAGE')}
          </h2>
          <span className={styles.locationSub}>
            {selectedCandidate ? 'Candidate Region' : (selectedHotspot ? `${selectedHotspot.lat?.toFixed(4)}, ${selectedHotspot.lng?.toFixed(4)}` : 'Awaiting Query')}
          </span>
        </div>

        <div className={styles.resolutionToggleGroup}>
          <button
            type="button"
            className={`${styles.resTab} ${selectedTier === '10m' ? styles.resTabActive : ''}`}
            onClick={() => setSelectedTier('10m')}
          >
            🛰️ Sentinel-2 (10m)
          </button>
          <button
            type="button"
            className={`${styles.resTab} ${selectedTier === '0.6m' ? styles.resTabActive : ''}`}
            onClick={() => setSelectedTier('0.6m')}
          >
            🔍 High-Res Aerial (~0.6m)
          </button>
        </div>

        <div className={styles.modeToggleGroup}>
          <button type="button" className={`${styles.modeTab} ${viewMode === 'raw' ? styles.modeTabActive : ''}`} onClick={() => setViewMode('raw')} disabled={!isAnalysisComplete}>↔️ Split Slider</button>
          <button type="button" className={`${styles.modeTab} ${viewMode === 'color' ? styles.modeTabActive : ''}`} onClick={() => setViewMode('color')} disabled={!isAnalysisComplete}>🔴 Optical Change</button>
          <button type="button" className={`${styles.modeTab} ${viewMode === 'ssim' ? styles.modeTabActive : ''}`} onClick={() => setViewMode('ssim')} disabled={!isAnalysisComplete}>🔲 SSIM Matrix</button>
          <button type="button" className={`${styles.modeTab} ${viewMode === 'veg' ? styles.modeTabActive : ''}`} onClick={() => setViewMode('veg')} disabled={!isAnalysisComplete}>🌿 Vegetation</button>
        </div>
      </div>

      <div
        className={styles.canvasContainer}
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {(!hasImagery && (stage === 'idle' || stage === 'error')) && renderEmptyState()}
        {stage === 'searching' && renderLoadingState('Understanding Semantic Query...')}
        
        {showMap && renderMapState()}
        
        {(hasImagery && !showMap) && (
          <>
            <canvas ref={canvasBeforeRef} className={styles.satelliteCanvas} />
            <div className={styles.afterClippedContainer} style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}>
              <canvas ref={canvasAfterRef} className={styles.satelliteCanvas} />
            </div>

            <div
              className={styles.sliderDivider}
              style={{ left: `${sliderPos}%` }}
              onPointerDown={handleSliderPointerDown}
              onTouchStart={handleSliderTouchStart}
            >
              <div className={styles.sliderGrip}><span>↔</span></div>
            </div>

            <div className={styles.labelBefore}>
              <span className={styles.dateTag}>📅 BASELINE: {selectedHotspot?.before_date || '2022'}</span>
            </div>

            <div className={styles.labelAfter}>
              <span className={styles.dateTag}>📅 CURRENT: {selectedHotspot?.after_date || '2025'}</span>
            </div>

            <div className={styles.floatingControls}>
              <div className={styles.zoomPills}>
                <button type="button" className={styles.ctrlBtn} onClick={handleZoomIn}>+</button>
                <span className={styles.zoomVal}>{zoomLevel.toFixed(1)}x</span>
                <button type="button" className={styles.ctrlBtn} onClick={handleZoomOut}>-</button>
                <button type="button" className={styles.ctrlBtn} onClick={handleResetZoom}>Reset</button>
              </div>
              <button
                type="button"
                className={`${styles.boxToggleBtn} ${showHotspotBoxes ? styles.boxToggleActive : ''}`}
                onClick={() => setShowHotspotBoxes(!showHotspotBoxes)}
              >
                {showHotspotBoxes ? 'Hide Parcels' : 'Show Parcels'}
              </button>
            </div>
            
            {stage === 'analyzing' && (
              <div className={styles.scanningOverlay}>
                <div className={styles.scanningLine}></div>
                <div className={styles.scanningText}>Performing Change Analysis...</div>
              </div>
            )}
            {stage === 'verifying' && (
              <div className={styles.verifyingOverlay}>
                <div className={styles.verifyingSpinner}></div>
                <div className={styles.verifyingText}>Verifying Semantics using Gemini Flash...</div>
              </div>
            )}
            {stage === 'ranking' && (
              <div className={styles.verifyingOverlay}>
                <div className={styles.verifyingSpinner}></div>
                <div className={styles.verifyingText}>Ranking Evidence...</div>
              </div>
            )}
          </>
        )}
      </div>

      <div className={styles.stageFooter}>
        <span className={styles.coordText}>📍 Center: {cursorCoords}</span>
        <span className={styles.extentText}>
          Monitored Extent: 5.0 km × 5.0 km ({selectedTier === '10m' ? '10m Multi-Spectral' : '~0.6m Sub-Meter Resolution'})
        </span>
      </div>
    </section>
  );
}
