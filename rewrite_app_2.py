import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# 1. handleAcquireImagery
handle_acquire_regex = r"  const handleAcquireImagery = useCallback\(\s*async \(targetLocation\) => \{[\s\S]*?    \},[\s\S]*?\[.*?\]\n  \);"
handle_acquire_replacement = r"""  const handleAcquireImagery = useCallback(
    async () => {
      const loc = currentInvestigation?.location;
      if (!loc) return;

      const { id: location_id, name: locName, coordinates, bbox } = loc;
      const [lat, lng] = coordinates || [loc.lat, loc.lng];
      const { before_date, after_date } = currentInvestigation.temporal_pair;

      console.log('[FETCH] handleAcquireImagery executing:', {
        location_id, lat, lng, bbox, before_date, after_date
      });

      setErrorMessage('');
      setIsScanning(true);
      setScanningStatusText('ACQUIRING IMAGERY: ✓ Area identified');
      clearProgressTimers();

      progressTimersRef.current.push(setTimeout(() => setScanningStatusText('ACQUIRING IMAGERY: ✓ Checking local archive'), 800));
      progressTimersRef.current.push(setTimeout(() => setScanningStatusText('ACQUIRING IMAGERY: → Discovering scenes...'), 2000));
      progressTimersRef.current.push(setTimeout(() => setScanningStatusText('ACQUIRING IMAGERY: → Selecting temporal pair...'), 4000));
      progressTimersRef.current.push(setTimeout(() => setScanningStatusText('ACQUIRING IMAGERY: → Fetching Sentinel-2 & high-resolution imagery...'), 7000));
      progressTimersRef.current.push(setTimeout(() => setScanningStatusText('ACQUIRING IMAGERY: → Validating assets & saving cache...'), 10000));

      try {
        const response = await fetch('/api/acquire-imagery', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            location_name: locName,
            lat, lng, bbox, before_date, after_date
          })
        });

        clearProgressTimers();

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          setErrorMessage(errData?.detail?.reason || errData?.reason || 'Acquisition failed.');
          setIsScanning(false);
          setScanningStatusText('');
          return;
        }

        const data = await response.json();
        if (!data.ready_for_analysis) {
          setErrorMessage('Acquisition incomplete: No valid Sentinel-2 imagery acquired.');
          setIsScanning(false);
          setScanningStatusText('');
          return;
        }

        const sentinelAssets = (data.assets || []).filter((a) => a.provider === 'copernicus');
        const beforeAsset = sentinelAssets.find((a) => a.role === 'before');
        const afterAsset = sentinelAssets.find((a) => a.role === 'after');
        
        const hrAssets = (data.assets || []).filter((a) => a.provider === 'arcgis_wayback');
        const hrBefore = hrAssets.find((a) => a.role === 'before');
        const hrAfter = hrAssets.find((a) => a.role === 'after');

        const updatedTiers = {
          '10m': {
            source: 'Sentinel-2 (Live Copernicus CDSE)',
            beforeImage: beforeAsset?.local_path ? `/static/results/${beforeAsset.local_path.split('/static/results/')[1] || ''}` : '',
            afterImage: afterAsset?.local_path ? `/static/results/${afterAsset.local_path.split('/static/results/')[1] || ''}` : '',
            beforeDate: beforeAsset?.acquisition_date || '2022-02-22',
            afterDate: afterAsset?.acquisition_date || '2025-02-26',
            colorDiffPct: null, ssimPct: null
          }
        };
        if (hrBefore && hrAfter) {
          updatedTiers['0.6m'] = {
            source: 'ArcGIS World Imagery Wayback (~0.6m)',
            beforeImage: hrBefore.local_path ? `/static/results/${hrBefore.local_path.split('/static/results/')[1] || ''}` : '',
            afterImage: hrAfter.local_path ? `/static/results/${hrAfter.local_path.split('/static/results/')[1] || ''}` : ''
          };
        }

        setCurrentInvestigation(prev => ({
          ...prev,
          imagery: { status: 'ready', sentinel2: updatedTiers['10m'], high_resolution: updatedTiers['0.6m'] || null },
          temporal_pair: { valid: true, before_date: updatedTiers['10m'].beforeDate, after_date: updatedTiers['10m'].afterDate },
          analysis: { status: 'pending', optical_change: null, ssim_difference: null, hotspots: [] }
        }));
        
        // Update locationsList to reflect imagery availability so "hasTemporalImagePair" succeeds for SectorCard
        setLocationsList(prev => prev.map(l => l.id === location_id ? { ...l, imageryAvailable: true, tiers: updatedTiers } : l));

        setScanningStatusText('ACQUIRING IMAGERY: ✓ Success.');
        setTimeout(() => { setIsScanning(false); setScanningStatusText(''); }, 1500);

        if (currentInvestigation.retrieval) {
           const query = currentInvestigation.retrieval.query || '';
           fetch('/api/verify-semantics', {
             method: 'POST',
             headers: {'Content-Type': 'application/json'},
             body: JSON.stringify({
               query, location_id,
               before_image: updatedTiers['10m'].beforeImage,
               after_image: updatedTiers['10m'].afterImage
             })
           }).then(r => r.json()).then(result => {
               setCurrentInvestigation(p => ({ ...p, semantic_verification: { status: 'completed', result } }));
           }).catch(err => console.error("Verification failed", err));
        }

      } catch (err) {
        clearProgressTimers();
        console.error('Acquisition failed:', err);
        setErrorMessage('Failed to connect to backend.');
        setIsScanning(false);
        setScanningStatusText('');
      }
    },
    [currentInvestigation]
  );"""
