import re

with open('src/components/ImageComparisonViewer/ImageComparisonViewer.jsx', 'r') as f:
    content = f.read()

replacement = r"""export function ImageComparisonViewer({
  location,
  currentInvestigation,
  threshold = 20.0,
  selectedTier = '10m',
  onTierChange,
  hotspots = [],
  selectedHotspotId,
  onSelectHotspot,
  onInspectHotspot
}) {
  const inv = currentInvestigation || {};
  const activeLocation = inv.location || location;
  const tiers = inv.imagery?.status === 'ready' ? { '10m': inv.imagery.sentinel2, '0.6m': inv.imagery.high_resolution } : activeLocation?.tiers;
  
  const isHighRes = selectedTier === '0.6m';
  const tier06 = tiers?.['0.6m'];
  const tier10 = tiers?.['10m'];
  const imageryAvailable = Boolean(tier10?.beforeImage && tier10?.afterImage);
"""

content = re.sub(r'export function ImageComparisonViewer\(\{[\s\S]*?const imageryAvailable = hasTemporalImagePair\(location, selectedTier\);', replacement, content)

content = content.replace('location?.analysisComplete', '(inv.analysis?.status === "completed" || activeLocation?.analysisComplete)')
content = content.replace('location?.isLiveAnalyzed', '(inv.analysis?.status === "completed" || activeLocation?.isLiveAnalyzed)')

with open('src/components/ImageComparisonViewer/ImageComparisonViewer_new.jsx', 'w') as f:
    f.write(content)
