export function getImageSources(location, tier = '10m') {
  if (!location?.imageryAvailable) return { before: '', after: '' };

  const selectedTier = location.tiers?.[tier] || location.tiers?.['10m'];
  return {
    before: selectedTier?.beforeImage || selectedTier?.before_image || location.localImages?.before || location.local_images?.before || location.before_image_url || '',
    after: selectedTier?.afterImage || selectedTier?.after_image || location.localImages?.after || location.local_images?.after || location.after_image_url || ''
  };
}

export function hasTemporalImagePair(location, tier = '10m') {
  const { before, after } = getImageSources(location, tier);
  return Boolean(before && after);
}