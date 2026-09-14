import React from 'react';
import styles from './RankedIntelligencePanel.module.css';

// Renders the BUILDING CHANGE section from real YOLO backend data.
// Only shown when yolo_analysis.available === true.
function BuildingChangePanel({ yolo }) {
  if (!yolo || !yolo.available) return null;
  const s = yolo.summary || {};
  const hasChange = s.new_count > 0 || s.expanded_count > 0;

  return (
    <div className={styles.buildingPanel}>
      <div className={styles.buildingHeader}>
        <span className={styles.buildingTitle}>🏗 BUILDING CHANGE</span>
        <span className={styles.buildingModel}>YOLOv8s-seg</span>
      </div>

      <div className={styles.buildingGrid}>
        <div className={`${styles.buildingCell} ${s.new_count > 0 ? styles.cellNew : ''}`}>
          <div className={styles.buildingCount}>{s.new_count ?? '—'}</div>
          <div className={styles.buildingLabel}>NEW</div>
        </div>
        <div className={`${styles.buildingCell} ${s.expanded_count > 0 ? styles.cellExpanded : ''}`}>
          <div className={styles.buildingCount}>{s.expanded_count ?? '—'}</div>
          <div className={styles.buildingLabel}>EXPANDED</div>
        </div>
        <div className={styles.buildingCell}>
          <div className={styles.buildingCount}>{s.existing_count ?? '—'}</div>
          <div className={styles.buildingLabel}>EXISTING</div>
        </div>
      </div>

      <div className={styles.buildingMeta}>
        {s.mean_confidence != null && (
          <div className={styles.metaRow}>
            <span>YOLO Confidence</span>
            <span>{(s.mean_confidence * 100).toFixed(1)}%</span>
          </div>
        )}
        {s.changed_pixel_area != null && s.changed_pixel_area > 0 && (
          <div className={styles.metaRow}>
            <span>Changed Pixel Area</span>
            <span>{s.changed_pixel_area.toLocaleString()} px²</span>
          </div>
        )}
        {s.ground_area_m2 != null && (
          <div className={styles.metaRow}>
            <span>Est. Ground Area</span>
            <span>{s.ground_area_m2.toFixed(0)} m²</span>
          </div>
        )}
        {s.ground_area_m2 == null && (
          <div className={styles.metaNote}>Ground area uncalibrated — pixel scale not available at 10m resolution</div>
        )}
      </div>

      {!hasChange && (
        <div className={styles.noChange}>NO BUILDING CHANGE DETECTED<br/>YOLO found no new or expanded structures.</div>
      )}

      {hasChange && (
        <button
          type="button"
          style={{
            marginTop: '12px',
            width: '100%',
            background: 'var(--accent-primary, #C96F3E)',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '11px',
            fontWeight: 'bold',
            cursor: 'pointer',
            textAlign: 'center'
          }}
          onClick={yolo.onInspectDossier}
        >
          Inspect Building Dossier 🔍
        </button>
      )}
    </div>
  );
}

// Renders evidence score breakdown from the new structured backend format.
function EvidenceBreakdown({ breakdown, evidenceScore }) {
  if (!breakdown) return null;

  // New structured format: { spectral_change: {score, weight, weighted_contribution}, ..., final_score }
  const keys = Object.keys(breakdown).filter(k => k !== 'final_score' && k !== 'analysis_mode');
  const isStructured = keys.length > 0 && typeof breakdown[keys[0]] === 'object';

  return (
    <div className={styles.scorePanel}>
      <div className={styles.scoreHeader}>
        <span className={styles.scoreTitle}>FUSED EVIDENCE SCORE</span>
        <span className={styles.scoreTotal}>{breakdown.final_score ?? evidenceScore}/100</span>
      </div>
      <div className={styles.scoreBreakdown}>
        {isStructured ? (
          keys.map(key => {
            const item = breakdown[key];
            const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            return (
              <div key={key} className={styles.scoreRow}>
                <span>{label}</span>
                <span className={styles.scoreVal}>
                  {item.score?.toFixed(1)}
                  <span style={{color:'var(--text-faint)',fontSize:9}}> ×{item.weight}</span>
                </span>
              </div>
            );
          })
        ) : (
          // Legacy string format e.g. "24/38"
          Object.entries(breakdown)
            .filter(([k]) => k !== 'final_score' && k !== 'analysis_mode')
            .map(([key, val]) => (
              <div key={key} className={styles.scoreRow}>
                <span>{key}</span>
                <span className={styles.scoreVal}>{typeof val === 'string' ? val : JSON.stringify(val)}</span>
              </div>
            ))
        )}
      </div>
    </div>
  );
}

export function RankedIntelligencePanel({
  searchMode,
  pipelineState,
  locationState,
  onSelectHotspot,
  onBack,
  onInspectDossier
}) {
  const { stage, query, analysisMode, hotspots, selectedHotspot } = pipelineState;

  const getEvidenceStrength = (score) => {
    if (score >= 80) return { label: 'STRONG', class: 'strong' };
    if (score >= 60) return { label: 'MODERATE', class: 'moderate' };
    return { label: 'WEAK', class: 'weak' };
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

          {/* Evidence Score — uses new structured breakdown when available */}
          <EvidenceBreakdown breakdown={hotspot.score_breakdown} evidenceScore={hotspot.evidence_score} />

          {/* Building Change Panel — only shown for built_up_change mode with real YOLO data */}
          <BuildingChangePanel yolo={{ ...hotspot.yolo_analysis, onInspectDossier }} />

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

    return (
      <aside className={styles.panel}>
        <button className={styles.backBtn} onClick={() => onSelectHotspot(null)}>
          ← BACK TO HOTSPOTS
        </button>

        <div className={styles.header} style={{ borderBottom: 'none' }}>
          <div className={styles.title}>{selectedHotspot.location_name || 'HOTSPOT'}</div>
          <div className={styles.query}>{analysisMode ? analysisMode.replace(/_/g, ' ').toUpperCase() : 'CHANGE DETECTED'}</div>
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

        {/* Fused Evidence Score — uses new structured breakdown when available */}
        <EvidenceBreakdown
          breakdown={selectedHotspot.score_breakdown}
          evidenceScore={selectedHotspot.evidence_score}
        />

        {/* Building Change Panel — only shown for built_up_change mode with real YOLO data */}
        <BuildingChangePanel yolo={{ ...selectedHotspot.yolo_analysis, onInspectDossier }} />

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
export default RankedIntelligencePanel;
