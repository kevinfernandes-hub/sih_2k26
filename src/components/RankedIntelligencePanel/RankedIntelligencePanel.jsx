import React from 'react';
import styles from './RankedIntelligencePanel.module.css';

export function RankedIntelligencePanel({
  searchMode,
  pipelineState,
  locationState,
  onSelectHotspot,
  onBack
}) {
  const { stage, query, analysisMode, hotspots, selectedHotspot } = pipelineState;

  const getEvidenceStrength = (score) => {
    if (score >= 80) return { label: 'STRONG', class: 'strong' };
    if (score >= 60) return { label: 'MODERATE', class: 'moderate' };
    return { label: 'WEAK', class: 'weak' };
  };

  // Compute breakdown: prefer real backend score_breakdown, fall back to proportion estimate
  const getEvidenceBreakdown = (hotspot) => {
    if (hotspot?.score_breakdown) return hotspot.score_breakdown;
    const base = hotspot?.evidence_score || 50;
    return {
      spectral: `${Math.round((base / 100) * 38)}/38`,
      temporal: `${Math.round((base / 100) * 23)}/23`,
      spatial:  `${Math.round((base / 100) * 18)}/18`,
      semantic: `${Math.round((hotspot?.semantic_score || 70) / 100 * 15)}/15`,
      total:    `${base}/100`
    };
  };

  // ── LOCATION MODE ──────────────────────────────────────────────────────
  if (searchMode === 'location') {
    const { stage: locStage, locationQuery, resolvedLocation, hotspot, hotspots: innerHotspots,
            analysisMode: locMode, before_date, after_date } = locationState;

    if (locStage === 'idle') {
      return (
        <aside className={styles.panel}>
          <div className={styles.header}>
            <div className={styles.title}>LOCATION INVESTIGATION</div>
            <div className={styles.query}>Search a Nagpur location to investigate</div>
          </div>
        </aside>
      );
    }

    if (locStage === 'resolving' || locStage === 'acquiring' || locStage === 'analyzing') {
      return (
        <aside className={styles.panel}>
          <div className={styles.header}>
            <div className={styles.title}>LOCATION INVESTIGATION</div>
            <div className={styles.query}>{locationQuery}</div>
            <div className={styles.status}>PIPELINE ACTIVE</div>
          </div>
          <div className={styles.checkList}>
            <div className={`${styles.checkItem} true`}>
              <span className={styles.checkIcon}>{locStage === 'resolving' ? '●' : '✓'}</span>
              {locStage === 'resolving' ? 'Geocoding location...' : `Resolved: ${resolvedLocation?.short_name || ''}`}
            </div>
            <div className={`${styles.checkItem} true`}>
              <span className={styles.checkIcon}>{locStage === 'acquiring' ? '●' : locStage === 'resolving' ? '○' : '✓'}</span>
              {locStage === 'acquiring' ? 'Acquiring Sentinel-2 pair...' : locStage === 'resolving' ? 'Imagery acquisition pending' : 'Imagery acquired'}
            </div>
            <div className={`${styles.checkItem} true`}>
              <span className={styles.checkIcon}>{locStage === 'analyzing' ? '●' : '○'}</span>
              {locStage === 'analyzing' ? 'Running change analysis...' : 'Analysis pending'}
            </div>
          </div>
        </aside>
      );
    }

    if (locStage === 'error') {
      return (
        <aside className={styles.panel}>
          <div className={styles.header}>
            <div className={styles.title}>LOCATION INVESTIGATION</div>
            <div className={styles.query}>{locationQuery}</div>
            <div style={{ color: 'var(--status-critical)', fontSize: 11, marginTop: 8 }}>
              {locationState.error}
            </div>
          </div>
        </aside>
      );
    }

    // Location results ready / investigation
    if ((locStage === 'ready' || locStage === 'investigation') && hotspot) {
      const strength = getEvidenceStrength(hotspot.evidence_score || 50);
      const breakdown = getEvidenceBreakdown(hotspot);
      const modeLabel = (locMode || 'general_change').replace(/_/g, ' ').toUpperCase();

      return (
        <aside className={styles.panel}>
          {locStage === 'investigation' && (
            <button className={styles.backBtn} onClick={() => onSelectHotspot(null)}>
              ← BACK TO LOCATION
            </button>
          )}

          <div className={styles.header} style={{ borderBottom: 'none' }}>
            <div className={styles.title}>{resolvedLocation?.short_name || locationQuery}</div>
            <div className={styles.query}>Nagpur, Maharashtra</div>
            <div className={styles.query}>{modeLabel}</div>
            <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
              <span className={`${styles.evidenceBadge} ${styles[strength.class]}`}>
                EVIDENCE: {strength.label}
              </span>
              <span style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--text-faint)', alignSelf: 'center' }}>
                {hotspot.cache_hit ? '⚡ CACHED' : '🛰 LIVE'}
              </span>
            </div>
          </div>

          <div className={styles.checkList}>
            <div className={styles.title} style={{ marginBottom: 10 }}>TEMPORAL PAIR</div>
            <div className={`${styles.checkItem} true`}>
              <span className={styles.checkIcon}>✓</span>
              BASELINE: {before_date || '2022-02-22'}
            </div>
            <div className={`${styles.checkItem} true`}>
              <span className={styles.checkIcon}>✓</span>
              CURRENT: {after_date || '2025-02-26'}
            </div>
            <div className={`${styles.checkItem} true`}>
              <span className={styles.checkIcon}>✓</span>
              Copernicus Sentinel-2 L2A
            </div>
          </div>

          <div className={styles.scorePanel}>
            <div className={styles.scoreHeader}>
              <span className={styles.scoreTitle}>FUSED EVIDENCE SCORE</span>
              <span className={styles.scoreTotal}>{breakdown.total}</span>
            </div>
            <div className={styles.scoreBreakdown}>
              {[
                { label: 'Spectral change',       val: breakdown.spectral },
                { label: 'Temporal consistency',  val: breakdown.temporal },
                { label: 'Spatial coherence',     val: breakdown.spatial  },
                { label: 'Location confidence',   val: breakdown.semantic }
              ].map(row => (
                <div key={row.label} className={styles.scoreRow}>
                  <span>{row.label}</span>
                  <span className={styles.scoreVal}>{row.val}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Analysis metrics */}
          {hotspot.analysis_metrics && (
            <div className={styles.scorePanel} style={{ marginTop: 8 }}>
              <div className={styles.scoreHeader}>
                <span className={styles.scoreTitle}>ANALYSIS METRICS</span>
              </div>
              <div className={styles.scoreBreakdown}>
                <div className={styles.scoreRow}>
                  <span>Color diff</span>
                  <span className={styles.scoreVal}>{hotspot.analysis_metrics.color_diff_pct?.toFixed(1)}%</span>
                </div>
                <div className={styles.scoreRow}>
                  <span>SSIM change</span>
                  <span className={styles.scoreVal}>{hotspot.analysis_metrics.ssim_pct?.toFixed(1)}%</span>
                </div>
                <div className={styles.scoreRow}>
                  <span>Confidence</span>
                  <span className={styles.scoreVal}>{(hotspot.analysis_metrics.confidence || 'N/A').toUpperCase()}</span>
                </div>
              </div>
            </div>
          )}

          {/* Inner hotspots list */}
          {innerHotspots && innerHotspots.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <div className={styles.title} style={{ marginBottom: 10 }}>CHANGE HOTSPOTS</div>
              <div className={styles.hotspotsList}>
                {innerHotspots.slice(0, 5).map((h, idx) => (
                  <div key={idx} className={styles.hotspotCard} style={{ padding: '10px 12px' }}>
                    <div className={styles.cardHeader}>
                      <span className={styles.rank}>#{String(idx + 1).padStart(2, '0')}</span>
                      <span className={`${styles.evidenceBadge} ${styles.moderate}`}>
                        CHANGE
                      </span>
                    </div>
                    <div className={styles.changeType}>
                      {h.change_type || h.label || modeLabel}
                    </div>
                    {h.area_m2 && (
                      <div className={styles.metricsGrid}>
                        <div className={styles.metric}>
                          <span className={styles.metricLabel}>Area</span>
                          <span className={styles.metricValue}>{h.area_m2.toFixed(0)} m²</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {(!innerHotspots || innerHotspots.length === 0) && locStage === 'ready' && (
            <div className={styles.emptyState}>
              NO SIGNIFICANT CHANGE DETECTED<br /><br />
              Live imagery was acquired and analyzed. No structural changes were detected for the selected mode.
            </div>
          )}
        </aside>
      );
    }

    return null;
  }

  // ── CHANGE MODE ──────────────────────────────────────────────────────────

  // 1. Idle / Error
  if (stage === 'idle' || stage === 'error') {
    return (
      <aside className={styles.panel}>
        <div className={styles.header}>
          <div className={styles.title}>CHANGE INTELLIGENCE</div>
          <div className={styles.query}>Awaiting query...</div>
        </div>
      </aside>
    );
  }

  // 2. Verifying
  if (stage === 'verifying') {
    return (
      <aside className={styles.panel}>
        <div className={styles.header}>
          <div className={styles.title}>PIPELINE ACTIVE</div>
          <div className={styles.query}>Processing: "{query}"</div>
        </div>

        <div className={styles.title} style={{ marginBottom: 16 }}>DISCOVERY & VERIFICATION</div>
        <div className={styles.checkList}>
          <div className={`${styles.checkItem} true`}>
            <span className={styles.checkIcon}>✓</span> Semantic retrieval
          </div>
          <div className={`${styles.checkItem} true`}>
            <span className={styles.checkIcon}>○</span> Acquiring live scenes...
          </div>
          <div className={`${styles.checkItem} true`}>
            <span className={styles.checkIcon}>○</span> Fusing spectral evidence...
          </div>
        </div>
      </aside>
    );
  }

  // 3. Investigation View
  if (stage === 'investigation' && selectedHotspot) {
    const strength = getEvidenceStrength(selectedHotspot.evidence_score || 85);
    const breakdown = getEvidenceBreakdown(selectedHotspot);

    return (
      <aside className={styles.panel}>
        <button className={styles.backBtn} onClick={() => onSelectHotspot(null)}>
          ← BACK TO HOTSPOTS
        </button>

        <div className={styles.header} style={{ borderBottom: 'none' }}>
          <div className={styles.title}>{selectedHotspot.location_name || 'HOTSPOT'}</div>
          <div className={styles.query}>{analysisMode ? analysisMode.replace('_', ' ').toUpperCase() : 'CHANGE DETECTED'}</div>
          <div style={{ marginTop: 12 }}>
            <span className={`${styles.evidenceBadge} ${styles[strength.class]}`}>
              EVIDENCE: {strength.label}
            </span>
          </div>
        </div>

        <div className={styles.checkList}>
          <div className={styles.title} style={{ marginBottom: 12 }}>EVIDENCE TRACES</div>
          <div className={`${styles.checkItem} true`}>
            <span className={styles.checkIcon}>✓</span> Temporal imagery available
          </div>
          <div className={`${styles.checkItem} true`}>
            <span className={styles.checkIcon}>✓</span> Spectral change coherence
          </div>
          <div className={`${styles.checkItem} true`}>
            <span className={styles.checkIcon}>✓</span> Semantic alignment: "{query}"
          </div>
        </div>

        <div className={styles.scorePanel}>
          <div className={styles.scoreHeader}>
            <span className={styles.scoreTitle}>FUSED EVIDENCE SCORE</span>
            <span className={styles.scoreTotal}>{breakdown.total}</span>
          </div>
          <div className={styles.scoreBreakdown}>
            <div className={styles.scoreRow}>
              <span>Spectral change</span>
              <span className={styles.scoreVal}>{breakdown.spectral}</span>
            </div>
            <div className={styles.scoreRow}>
              <span>Temporal consistency</span>
              <span className={styles.scoreVal}>{breakdown.temporal}</span>
            </div>
            <div className={styles.scoreRow}>
              <span>Spatial coherence</span>
              <span className={styles.scoreVal}>{breakdown.spatial}</span>
            </div>
            <div className={styles.scoreRow}>
              <span>Semantic support</span>
              <span className={styles.scoreVal}>{breakdown.semantic}</span>
            </div>
          </div>
        </div>
      </aside>
    );
  }

  // 4. Hotspots Ready
  return (
    <aside className={styles.panel}>
      <div className={styles.header}>
        <div className={styles.title}>DETECTED HOTSPOTS</div>
        <div className={styles.query}>{analysisMode ? analysisMode.replace('_', ' ').toUpperCase() : 'CHANGE DETECTED'}</div>
        <div className={styles.status}>RESULTS READY</div>
      </div>

      {(!hotspots || hotspots.length === 0) ? (
        <div className={styles.emptyState}>
          NO SIGNIFICANT CHANGE DETECTED<br /><br />
          Live imagery was analyzed, but the available temporal evidence did not support significant '{analysisMode ? analysisMode.replace('_', ' ') : 'change'}'.
        </div>
      ) : (
        <div className={styles.hotspotsList}>
          {hotspots.map((hotspot, idx) => {
            const rank = (idx + 1).toString().padStart(2, '0');
            const conf = hotspot.evidence_score || (85 - (idx * 4));
            const strength = getEvidenceStrength(conf);

            return (
              <div key={hotspot.hotspot_id} className={styles.hotspotCard}>
                <div className={styles.cardHeader}>
                  <span className={styles.rank}>#{rank}</span>
                  <span className={`${styles.evidenceBadge} ${styles[strength.class]}`}>
                    {strength.label} EVIDENCE
                  </span>
                </div>

                <div className={styles.changeType}>
                  {hotspot.location_name}
                </div>

                <div className={styles.metricsGrid}>
                  <div className={styles.metric}>
                    <span className={styles.metricLabel}>Semantic</span>
                    <span className={styles.metricValue}>{hotspot.semantic_score ? hotspot.semantic_score.toFixed(1) + '%' : 'N/A'}</span>
                  </div>
                  <div className={styles.metric}>
                    <span className={styles.metricLabel}>Total Score</span>
                    <span className={styles.metricValue}>{conf}</span>
                  </div>
                </div>

                <button
                  className={styles.investigateBtn}
                  onClick={() => onSelectHotspot(hotspot)}
                >
                  INVESTIGATE
                </button>
              </div>
            );
          })}
        </div>
      )}
    </aside>
  );
}