content = re.sub(handle_acquire_regex, handle_acquire_replacement, content)

# 2. handleAnalyzeCustomDates
handle_analyze_regex = r"  const handleAnalyzeCustomDates = useCallback\(\s*async \(beforeDate, afterDate\) => \{[\s\S]*?    \},[\s\S]*?\[.*?\]\n  \);"
handle_analyze_replacement = r"""  const handleAnalyzeCustomDates = useCallback(
    async (beforeDate, afterDate) => {
      if (!currentInvestigation || currentInvestigation.imagery.status !== 'ready') {
        setErrorMessage('Stage satellite imagery before running analysis.');
        return;
      }
      const loc = currentInvestigation.location;
      const [lat, lng] = loc.coordinates || [loc.lat, loc.lng];

      setErrorMessage('');
      setIsScanning(true);
      setScanningStatusText(`1/3 Fetching Process API granules for ${beforeDate} & ${afterDate}...`);
      clearProgressTimers();

      progressTimersRef.current.push(setTimeout(() => setScanningStatusText('2/3 Computing optical pixel delta...'), 3000));
      progressTimersRef.current.push(setTimeout(() => setScanningStatusText('3/3 Generating SSIM structural divergence matrix...'), 6000));

      try {
        const response = await fetch('/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lat, lng, location_name: loc.name, before_date: beforeDate, after_date: afterDate })
        });

        clearProgressTimers();

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          setErrorMessage(errData?.detail?.reason || errData?.reason || 'Analysis failed.');
          setIsScanning(false);
          setScanningStatusText('');
          return;
        }

        const data = await response.json();
        const ssimArea = data.ssim_pct;
        const colorDiff = data.color_diff_pct;

        setCurrentInvestigation(prev => ({
          ...prev,
          analysis: {
            ...prev.analysis,
            status: 'completed',
            optical_change: colorDiff,
            ssim_difference: ssimArea,
            ssim_score: data.ssim_score,
            confidence: data.confidence,
            hotspots: data.hotspots || []
          },
          imagery: {
            ...prev.imagery,
            sentinel2: {
              ...prev.imagery.sentinel2,
              colorDiffOverlay: data.color_diff_overlay_url,
              ssimOverlay: data.ssim_overlay_url
            }
          }
        }));

        setLocationsList(prev => prev.map(l => {
          if (l.id === loc.id) {
             return {
                ...l, colorDiff, ssimArea, analysisComplete: true,
                tiers: { ...l.tiers, '10m': { ...l.tiers?.['10m'], colorDiffOverlay: data.color_diff_overlay_url, ssimOverlay: data.ssim_overlay_url } }
             };
          }
          return l;
        }));

        if (data.hotspots && Array.isArray(data.hotspots) && data.hotspots.length > 0) {
          setHotspotsList(data.hotspots);
          setSelectedHotspotId(data.hotspots[0].hotspot_id);
        } else {
          setHotspotsList([]);
        }

        setIsScanning(false);
        setScanningStatusText('');
      } catch (err) {
        clearProgressTimers();
        console.error('Analysis failed:', err);
        setErrorMessage('Failed to connect to backend.');
        setIsScanning(false);
        setScanningStatusText('');
      }
    },
    [currentInvestigation]
  );"""
content = re.sub(handle_analyze_regex, handle_analyze_replacement, content)

with open('src/App_new.jsx', 'w') as f:
    f.write(content)
