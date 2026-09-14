import re

with open('src/components/MetricsPanel/MetricsPanel.jsx', 'r') as f:
    content = f.read()

replacement = r"""export function MetricsPanel({ location, currentInvestigation, selectedTier = '10m', onTierChange }) {
  const inv = currentInvestigation || {};
  const activeLocation = inv.location || location;
  const tiers = inv.imagery?.status === 'ready' ? { '10m': inv.imagery.sentinel2, '0.6m': inv.imagery.high_resolution } : activeLocation?.tiers;
  
  const tier06 = tiers?.['0.6m'];
  const tier10 = tiers?.['10m'];
  const activeTier = selectedTier === '0.6m' && tier06 ? tier06 : tier10;
  
  const retrieval = inv.retrieval || activeLocation?.retrievalResult;
  const evidence = activeLocation?.retrievalPlan?.evidence;
  
  const imageryAvailable = Boolean(tier10?.beforeImage && tier10?.afterImage);
  const isAnalysisComplete = inv.analysis?.status === 'completed' || activeLocation?.analysisComplete;
  
  const changeDetected = Boolean(isAnalysisComplete && (inv.analysis?.optical_change > 0 || inv.analysis?.ssim_difference > 0 || activeTier?.colorDiffPct > 0));
  
  const colorDiff = inv.analysis?.optical_change ?? activeLocation?.colorDiff;
  const ssimArea = inv.analysis?.ssim_difference ?? activeLocation?.ssimArea;
  const beforeDate = inv.temporal_pair?.before_date || tier10?.beforeDate || activeLocation?.beforeDate;
  const afterDate = inv.temporal_pair?.after_date || tier10?.afterDate || activeLocation?.afterDate;
  
  const semanticVerification = inv.semantic_verification?.status === 'completed' 
      ? { ...inv.semantic_verification.result, status: 'completed' } 
      : (inv.semantic_verification?.status === 'pending' ? 'pending' : activeLocation?.semanticVerification);
"""

content = re.sub(r'export function MetricsPanel\(\{ location, selectedTier = \'10m\', onTierChange \}\) \{[\s\S]*?const isAnalysisComplete = Boolean\(location\?\.analysisComplete\);', replacement, content)

content = content.replace('location?.semanticVerification', 'semanticVerification')
content = content.replace('location.semanticVerification', 'semanticVerification')
content = content.replace('location?.colorDiff', 'colorDiff')
content = content.replace('location?.ssimArea', 'ssimArea')
content = content.replace('location?.beforeDate', 'beforeDate')
content = content.replace('location?.afterDate', 'afterDate')
content = content.replace('location?.acquisitionSource', '(inv.imagery?.status === "ready" ? "LIVE ACQUIRED" : activeLocation?.acquisitionSource)')

with open('src/components/MetricsPanel/MetricsPanel_new.jsx', 'w') as f:
    f.write(content)
