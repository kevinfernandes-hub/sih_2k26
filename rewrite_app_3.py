import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# Update StatusBar
status_block = r"""      <div className=\{styles.systemStatusBar\}>
        <span className=\{styles.systemStatusLabel\}>\{indexStatus\?.offline_ready \? 'OFFLINE ARCHIVE READY' : 'INDEX STATUS UNAVAILABLE'\}</span>
        <span>
          \{selectedLocation\?.analysisComplete
            \? 'ANALYSIS COMPLETE'
            : isScanning
            \? 'ANALYZING...'
            : selectedLocation\?.imageryAvailable
            \? 'IMAGERY READY'
            : 'LIVE IMAGERY REQUIRED'\}
        </span>"""

status_replace = r"""      <div className={styles.systemStatusBar}>
        <span className={styles.systemStatusLabel}>{indexStatus?.offline_ready ? 'OFFLINE ARCHIVE READY' : 'INDEX STATUS UNAVAILABLE'}</span>
        <span>
          {currentInvestigation?.analysis?.status === 'completed' || selectedLocation?.analysisComplete
            ? 'ANALYSIS COMPLETE'
            : isScanning
            ? 'ANALYZING...'
            : currentInvestigation?.imagery?.status === 'ready' || selectedLocation?.imageryAvailable
            ? 'IMAGERY READY'
            : 'LIVE IMAGERY REQUIRED'}
        </span>"""
content = re.sub(status_block, status_replace, content)

# Update YOLOBuildingIntelligence
yolo_block = r"""          beforeImageUrl=\{selectedLocation\?.tiers\?\.\['0\.6m'\]\?.beforeImage \|\| selectedLocation\?.tiers\?\.\['10m'\]\?.beforeImage \|\| ''\}
          afterImageUrl=\{selectedLocation\?.tiers\?\.\['0\.6m'\]\?.afterImage \|\| selectedLocation\?.tiers\?\.\['10m'\]\?.afterImage \|\| ''\}"""

yolo_replace = r"""          beforeImageUrl={currentInvestigation?.imagery?.high_resolution?.beforeImage || currentInvestigation?.imagery?.sentinel2?.beforeImage || selectedLocation?.tiers?.['0.6m']?.beforeImage || selectedLocation?.tiers?.['10m']?.beforeImage || ''}
          afterImageUrl={currentInvestigation?.imagery?.high_resolution?.afterImage || currentInvestigation?.imagery?.sentinel2?.afterImage || selectedLocation?.tiers?.['0.6m']?.afterImage || selectedLocation?.tiers?.['10m']?.afterImage || ''}"""
content = re.sub(yolo_block, yolo_replace, content)


with open('src/App_new.jsx', 'w') as f:
    f.write(content)
