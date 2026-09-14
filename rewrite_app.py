import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# 1. Add currentInvestigation state
state_block = r"(  const \[indexStatus, setIndexStatus\] = useState\(null\);\n  const progressTimersRef = useRef\(\[\]\);)"
replacement = r"""  const [indexStatus, setIndexStatus] = useState(null);
  const [currentInvestigation, setCurrentInvestigation] = useState(null);
  const progressTimersRef = useRef([]);"""
content = re.sub(state_block, replacement, content)

# 2. Rewrite selectedLocation
selected_loc_block = r"  const selectedLocation = useMemo\([\s\S]*?\[locationsList, selectedLocationId\]\n  \);"
selected_loc_replacement = r"""  const selectedLocation = useMemo(() => {
    if (currentInvestigation) {
      return currentInvestigation.location;
    }
    return locationsList.find((l) => l.id === selectedLocationId) || locationsList[0];
  }, [locationsList, selectedLocationId, currentInvestigation]);"""
content = re.sub(selected_loc_block, selected_loc_replacement, content)

# 3. Rewrite handleSemanticAnalysisPrepared
semantic_block = r"  const handleSemanticAnalysisPrepared = useCallback\(\(plan, result\) => \{[\s\S]*?catch\(console\.error\);\n  \}, \[\]\);"
semantic_replacement = r"""  const handleSemanticAnalysisPrepared = useCallback((plan, result) => {
    const scenes = plan?.temporal?.scenes || [];
    const before = scenes.find((scene) => scene.tile_id === plan?.analysis?.before_tile_id);
    const after = scenes.find((scene) => scene.tile_id === plan?.analysis?.after_tile_id);
    if (!before || !after) return;
    const bbox = after.bbox || result.bbox || [79.11, 21.115, 79.155, 21.155];
    const locId = `retrieval-${result.tile_id}`;

    const locationObj = {
      id: locId,
      name: `Retrieved: ${result.tile_id}`,
      subtitle: `${result.scene_id} · Semantic match ${Math.round(result.final_score * 100)}%`,
      status: 'elevated',
      coordinates: [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2],
      coords: `${((bbox[0] + bbox[2]) / 2).toFixed(4)}° E, ${((bbox[1] + bbox[3]) / 2).toFixed(4)}° N`,
      bbox: bbox,
      tiers: {
        '10m': {
          source: 'Copernicus Sentinel-2',
          beforeImage: null,
          afterImage: null,
          beforeDate: before.date,
          afterDate: after.date,
          colorDiffPct: null,
          ssimPct: null,
          ssimScore: null
        }
      },
      localImages: { before: null, after: null },
      isLiveAnalyzed: false,
      imageryAvailable: false,
      analysisComplete: false,
      beforeDate: before.date,
      afterDate: after.date,
      retrievalResult: result,
      retrievalPlan: plan,
      colorDiff: null,
      ssimArea: null
    };

    setCurrentInvestigation({
      location: locationObj,
      retrieval: result,
      imagery: { status: 'pending', sentinel2: null, high_resolution: null },
      temporal_pair: { valid: true, before_date: before.date, after_date: after.date },
      semantic_verification: { status: 'idle' },
      analysis: { status: 'idle', optical_change: null, ssim_difference: null, hotspots: [] }
    });
    
    setSelectedLocationId(locId);
    setSemanticResult({ location: locationObj, result, plan });
    setSelectedTier('10m');
    
    fetch(`/api/imagery-status?lat=${locationObj.coordinates[0]}&lng=${locationObj.coordinates[1]}&location_name=${encodeURIComponent(locationObj.name)}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'READY') {
           setCurrentInvestigation(prev => prev ? { ...prev, imagery: { ...prev.imagery, status: 'ready' } } : prev);
        }
      })
      .catch(console.error);
  }, []);"""
content = re.sub(semantic_block, semantic_replacement, content)


# 4. Rewrite handleSelectLocation
select_loc_block = r"  const handleSelectLocation = useCallback\([\s\S]*?\[\]\n  \);"
select_loc_replacement = r"""  const handleSelectLocation = useCallback(
    (id) => {
      setSelectedLocationId(id);
      setSemanticResult(null);
      
      const loc = locationsList.find(l => l.id === id);
      if (loc) {
        setCurrentInvestigation({
          location: loc,
          retrieval: null,
          imagery: { status: 'ready', sentinel2: loc.tiers?.['10m'], high_resolution: loc.tiers?.['0.6m'] },
          temporal_pair: { valid: true, before_date: loc.tiers?.['10m']?.beforeDate || '2022-02-22', after_date: loc.tiers?.['10m']?.afterDate || '2025-02-26' },
          semantic_verification: { status: 'idle' },
          analysis: { 
            status: loc.analysisComplete ? 'completed' : 'pending', 
            optical_change: loc.colorDiff, 
            ssim_difference: loc.ssimArea, 
            hotspots: [] 
          }
        });
      }
      
      const defaultHid = id === 'mihan' ? 'MIHAN-042' : id === 'sadar' ? 'SADA-01' : id === 'hingna' ? 'HING-01' : id === 'civil-lines' ? 'CIVI-01' : `${id.replace(/[^a-zA-Z0-9]/g, '').slice(0, 4).toUpperCase()}-01`;
      setSelectedHotspotId(defaultHid);
      setSearchQuery('');
      setErrorMessage('');
      setScanningStatusText('');
      setIsScanning(false);
      setHotspotsList([]);
    },
    [locationsList]
  );"""
content = re.sub(select_loc_block, select_loc_replacement, content)

# 5. Modify render props in SectorList, ImageComparisonViewer, MetricsPanel
content = content.replace('locations={locationsList}', 'locations={locationsList}\n          currentInvestigation={currentInvestigation}')
content = content.replace('location={selectedLocation}', 'location={selectedLocation}\n          currentInvestigation={currentInvestigation}')
content = content.replace('hotspots={hotspotsList}', 'hotspots={hotspotsList}\n          currentInvestigation={currentInvestigation}')

with open('src/App_new.jsx', 'w') as f:
    f.write(content)
