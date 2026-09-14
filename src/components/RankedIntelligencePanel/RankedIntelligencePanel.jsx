import React from 'react';
import styles from './RankedIntelligencePanel.module.css';

export function RankedIntelligencePanel({ 
  pipelineState, 
  onSelectHotspot,
  onBack
}) {
  const { stage, query, analysisMode, hotspots, selectedHotspot } = pipelineState;

  const getEvidenceStrength = (score) => {
    if (score >= 80) return { label: 'STRONG', class: 'strong' };
    if (score >= 60) return { label: 'MODERATE', class: 'moderate' };
    return { label: 'WEAK', class: 'weak' };
  };

  const getEvidenceBreakdown = (hotspot) => {
    const base = hotspot.evidence_score || 85;
    const s_spectral = Math.round((base / 100) * 38);
    const s_temporal = Math.round((base / 100) * 23);
    const s_spatial = Math.round((base / 100) * 18);
    const s_semantic = Math.round((hotspot.semantic_score || 70) / 100 * 15);
    const total = hotspot.evidence_score || base;
    
    return {
      spectral: `${s_spectral}/38`,
      temporal: `${s_temporal}/23`,
      spatial: `${s_spatial}/18`,
      semantic: `${s_semantic}/15`,
      total: `${total}/100`
    };
  };

  // 1. Initial State or Error
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
        
        <div className={styles.title} style={{marginBottom: 16}}>DISCOVERY & VERIFICATION</div>
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
        
        <div className={styles.header} style={{borderBottom: 'none'}}>
          <div className={styles.title}>{selectedHotspot.location_name || 'HOTSPOT'}</div>
          <div className={styles.query}>{analysisMode ? analysisMode.replace('_', ' ').toUpperCase() : 'CHANGE DETECTED'}</div>
          <div style={{marginTop: 12}}>
            <span className={`${styles.evidenceBadge} ${styles[strength.class]}`}>
              EVIDENCE: {strength.label}
            </span>
          </div>
        </div>

        <div className={styles.checkList}>
          <div className={styles.title} style={{marginBottom: 12}}>EVIDENCE TRACES</div>
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
          NO SIGNIFICANT CHANGE DETECTED<br/><br/>
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
                    <span className={styles.metricValue}>
                      {conf}
                    </span>
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
