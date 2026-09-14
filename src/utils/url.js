/**
 * Normalizes any image URL (absolute http/https or relative) to clean relative paths
 * to prevent mixed content blocking when deployed on HTTPS (e.g. Render/Vercel).
 */
export const normalizeImageUrl = (url) => {
  if (!url || typeof url !== 'string') return '';
  if (url.includes('/static/')) {
    return '/static/' + url.split('/static/')[1];
  }
  if (url.includes('/outputs/')) {
    return '/outputs/' + url.split('/outputs/')[1];
  }
  if (url.includes('/public/')) {
    return '/public/' + url.split('/public/')[1];
  }
  return url;
};
