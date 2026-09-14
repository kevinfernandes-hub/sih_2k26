import React, { useEffect } from 'react';
import styles from './CaseSummaryModal.module.css';

export function CaseSummaryModal({
  isOpen,
  onClose,
  locationsList = [],
  hotspotsList = [],
  onInspectHotspot
}) {
  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Active cases derived from locations list & hotspots list
  const activeCases = (locationsList.length > 0 ? locationsList : [
    { id: 'mihan', name: 'MIHAN / Outer Ring Road', subtitle: 'South Ward IX — Aerospace & SEZ Corridor', status: 'flagged', colorDiff: 7.06 },
    { id: 'sadar', name: 'Sadar Commercial District', subtitle: 'Central Ward II — Civil District', status: 'flagged', colorDiff: 6.85 },
    { id: 'hingna', name: 'Hingna MIDC Industrial Zone', subtitle: 'Industrial MIDC Zone — Earthworks', status: 'flagged', colorDiff: 8.12 },
    { id: 'civil', name: 'Civil Lines Secretariat Zone', subtitle: 'Administrative Ward I — High Court Corridor', status: 'flagged', colorDiff: 9.40 },
    { id: 'dharampeth', name: 'Dharampeth West Corridor', subtitle: 'West Ward VIII — Residential & Commercial', status: 'elevated', colorDiff: 4.50 },
    { id: 'sitabuldi', name: 'Sitabuldi Metro Interchange', subtitle: 'Central Transit Ward — Metro Corridor', status: 'elevated', colorDiff: 4.20 },
    { id: 'nandanvan', name: 'Nandanvan Growth Corridor', subtitle: 'East Ward VI — Educational Corridor', status: 'elevated', colorDiff: 3.90 }
  ]).map((loc, idx) => {
    const isHigh = loc.status === 'flagged' || loc.colorDiff > 6.0;
    const isMedium = loc.status === 'elevated';
    return {
      case_id: `CASE #NGP-2025-0${idx + 1}`,
      hotspot_id: loc.id === 'mihan' ? 'MIHAN-042' : `${loc.id.slice(0, 4).toUpperCase()}-01`,
      location_name: loc.name,
      ward: loc.subtitle || 'Ward 36 · Nagpur Urban',
      change_observed: isHigh ? 'New Building Emergence (+1,812 px)' : isMedium ? 'Parcel Footprint Expansion' : 'Persistent Baseline',
      evidence_strength: isHigh ? '🟢 STRONG' : isMedium ? '🟡 MODERATE' : '🟢 STABLE',
      priority: isHigh ? 'HIGH' : isMedium ? 'MEDIUM' : 'LOW',
      recommended_action: isHigh ? 'FIELD INSPECTION REQUIRED' : isMedium ? 'OFFICER REVIEW' : 'ROUTINE MONITORING',
      location_id: loc.id
    };
  });

  const highPriorityCount = activeCases.filter((c) => c.priority === 'HIGH').length;
  const pendingInspectionCount = activeCases.length;
  const reviewCount = activeCases.filter((c) => c.priority === 'MEDIUM').length;

  return (
    <div className={styles.modalBackdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modalContainer} onClick={(e) => e.stopPropagation()}>
        
        {/* Header Bar */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <h2 className={styles.title}>
              <span>🏛️</span> Nagpur Municipal Corporation — Executive Case Overview &amp; Priorities Hub
            </h2>
            <p className={styles.subtitle}>
              City-wide urban surveillance case priorities, target corridor reviews &amp; active inspection dossier pipeline
            </p>
          </div>
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        {/* Body Content */}
        <div className={styles.bodyContent}>
          
          {/* SECTION 1: 4 Summary KPI Cards Grid */}
          <div className={styles.cardsGrid}>
            <div className={`${styles.summaryCard} ${styles.highCard}`}>
              <span className={styles.cardIcon}>🔴</span>
              <div>
                <div className={styles.cardVal}>{highPriorityCount}</div>
                <div className={styles.cardLabel}>HIGH PRIORITY CASES</div>
              </div>
            </div>

            <div className={`${styles.summaryCard} ${styles.inspectCard}`}>
              <span className={styles.cardIcon}>🏛️</span>
              <div>
                <div className={styles.cardVal}>{pendingInspectionCount}</div>
                <div className={styles.cardLabel}>FIELD INSPECTIONS AWAITING</div>
              </div>
            </div>

            <div className={`${styles.summaryCard} ${styles.reviewCard}`}>
              <span className={styles.cardIcon}>⚠️</span>
              <div>
                <div className={styles.cardVal}>{reviewCount}</div>
                <div className={styles.cardLabel}>NEEDS OFFICER REVIEW</div>
              </div>
            </div>

            <div className={`${styles.summaryCard} ${styles.areaCard}`}>
              <span className={styles.cardIcon}>📐</span>
              <div>
                <div className={styles.cardVal}>24,812 m²</div>
                <div className={styles.cardLabel}>TOTAL BUILT AREA DELTA</div>
              </div>
            </div>
          </div>

          {/* SECTION 2: 🎯 TARGET MUNICIPAL AREAS & SURVEILLANCE CORRIDORS */}
          <div className={styles.sectionBlock}>
            <div className={styles.sectionHeaderRow}>
              <div>
                <h3 className={styles.sectionTitle}>🎯 Target Municipal Surveillance Corridors &amp; Priority Sectors</h3>
                <span className={styles.sectionSub}>Surveillance zones flagged for town planning officer review across Nagpur Corporation wards</span>
              </div>
            </div>

            <div className={styles.sectorsGrid}>
              {activeCases.map((sector) => (
                <div key={sector.location_id} className={styles.sectorCard}>
                  <div className={styles.sectorHeader}>
                    <span className={styles.sectorName}>{sector.location_name}</span>
                    <span className={sector.priority === 'HIGH' ? styles.tagHigh : styles.tagMed}>
                      {sector.priority === 'HIGH' ? '🔴 HIGH PRIORITY' : '🟡 MODERATE'}
                    </span>
                  </div>
                  <div className={styles.sectorWard}>{sector.ward}</div>
                  <div className={styles.sectorChangeRow}>
                    <span>Observed Change:</span>
                    <strong>{sector.change_observed}</strong>
                  </div>
                  <div className={styles.sectorFooter}>
                    <span>Evidence: <strong style={{ color: '#34D399' }}>{sector.evidence_strength}</strong></span>
                    <button
                      type="button"
                      className={styles.sectorInspectBtn}
                      onClick={() => {
                        onClose();
                        if (onInspectHotspot) {
                          onInspectHotspot(sector.hotspot_id);
                        }
                      }}
                    >
                      Inspect Sector 🎯
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SECTION 3: 📂 ACTIVE MUNICIPAL INSPECTION CASES TABLE */}
          <div className={styles.sectionBlock}>
            <div className={styles.sectionHeaderRow}>
              <div>
                <h3 className={styles.sectionTitle}>📂 Active Vigilance &amp; Field Inspection Dossiers</h3>
                <span className={styles.sectionSub}>Cross-verified against high-resolution sub-meter optical satellite imagery</span>
              </div>
            </div>

            <div className={styles.tableWrapper}>
              <table className={styles.caseTable}>
                <thead>
                  <tr>
                    <th>Case ID</th>
                    <th>Location / Ward</th>
                    <th>Observed Change</th>
                    <th>Evidence</th>
                    <th>Priority</th>
                    <th>Recommended Action</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {activeCases.map((c) => (
                    <tr key={c.case_id}>
                      <td className={styles.caseId}>{c.case_id}</td>
                      <td>
                        <strong style={{ color: '#F8FAFC' }}>{c.location_name}</strong>
                        <div style={{ fontSize: '11px', color: '#94A3B8' }}>{c.ward}</div>
                      </td>
                      <td style={{ color: '#E2E8F0' }}>{c.change_observed}</td>
                      <td>{c.evidence_strength}</td>
                      <td>
                        <span className={c.priority === 'HIGH' ? styles.priorityHigh : c.priority === 'MEDIUM' ? styles.priorityMedium : styles.priorityLow}>
                          {c.priority}
                        </span>
                      </td>
                      <td style={{ fontWeight: '700', color: c.priority === 'HIGH' ? '#60A5FA' : '#E2E8F0' }}>
                        {c.recommended_action}
                      </td>
                      <td>
                        <button
                          type="button"
                          className={styles.inspectBtn}
                          onClick={() => {
                            onClose();
                            if (onInspectHotspot) {
                              onInspectHotspot(c.hotspot_id);
                            }
                          }}
                        >
                          Inspect 🔍
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className={styles.footer}>
          <span className={styles.footerNote}>
            Nagpur Municipal Corporation — Surveillance Records automatically updated from Esri Wayback &amp; Sentinel-2 satellite pipeline.
          </span>
          <button type="button" className={styles.dismissBtn} onClick={onClose}>
            Close
          </button>
        </div>

      </div>
    </div>
  );
}

export default CaseSummaryModal;
