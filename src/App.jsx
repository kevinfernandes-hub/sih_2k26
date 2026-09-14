import React, { useState, useEffect } from 'react';
import { WorkspaceLayout } from './components/WorkspaceLayout/WorkspaceLayout';
import { IntelligenceSidebar } from './components/IntelligenceSidebar/IntelligenceSidebar';
import { RankedIntelligencePanel } from './components/RankedIntelligencePanel/RankedIntelligencePanel';
import { ImageComparisonViewer } from './components/ImageComparisonViewer/ImageComparisonViewer';
import styles from './App.module.css';

export function App() {
  // ── CHANGE SEARCH STATE ──────────────────────────────────────────────────
  const initialChangePipelineState = {
    stage: 'idle',
    // Possible stages: 'idle', 'verifying', 'hotspots_ready', 'investigation', 'error'
    query: '',
    analysisMode: null,
    hotspots: [],
    selectedHotspot: null,
    error: null
  };

  // ── LOCATION SEARCH STATE ────────────────────────────────────────────────
  const initialLocationState = {
    stage: 'idle',
    // Possible stages: 'idle', 'resolving', 'acquiring', 'analyzing', 'ready', 'investigation', 'error'
    locationQuery: '',
    analysisMode: 'general_change',
    resolvedLocation: null,  // { name, short_name, latitude, longitude, bbox }
    hotspot: null,           // single result converted to hotspot shape
    hotspots: [],            // inner change hotspots
    score_breakdown: null,
    error: null
  };

  const [searchMode, setSearchMode] = useState('change'); // 'change' | 'location'
  const [pipelineState, setPipelineState] = useState(initialChangePipelineState);
  const [locationState, setLocationState] = useState(initialLocationState);
  const [indexStatus, setIndexStatus] = useState(null);

  useEffect(() => {
    fetch('/api/retrieval/index/status')
      .then((res) => (res.ok ? res.json() : null))
      .then(setIndexStatus)
      .catch(() => setIndexStatus(null));
  }, []);

  // ── CHANGE SEARCH HANDLERS ───────────────────────────────────────────────
  const setStage = (stage, updates = {}) => {
    setPipelineState(prev => ({ ...prev, stage, ...updates }));
  };

  const handleSearchChange = (val) => {
    setPipelineState(prev => ({ ...prev, query: val }));
  };

  const handleSearch = async (searchQuery) => {
    // Switch to change mode and clear location state
    setSearchMode('change');
    setLocationState(initialLocationState);
    setPipelineState({
      ...initialChangePipelineState,
      stage: 'verifying',
      query: searchQuery
    });

    try {
      const res = await fetch('/api/discover-and-verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, top_k: 3 })
      });

      if (!res.ok) throw new Error('Discovery and Verification Pipeline failed');
      const data = await res.json();

      const hotspots = data.ranked_hotspots || [];
      if (hotspots.length === 0) throw new Error('No verified hotspots found for query.');

      setStage('hotspots_ready', {
        hotspots: hotspots,
        analysisMode: data.mode
      });
    } catch (err) {
      console.error(err);
      setStage('error', { error: err.message || 'Pipeline encountered a critical error.' });
    }
  };

  const handleHotspotSelect = (hotspot) => {
    if (hotspot) {
      setStage('investigation', { selectedHotspot: hotspot });
    } else {
      setStage('hotspots_ready', { selectedHotspot: null });
    }
  };

  const handleBack = (targetStage) => {
    setStage(targetStage);
  };

  // ── LOCATION SEARCH HANDLERS ─────────────────────────────────────────────
  const setLocationStage = (stage, updates = {}) => {
    setLocationState(prev => ({ ...prev, stage, ...updates }));
  };

  const handleLocationQueryChange = (val) => {
    setLocationState(prev => ({ ...prev, locationQuery: val }));
  };

  const handleLocationAnalysisModeChange = (mode) => {
    setLocationState(prev => ({ ...prev, analysisMode: mode }));
  };

  const handleLocationSearch = async (locationQuery, analysisMode) => {
    // Switch to location mode and clear change state
    setSearchMode('location');
    setPipelineState(initialChangePipelineState);
    setLocationState({
      ...initialLocationState,
      locationQuery,
      analysisMode,
      stage: 'resolving'
    });

    try {
      // Step 1: Resolving
      setLocationStage('resolving', { locationQuery, analysisMode });

      const res = await fetch('/api/location-investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: locationQuery,
          analysis_mode: analysisMode,
          before_date: '2022-02-22',
          after_date: '2025-02-26'
        })
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        const detail = errBody.detail || {};
        if (detail.error === 'OUTSIDE_COVERAGE') {
          throw new Error(`LOCATION OUTSIDE CURRENT COVERAGE\n\n"${locationQuery}" is not within Nagpur, Maharashtra.\nCurrent coverage: NAGPUR, MAHARASHTRA, INDIA`);
        }
        throw new Error(detail.message || 'Location investigation failed');
      }

      const data = await res.json();

      // Build a hotspot-shaped object for the existing ImageComparisonViewer
      const hotspot = {
        hotspot_id: `LOC-${data.location.short_name.toUpperCase().replace(/\s+/g, '-')}`,
        location_name: data.location.name,
        lat: data.location.latitude,
        lng: data.location.longitude,
        bbox: data.location.bbox,
        before_image: data.before_image,
        after_image: data.after_image,
        color_overlay: data.color_overlay,
        ssim_overlay: data.ssim_overlay,
        tiers: data.tiers,
        hotspots: data.hotspots,
        evidence_score: data.evidence_score,
        semantic_score: 100,  // Location mode: directly resolved
        analysis_metrics: data.analysis_metrics,
        score_breakdown: data.score_breakdown,
        mode: data.analysis_mode,
        cache_hit: data.cache_hit
      };

      setLocationState(prev => ({
        ...prev,
        stage: 'ready',
        resolvedLocation: data.location,
        hotspot,
        hotspots: data.hotspots || [],
        score_breakdown: data.score_breakdown,
        analysisMode: data.analysis_mode,
        before_date: data.before_date,
        after_date: data.after_date,
        error: null
      }));
    } catch (err) {
      console.error(err);
      setLocationStage('error', { error: err.message || 'Location investigation failed.' });
    }
  };

  const handleLocationHotspotSelect = (hotspot) => {
    if (hotspot) {
      setLocationStage('investigation', { hotspot });
    } else {
      setLocationStage('ready', {});
    }
  };

  // ── DERIVE ACTIVE HOTSPOT FOR VIEWER ─────────────────────────────────────
  // The ImageComparisonViewer always needs a selectedHotspot to render imagery.
  // In location mode, the "hotspot" IS the resolved location result.
  const activePipelineState = searchMode === 'change'
    ? pipelineState
    : {
        stage: locationState.stage === 'ready' ? 'investigation'
          : locationState.stage === 'investigation' ? 'investigation'
          : locationState.stage,
        query: locationState.locationQuery,
        analysisMode: locationState.analysisMode,
        hotspots: locationState.hotspots,
        selectedHotspot: locationState.hotspot,
        error: locationState.error
      };

  return (
    <div className={styles.appContainer}>
      <WorkspaceLayout
        leftPanel={
          <IntelligenceSidebar
            searchMode={searchMode}
            pipelineState={pipelineState}
            locationState={locationState}
            onSearchChange={handleSearchChange}
            onRequestSearch={handleSearch}
            onLocationQueryChange={handleLocationQueryChange}
            onLocationAnalysisModeChange={handleLocationAnalysisModeChange}
            onRequestLocationSearch={handleLocationSearch}
          />
        }
        centerPanel={
          <ImageComparisonViewer
            pipelineState={activePipelineState}
            searchMode={searchMode}
            onSelectHotspot={searchMode === 'change' ? handleHotspotSelect : handleLocationHotspotSelect}
          />
        }
        rightPanel={
          <RankedIntelligencePanel
            searchMode={searchMode}
            pipelineState={pipelineState}
            locationState={locationState}
            onSelectHotspot={searchMode === 'change' ? handleHotspotSelect : handleLocationHotspotSelect}
            onBack={handleBack}
          />
        }
      />

      <div className={styles.systemStatusBar}>
        <span className={styles.systemStatusLabel}>EARTHWATCH ENGINE v2</span>
        <span>
          {indexStatus ? `${indexStatus.indexed_scenes} Scenes · ${indexStatus.indexed_tiles} Tiles` : 'Connecting...'}
        </span>
        <span>
          MODE: {searchMode.toUpperCase()} · STATUS: {(searchMode === 'change' ? pipelineState.stage : locationState.stage).toUpperCase()}
        </span>
      </div>
    </div>
  );
}

export default App;
