import React from 'react';
import styles from './IntelligenceSidebar.module.css';

const SUGGESTED_QUERIES = [
  'vegetation loss',
  'new construction',
  'water body reduction',
  'urban expansion'
];

const STAGES = [
  { id: 'query', label: 'QUERY UNDERSTOOD' },
  { id: 'retrieval', label: 'SEMANTIC RETRIEVAL' },
  { id: 'verifying', label: 'VERIFYING SATELLITE DATA' },
  { id: 'analysis', label: 'CHANGE ANALYSIS & FUSION' },
  { id: 'results', label: 'HOTSPOTS RANKED' }
];

export function IntelligenceSidebar({ 
  pipelineState, 
  onSearchChange, 
  onRequestSearch 
}) {
  const { query, stage, analysisMode, error } = pipelineState;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && stage !== 'verifying') {
      onRequestSearch(query);
    }
  };

  const getStageStatus = (stageId) => {
    let currentStageIndex = -1;
    if (stage === 'verifying') {
      // Since it's all automated in one API call, we just light up the first few as active
      if (stageId === 'query' || stageId === 'retrieval' || stageId === 'verifying' || stageId === 'analysis') return 'active';
      return 'pending';
    }
    if (['hotspots_ready', 'investigation'].includes(stage)) currentStageIndex = 4;

    const stageIndex = STAGES.findIndex(s => s.id === stageId);
    
    if (currentStageIndex === -1) return 'pending';
    if (stageIndex <= currentStageIndex) return 'completed';
    return 'pending';
  };

  const renderIcon = (status) => {
    if (status === 'completed') return '✓';
    if (status === 'active') return '●';
    return '○';
  };

  const getStageDesc = (stageId, status) => {
    if (status === 'pending') return 'pending';
    
    switch(stageId) {
      case 'query': return analysisMode ? analysisMode.replace('_', ' ') : (status === 'active' ? 'parsing semantic intent...' : 'query parsed');
      case 'retrieval': return status === 'active' ? 'retrieving deduplicated regions...' : 'candidates retrieved';
      case 'verifying': return status === 'active' ? 'acquiring live scenes...' : 'imagery acquired';
      case 'analysis': return status === 'active' ? 'analyzing and fusing evidence...' : 'analysis complete';
      case 'results': return 'hotspots available for investigation';
      default: return '';
    }
  };

  return (
    <aside className={styles.sidebar}>
      <header className={styles.header}>
        <h1 className={styles.title}>EARTHWATCH</h1>
        <div className={styles.subtitle}>SATELLITE INTELLIGENCE</div>
        <div className={styles.subtitle} style={{textTransform: 'none', marginTop: 4, color: 'var(--text-faint)'}}>
          Semantic retrieval + multi-temporal change analysis
        </div>
      </header>

      <section className={styles.searchSection}>
        <span className={styles.searchLabel}>Search Satellite Intelligence</span>
        <form className={styles.form} onSubmit={handleSubmit}>
          <input
            className={styles.input}
            value={query}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Describe the change you're looking for..."
            disabled={stage === 'searching' || stage === 'acquiring' || stage === 'analyzing'}
          />
          <button 
            className={styles.searchButton} 
            type="submit" 
            disabled={!query.trim() || stage === 'searching' || stage === 'acquiring' || stage === 'analyzing'}
          >
            ANALYZE QUERY
          </button>
        </form>

        {(stage === 'idle' || stage === 'error') && (
          <div className={styles.suggestions}>
            {SUGGESTED_QUERIES.map(q => (
              <button 
                key={q} 
                className={styles.suggestionBtn}
                onClick={() => {
                  onSearchChange(q);
                  onRequestSearch(q);
                }}
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </section>

      {error && (
        <div style={{color: 'var(--status-critical)', fontSize: 12, marginBottom: 24, padding: 12, background: 'var(--status-critical-bg)', borderRadius: 6}}>
          {error}
        </div>
      )}

      {stage !== 'idle' && (
        <>
          {analysisMode && (
            <div className={styles.queryType}>
              <div className={styles.queryTypeLabel}>Analysis Mode</div>
              <div className={styles.queryTypeValue}>{analysisMode.replace('_', ' ').toUpperCase()}</div>
            </div>
          )}

          <div className={styles.timeline}>
            {STAGES.map((s) => {
              const status = getStageStatus(s.id);
              if (stage === 'error' && status === 'pending') return null;

              return (
                <div key={s.id} className={`${styles.timelineItem} ${styles[status]}`}>
                  <div className={`${styles.timelineIcon} ${styles[status]}`}>
                    {renderIcon(status)}
                  </div>
                  <div className={styles.timelineContent}>
                    <div className={styles.timelineTitle}>{s.label}</div>
                    <div className={styles.timelineDesc}>{getStageDesc(s.id, status)}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </aside>
  );
}
