import React, { useState } from 'react';
import styles from './IntelligenceSidebar.module.css';

const CHANGE_EXAMPLES = ['vegetation loss', 'new construction', 'water body reduction', 'urban expansion'];
const LOCATION_EXAMPLES = ['MIHAN', 'Hingna', 'Nandanvan', 'Sitabuldi', 'VNIT', 'Kamptee Road'];

const ANALYSIS_MODES = [
  { id: 'general_change',    label: 'GENERAL',     icon: '◎' },
  { id: 'vegetation_change', label: 'VEGETATION',  icon: '🌿' },
  { id: 'built_up_change',   label: 'BUILT-UP',    icon: '🏗' },
  { id: 'water_change',      label: 'WATER',       icon: '💧' }
];

const CHANGE_STAGES = [
  { id: 'query',     label: 'QUERY UNDERSTOOD' },
  { id: 'retrieval', label: 'SEMANTIC RETRIEVAL' },
  { id: 'verifying', label: 'VERIFYING SATELLITE DATA' },
  { id: 'analysis',  label: 'CHANGE ANALYSIS & FUSION' },
  { id: 'results',   label: 'HOTSPOTS RANKED' }
];

const LOCATION_STAGES = [
  { id: 'resolving',  label: 'RESOLVING LOCATION' },
  { id: 'acquiring',  label: 'ACQUIRING SATELLITE DATA' },
  { id: 'analyzing',  label: 'TEMPORAL ANALYSIS' },
  { id: 'ready',      label: 'RESULTS READY' }
];

