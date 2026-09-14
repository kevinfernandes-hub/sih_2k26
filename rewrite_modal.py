import re

with open('src/components/InspectionModal/InspectionModal.jsx', 'r') as f:
    content = f.read()

replacement = r"""export function InspectionModal({ location, currentInvestigation, onClose }) {
  if (!location && !currentInvestigation) return null;
  const loc = currentInvestigation?.location || location;
  const unpermitted = loc.permits?.filter((p) => p.status === 'unmatched') || [];
  const colorDiff = currentInvestigation?.analysis?.optical_change ?? loc.colorDiff ?? 0;
  const ssimArea = currentInvestigation?.analysis?.ssim_difference ?? loc.ssimArea ?? 0;

  return (
    <div className={styles.backdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.card} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <span className={styles.title}>Field Inspection Dispatch</span>
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>

        <div className={styles.body}>
          <p><strong>Target Sector:</strong> {loc.name} ({loc.subtitle})</p>
          <p><strong>Coordinates:</strong> {loc.coords}</p>
          <p style={{ marginTop: '8px' }}>
            <strong>Geospatial Delta:</strong> Color Diff {colorDiff.toFixed(2)}%, SSIM Structural Area {ssimArea.toFixed(2)}%.
          </p>
          <p style={{ marginTop: '8px', color: unpermitted.length > 0 ? 'var(--accent-primary)' : 'inherit' }}>
            <strong>Municipal Audit:</strong> {unpermitted.length} unpermitted plot alteration(s) flagged for physical on-site verification.
          </p>
        </div>
"""

content = re.sub(r'export function InspectionModal\(\{ location, onClose \}\) \{[\s\S]*?<div className=\{styles\.body\}>[\s\S]*?</div>', replacement, content)

with open('src/components/InspectionModal/InspectionModal_new.jsx', 'w') as f:
    f.write(content)
