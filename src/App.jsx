import React, { useState, useEffect } from 'react';
import { WorkspaceLayout } from './components/WorkspaceLayout/WorkspaceLayout';
import { IntelligenceSidebar } from './components/IntelligenceSidebar/IntelligenceSidebar';
import { RankedIntelligencePanel } from './components/RankedIntelligencePanel/RankedIntelligencePanel';
import { ImageComparisonViewer } from './components/ImageComparisonViewer/ImageComparisonViewer';
import styles from './App.module.css';

export function App() {
  const initialState = {
    stage: 'idle', 
    // Possible stages: 'idle', 'verifying', 'hotspots_ready', 'investigation', 'error'
    query: '',
    analysisMode: null,
    hotspots: [],
    selectedHotspot: null,
    error: null
  };

  const [pipelineState, setPipelineState] = useState(initialState);
  const [indexStatus, setIndexStatus] = useState(null);

  useEffect(() => {
    fetch('/api/retrieval/index/status')
      .then((res) => (res.ok ? res.json() : null))
      .then(setIndexStatus)
      .catch(() => setIndexStatus(null));
  }, []);

  const setStage = (stage, updates = {}) => {
    setPipelineState(prev => ({ ...prev, stage, ...updates }));
  };

  const handleSearchChange = (val) => {
    setPipelineState(prev => ({ ...prev, query: val }));
  };

  // FULL AUTOMATED PIPELINE: Search -> Retrieval -> Verify -> Analyze -> Extract Hotspots -> Rank
  const handleSearch = async (searchQuery) => {
    // Clear all previous state completely!
    setPipelineState({
      ...initialState,
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

  // Investigate Hotspot (Toggle 10m vs 0.6m)
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

  return (
    <div className={styles.appContainer}>
      <WorkspaceLayout 
        leftPanel={
          <IntelligenceSidebar 
            pipelineState={pipelineState}
            onSearchChange={handleSearchChange}
            onRequestSearch={handleSearch}
          />
        }
        centerPanel={
          <ImageComparisonViewer 
            pipelineState={pipelineState}
            onSelectHotspot={handleHotspotSelect}
          />
        }
        rightPanel={
          <RankedIntelligencePanel 
            pipelineState={pipelineState}
            onSelectHotspot={handleHotspotSelect}
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
          STATUS: {pipelineState.stage.toUpperCase()}
        </span>
      </div>
    </div>
  );
}

export default App;