export function IntelligenceSidebar({
  searchMode,
  pipelineState,
  locationState,
  onSearchChange,
  onRequestSearch,
  onLocationQueryChange,
  onLocationAnalysisModeChange,
  onRequestLocationSearch
}) {
  const { query, stage, analysisMode, error } = pipelineState;
  const locStage = locationState.stage;
  const locError = locationState.error;

  const handleChangeSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && stage !== 'verifying') onRequestSearch(query);
  };

  const handleLocationSubmit = (e) => {
    e.preventDefault();
    const q = locationState.locationQuery.trim();
    if (q && locStage !== 'resolving' && locStage !== 'acquiring' && locStage !== 'analyzing') {
      onRequestLocationSearch(q, locationState.analysisMode);
    }
  };

  // ── CHANGE SEARCH TIMELINE HELPERS ──────────────────────────────────────
  const getChangeStageStatus = (stageId) => {
    if (stage === 'verifying') {
      if (['query', 'retrieval', 'verifying', 'analysis'].includes(stageId)) return 'active';
      return 'pending';
    }
    if (['hotspots_ready', 'investigation'].includes(stage)) {
      const idx = CHANGE_STAGES.findIndex(s => s.id === stageId);
      return idx <= 4 ? 'completed' : 'pending';
    }
    return 'pending';
  };

  const getChangeStageDesc = (stageId, status) => {
    if (status === 'pending') return 'pending';
    switch (stageId) {
      case 'query':     return analysisMode ? analysisMode.replace('_', ' ') : (status === 'active' ? 'parsing intent...' : 'query parsed');
      case 'retrieval': return status === 'active' ? 'retrieving Nagpur observations...' : 'candidates retrieved';
      case 'verifying': return status === 'active' ? 'acquiring live Sentinel-2 scenes...' : 'imagery acquired';
      case 'analysis':  return status === 'active' ? 'fusing spectral evidence...' : 'analysis complete';
      case 'results':   return 'hotspots available for investigation';
      default: return '';
    }
  };

  // ── LOCATION SEARCH TIMELINE HELPERS ────────────────────────────────────
  const getLocStageStatus = (stageId) => {
    const order = ['resolving', 'acquiring', 'analyzing', 'ready'];
    const current = order.indexOf(locStage);
    const target = order.indexOf(stageId);
    if (locStage === 'error') return target === 0 ? 'active' : 'pending';
    if (current === -1) return 'pending';
    if (target < current) return 'completed';
    if (target === current) return 'active';
    return 'pending';
  };

  const getLocStageDesc = (stageId, status) => {
    if (status === 'pending') return 'pending';
    switch (stageId) {
      case 'resolving':  return status === 'active' ? 'geocoding location...' : `resolved: ${locationState.resolvedLocation?.short_name || ''}`;
      case 'acquiring':  return status === 'active' ? 'fetching Sentinel-2 pair...' : 'imagery acquired';
      case 'analyzing':  return status === 'active' ? 'running change analysis...' : 'analysis complete';
      case 'ready':      return locationState.cache_hit ? 'results ready (cache hit)' : 'results ready (live acquisition)';
      default: return '';
    }
  };

  const renderIcon = (status) => {
    if (status === 'completed') return '✓';
    if (status === 'active') return '●';
    return '○';
  };

  const isLocBusy = ['resolving', 'acquiring', 'analyzing'].includes(locStage);
  const isChangeBusy = stage === 'verifying';

  return (
    <aside className={styles.sidebar}>
      {/* ── HEADER ────────────────────────────────────────────────────── */}
      <header className={styles.header}>
        <h1 className={styles.title}>EARTHWATCH</h1>
        <div className={styles.subtitle}>SATELLITE INTELLIGENCE</div>
        <div className={styles.subtitle} style={{ textTransform: 'none', marginTop: 4, color: 'var(--text-faint)' }}>
          Semantic retrieval + multi-temporal change analysis
        </div>
      </header>

      {/* ── CHANGE SEARCH ─────────────────────────────────────────────── */}
      <section className={`${styles.searchSection} ${searchMode === 'change' ? styles.activeSection : styles.inactiveSection}`}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionTag}>CHANGE-FIRST</span>
          <span className={styles.sectionTitle}>CHANGE SEARCH</span>
        </div>
        <span className={styles.searchLabel}>What change are you looking for?</span>
        <form className={styles.form} onSubmit={handleChangeSubmit}>
          <input
            className={styles.input}
            value={query}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="vegetation loss, new construction..."
            disabled={isChangeBusy}
          />
          <button
            className={styles.searchButton}
            type="submit"
            disabled={!query.trim() || isChangeBusy}
          >
            {isChangeBusy ? 'ANALYZING...' : 'ANALYZE CHANGE'}
          </button>
        </form>

        {(stage === 'idle' || stage === 'error') && (
          <div className={styles.suggestions}>
            {CHANGE_EXAMPLES.map(q => (
              <button
                key={q}
                className={styles.suggestionBtn}
                onClick={() => { onSearchChange(q); onRequestSearch(q); }}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {error && (
          <div className={styles.errorBox}>{error}</div>
        )}

        {stage !== 'idle' && !error && (
          <div className={styles.timeline}>
            {CHANGE_STAGES.map((s) => {
              const status = getChangeStageStatus(s.id);
              if (stage === 'error' && status === 'pending') return null;
              return (
                <div key={s.id} className={`${styles.timelineItem} ${styles[status]}`}>
                  <div className={`${styles.timelineIcon} ${styles[status]}`}>{renderIcon(status)}</div>
                  <div className={styles.timelineContent}>
                    <div className={styles.timelineTitle}>{s.label}</div>
                    <div className={styles.timelineDesc}>{getChangeStageDesc(s.id, status)}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* ── DIVIDER ───────────────────────────────────────────────────── */}
      <div className={styles.sectionDivider}>
        <span className={styles.orLabel}>OR</span>
      </div>

      {/* ── LOCATION SEARCH ───────────────────────────────────────────── */}
      <section className={`${styles.searchSection} ${searchMode === 'location' ? styles.activeSection : styles.inactiveSection}`}>
        <div className={styles.sectionHeader}>
          <span className={`${styles.sectionTag} ${styles.locationTag}`}>LOCATION-FIRST</span>
          <span className={styles.sectionTitle}>LOCATION SEARCH</span>
        </div>
        <span className={styles.searchLabel}>Where do you want to investigate?</span>
        <form className={styles.form} onSubmit={handleLocationSubmit}>
          <input
            className={styles.input}
            value={locationState.locationQuery}
            onChange={(e) => onLocationQueryChange(e.target.value)}
            placeholder="Search a place in Nagpur..."
            disabled={isLocBusy}
          />

          {/* Analysis mode selector */}
          <div className={styles.modeGrid}>
            {ANALYSIS_MODES.map(m => (
              <button
                key={m.id}
                type="button"
                className={`${styles.modeBtn} ${locationState.analysisMode === m.id ? styles.modeBtnActive : ''}`}
                onClick={() => onLocationAnalysisModeChange(m.id)}
                disabled={isLocBusy}
              >
                <span className={styles.modeIcon}>{m.icon}</span>
                <span>{m.label}</span>
              </button>
            ))}
          </div>

          <button
            className={`${styles.searchButton} ${styles.locationButton}`}
            type="submit"
            disabled={!locationState.locationQuery.trim() || isLocBusy}
          >
            {isLocBusy ? 'INVESTIGATING...' : 'INVESTIGATE LOCATION'}
          </button>
        </form>

        {(locStage === 'idle' || locStage === 'error') && !locError && (
          <div className={styles.suggestions}>
            {LOCATION_EXAMPLES.map(q => (
              <button
                key={q}
                className={styles.suggestionBtn}
                onClick={() => {
                  onLocationQueryChange(q);
                  onRequestLocationSearch(q, locationState.analysisMode);
                }}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {locError && (
          <div className={styles.errorBox} style={{ whiteSpace: 'pre-line' }}>{locError}</div>
        )}

        {locStage !== 'idle' && !locError && (
          <div className={styles.timeline}>
            {LOCATION_STAGES.map((s) => {
              const status = getLocStageStatus(s.id);
              if (locStage === 'error' && status === 'pending') return null;
              return (
                <div key={s.id} className={`${styles.timelineItem} ${styles[status]}`}>
                  <div className={`${styles.timelineIcon} ${styles[status]}`}>{renderIcon(status)}</div>
                  <div className={styles.timelineContent}>
                    <div className={styles.timelineTitle}>{s.label}</div>
                    <div className={styles.timelineDesc}>{getLocStageDesc(s.id, status)}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Show resolved location info */}
        {locationState.resolvedLocation && (locStage === 'ready' || locStage === 'investigation') && (
          <div className={styles.resolvedCard}>
            <div className={styles.resolvedName}>{locationState.resolvedLocation.short_name}</div>
            <div className={styles.resolvedSub}>Nagpur, Maharashtra</div>
            <div className={styles.resolvedCoords}>
              {locationState.resolvedLocation.latitude?.toFixed(4)}° N,{' '}
              {locationState.resolvedLocation.longitude?.toFixed(4)}° E
            </div>
            {locationState.cache_hit !== undefined && (
              <div className={styles.cacheTag}>
                {locationState.hotspot?.cache_hit ? '⚡ CACHE HIT' : '🛰 LIVE ACQUISITION'}
              </div>
            )}
          </div>
        )}
      </section>

      {/* ── COVERAGE NOTICE ───────────────────────────────────────────── */}
      <div className={styles.coverageNotice}>
        <span className={styles.coverageLabel}>NAGPUR COVERAGE</span>
        <span className={styles.coverageValue}>Nagpur, Maharashtra, India</span>
      </div>
    </aside>
  );
}
export default IntelligenceSidebar;
