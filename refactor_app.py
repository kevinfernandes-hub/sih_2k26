import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# 1. Add currentInvestigation state
state_block_end = content.find('const progressTimersRef = useRef([]);')
content = content[:state_block_end] + """  const [currentInvestigation, setCurrentInvestigation] = useState(null);
  """ + content[state_block_end:]

# 2. handleSelectLocation
# We want it to set currentInvestigation based on the preset location
handle_select = """  const handleSelectLocation = useCallback(
    (id) => {
      setSelectedLocationId(id);
      setSemanticResult(null);
      const loc = locationsList.find(l => l.id === id);
      if (loc) {
        setCurrentInvestigation({
          location: { id: loc.id, name: loc.name, lat: loc.coordinates[0], lng: loc.coordinates[1], bbox: loc.bbox || null },
          retrieval: null,
          imagery: { status: 'ready', source: 'CACHED', sentinel2: loc.tiers?.['10m'], high_resolution: loc.tiers?.['0.6m'] },
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
content = re.sub(r'  const handleSelectLocation = useCallback\([\s\S]*?\[\]\n  \);', handle_select, content)


with open('src/App.jsx', 'w') as f:
    f.write(content)
