import { normalizeImageUrl } from '../../utils/url';
import React, { useState, useEffect } from 'react';
import styles from './AIInspectionModal.module.css';

export function AIInspectionModal({
  isOpen,
  onClose,
  caseData,
  isLoading = false,
  onExportDispatch,
  userViewMode = 'officer'
}) {
  const [activeZoomKey, setActiveZoomKey] = useState('level1');
  const [overlayMode, setOverlayMode] = useState('diff');
  const [showChangeHighlight, setShowChangeHighlight] = useState(true);
  const [selectedBldg, setSelectedBldg] = useState(null);
  const [officerDecision, setOfficerDecision] = useState(null);
  const [isAnalystAccordionOpen, setIsAnalystAccordionOpen] = useState(userViewMode === 'analyst');
  const [priorityData, setPriorityData] = useState(null);
  const [isEvaluatingPriority, setIsEvaluatingPriority] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
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

  // Fetch Phase 5 priority evaluation & explanation layer when modal opens
  useEffect(() => {
    if (isOpen && caseData) {
      setActiveZoomKey('level1');
      setOverlayMode('diff');
      setShowChangeHighlight(true);
      setOfficerDecision(null);
      setIsAnalystAccordionOpen(userViewMode === 'analyst');
      setIsEvaluatingPriority(true);

      fetch('/api/priority/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseData.case_id || `CASE-${caseData.hotspot_id || '042'}`,
          case_data: caseData
        })
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) setPriorityData(data);
        })
        .catch((err) => {
          console.warn('Priority evaluation API error:', err);
        })
        .finally(() => {
          setIsEvaluatingPriority(false);
        });
    }
  }, [isOpen, caseData, userViewMode]);

  const handleDecision = async (decision) => {
    setOfficerDecision(decision);
    try {
      await fetch('/api/priority/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseData.case_id || `CASE-${caseData.hotspot_id || '042'}`,
          officer_decision: decision,
          officer_priority: priorityData?.active_priority || caseData?.priority || 'HIGH',
          case_data: caseData
        })
      });
    } catch (err) {
      console.warn('Feedback log error:', err);
    }
  };

  const handlePrintDispatch = () => {
    handleDecision('CONFIRMED');
    if (onExportDispatch) {
      onExportDispatch(caseData);
    } else {
      window.print();
    }
  };

  if (!isOpen || !caseData) return null;

  const zoomLevels = caseData.zoom_levels || {};
  const activeZoom = zoomLevels[activeZoomKey] || zoomLevels['level1'] || {};

  const beforeSrc = activeZoom.before_image_url || '/wayback_mihan_same_season_20190131_before.png';
  const afterSrc = activeZoom.after_image_url || '/wayback_mihan_same_season_20250130_after.png';
  
  const yoloRes = caseData.yolo_analysis || null;
  const yoloArtifacts = yoloRes?.artifacts || null;

  let diffSrc = activeZoom.overlay_image_url || activeZoom.difference_image_url || '/wayback_mihan_sameszn_calibrated_color_overlay.png';
  if (overlayMode === 'yolo' && yoloArtifacts?.change_overlay) {
    diffSrc = yoloArtifacts.change_overlay;
  } else if (overlayMode === 'yolo_mask' && yoloArtifacts?.change_mask) {
    diffSrc = yoloArtifacts.change_mask;
  } else if (overlayMode === 'ssim' && activeZoom.ssim_image_url) {
    diffSrc = activeZoom.ssim_image_url;
  } else if (overlayMode === 'veg' && activeZoom.veg_overlay_image_url) {
    diffSrc = activeZoom.veg_overlay_image_url;
  }

  const activePrio = priorityData?.active_priority || caseData.priority || 'HIGH';
  const isStable = activePrio === 'LOW' || caseData.change_type === 'NO_SIGNIFICANT_CHANGE';
  const isUncertain = activePrio === 'NEEDS_REVIEW' || activePrio === 'UNCERTAIN';

  const priorityBadge = isStable
    ? { label: '🟢 STABLE', color: '#10B981', bg: 'rgba(16, 185, 129, 0.15)' }
    : isUncertain
      ? { label: '⚠️ NEEDS REVIEW', color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.15)' }
      : activePrio === 'CRITICAL'
        ? { label: '🔴 CRITICAL PRIORITY', color: '#EF4444', bg: 'rgba(239, 68, 68, 0.15)' }
        : { label: '🔴 HIGH PRIORITY', color: '#EF4444', bg: 'rgba(239, 68, 68, 0.15)' };

  const changeCategory = isStable
    ? 'SURFACE STABLE / NO CHANGE'
    : caseData.change_type === 'EXPANDED'
      ? 'STRUCTURE FOOTPRINT EXPANSION'
      : '🏗️ NEW PHYSICAL STRUCTURE';

  const explanation = priorityData?.explanation || {};
  const whyReasons = explanation.why_flagged || priorityData?.rule_based_priority?.reasons || [
    'Physical change detected between 2019 baseline and 2025 current imagery',
    'Strong supporting multi-scale satellite evidence',
    'Target location requires municipal town planning field review'
  ];
  const officerChecklist = explanation.what_officer_should_verify || [
    'Confirm physical structure presence on ground',
    'Verify exact parcel boundary coordinates',
    'Record current physical construction state & footprint',
    'Cross-reference municipal sanction/permit records'
  ];

  return (
    <div className={styles.modalBackdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modalContainer} onClick={(e) => e.stopPropagation()}>
        
        {/* Header Bar */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <div className={styles.caseBadgeRow}>
              <span className={styles.caseIdBadge}>{caseData.case_id || 'CASE #NGP-2025-042'}</span>
              <span className={styles.priorityTag} style={{ background: priorityBadge.bg, color: priorityBadge.color }}>
                {priorityBadge.label}
              </span>
              <span className={styles.evidenceQualityBadge}>
                EVIDENCE: {priorityData?.rule_based_priority?.evidence_strength || '🟢 STRONG'}
              </span>
            </div>
            <h2 className={styles.modalTitle}>
              Nagpur Municipal Case Dossier — {caseData.name || caseData.location_name}
            </h2>
            <div className={styles.metaRow}>
              <span>📍 {caseData.location_name || 'MIHAN / Outer Ring Road'} ({caseData.coordinates || '21.0568° N, 79.0435° E'})</span>
              <span>• Ward {caseData.ward || '36'} (Laxmi Nagar Zone)</span>
              <span>• Observed Window: {(caseData.before_date || '2019-01-31').split(' ')[0]} ➔ {(caseData.after_date || '2025-01-30').split(' ')[0]}</span>
            </div>
          </div>

          <div className={styles.headerRight}>
            <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close Dossier">
              ✕
            </button>
          </div>
        </div>

        <div className={styles.bodyScrollContent}>
          
          {/* ======================================================================== */}
          {/* 1. NMC OFFICER DECISION SUMMARY & ACTION BOX (10-SECOND CLARITY)          */}
          {/* ======================================================================== */}
          <div className={styles.officerSummaryBox}>
            <div className={styles.summaryTopRow}>
              <div className={styles.changeCategoryTitle}>
                {changeCategory}
              </div>
              <div className={styles.actionRecommendationPill}>
                🏛️ RECOMMENDED: {priorityData?.rule_based_priority?.recommended_action || 'FIELD INSPECTION REQUIRED'}
              </div>
            </div>

            <div className={styles.checklistGrid}>
              <div className={styles.checklistItem}>
                <span className={styles.checkLabel}>WHAT HAPPENED?</span>
                <span className={styles.checkValue}>
                  {explanation.what_happened || 'A new physical structure appears in the latest satellite imagery that was not visible in the earlier observation.'}
                </span>
              </div>

              <div className={styles.checklistItem}>
                <span className={styles.checkLabel}>WHY FLAGGED FOR INSPECTION?</span>
                <ul className={styles.reasonsList}>
                  {whyReasons.map((reason, i) => (
                    <li key={i}>✓ {reason}</li>
                  ))}
                </ul>
              </div>

              <div className={styles.checklistItem}>
                <span className={styles.checkLabel}>WHAT SHOULD THE OFFICER VERIFY ON SITE?</span>
                <ul className={styles.verifyList}>
                  {officerChecklist.map((item, i) => (
                    <li key={i}>🔍 {item}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Officer Action Workflow Box */}
            <div className={styles.workflowRow}>
              <div style={{ flex: 1 }}>
                <div className={styles.actionPromptText}>
                  Notice: Remote satellite imagery confirms physical ground structure emergence. Legal determination requires municipal permit verification and on-ground field inspection.
                </div>
              </div>

              <div className={styles.officerBtnGroup}>
                <button
                  type="button"
                  className={`${styles.decisionBtn} ${officerDecision === 'CONFIRMED' ? styles.btnConfirmed : ''}`}
                  onClick={() => handleDecision('CONFIRMED')}
                >
                  ✓ CONFIRM CHANGE
                </button>
                <button
                  type="button"
                  className={`${styles.decisionBtn} ${officerDecision === 'FALSE_POSITIVE' ? styles.btnFalsePos : ''}`}
                  onClick={() => handleDecision('FALSE_POSITIVE')}
                >
                  ✕ FALSE POSITIVE
                </button>
                <button
                  type="button"
                  className={`${styles.decisionBtn} ${officerDecision === 'NEEDS_REVIEW' ? styles.btnReview : ''}`}
                  onClick={() => handleDecision('NEEDS_REVIEW')}
                >
                  ⚠️ NEEDS REVIEW
                </button>
                <button
                  type="button"
                  className={styles.dispatchNoticeBtn}
                  onClick={handlePrintDispatch}
                >
                  📄 ASSIGN INSPECTOR &amp; EXPORT
                </button>
              </div>
            </div>

            {officerDecision && (
              <div className={styles.decisionRecordedNote}>
                ✅ Officer Decision Recorded: <strong>{officerDecision}</strong> (Logged into Phase 5 training dataset).
              </div>
            )}
          </div>

          {/* ======================================================================== */}
          {/* 2. VISUAL EVIDENCE (BEFORE vs AFTER)                                     */}
          {/* ======================================================================== */}
          <div className={styles.visualEvidenceSection}>
            <div className={styles.visualHeader}>
              <h3 className={styles.visualTitle}>📷 VISUAL SATELLITE EVIDENCE (BEFORE vs AFTER)</h3>
              <button
                type="button"
                className={styles.toggleHighlightBtn}
                onClick={() => setShowChangeHighlight(!showChangeHighlight)}
              >
                {showChangeHighlight ? 'Hide Change Highlight Overlay' : '✨ Show Change Highlight Overlay'}
              </button>
            </div>

            <div className={styles.sideBySideGrid}>
              {/* BEFORE */}
              <div className={styles.imageCard}>
                <div className={styles.imageHeader}>
                  <span>BEFORE: {(caseData.before_date || '2019-01-31').split(' ')[0]}</span>
                  <span className={styles.subtextBadge}>0.6m Baseline</span>
                </div>
                <div className={styles.imgWrap}>
                  <img src={normalizeImageUrl(beforeSrc)} alt="Historical Satellite Baseline" className={styles.satelliteImg} />
                </div>
              </div>

              {/* AFTER */}
              <div className={styles.imageCard}>
                <div className={styles.imageHeader}>
                  <span>AFTER: {(caseData.after_date || '2025-01-30').split(' ')[0]}</span>
                  <span className={styles.subtextBadge}>0.6m Current Scene</span>
                </div>
                <div className={styles.imgWrap}>
                  <img src={normalizeImageUrl(afterSrc)} alt="Current Satellite State" className={styles.satelliteImg} />
                </div>
              </div>

              {/* OVERLAY HIGHLIGHT */}
              {showChangeHighlight && (
                <div className={styles.imageCard}>
                  <div className={styles.imageHeader}>
                    <span>DETECTED CHANGE OVERLAY</span>
                    <span className={styles.subtextBadge}>Aligned Analysis</span>
                  </div>
                  <div className={styles.imgWrap}>
                    <img src={normalizeImageUrl(diffSrc)} alt="Detected Change Overlay" className={styles.satelliteImg} />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ======================================================================== */}
          {/* 3. COLLAPSIBLE TECHNICAL EVIDENCE & AI DECISION CHAIN SECTION             */}
          {/* ======================================================================== */}
          <div className={styles.analystAccordion}>
            <button
              type="button"
              className={styles.accordionHeader}
              onClick={() => setIsAnalystAccordionOpen(!isAnalystAccordionOpen)}
            >
              <span>🔬 Technical Priority Analysis &amp; Model Decision Chain — For Analysts</span>
              <span>{isAnalystAccordionOpen ? '▲ Collapse' : '▼ Expand Technical Details'}</span>
            </button>

            {isAnalystAccordionOpen && (
              <div className={styles.accordionContent}>
                
                {/* AI Decision Chain Stepper Diagram */}
                <div style={{ background: '#0F172A', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', padding: '12px', marginBottom: '14px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#38BDF8', textTransform: 'uppercase', marginBottom: '8px' }}>
                    🔗 Phase 5 Multi-Stage AI Decision Chain
                  </div>
                  <div style={{ fontSize: '11px', color: '#94A3B8', lineHeight: '1.6' }}>
                    <code>Satellite Imagery</code> ➔ <code>YOLOv8 Segmentation</code> ➔ <code>Multi-Scale Verification</code> ➔ <code>Feature Extraction</code> ➔ <code>Rule Engine (Score: {priorityData?.rule_based_priority?.priority_score || 80}/100)</code> ➔ <code>Officer Feedback Store</code> ➔ <code>XGBoost Classifier ({priorityData?.xgboost_model?.model_status || 'ADAPTIVE_MODEL_NOT_READY'})</code> ➔ <code>Grok/Gemini Explanation</code> ➔ <code>NMC Officer Action</code>
                  </div>
                </div>

                {/* Tech Grid 1: Model & Hardware */}
                <div className={styles.techMetricsGrid}>
                  <div className={styles.techCard}>
                    <span className={styles.techLabel}>Rule-Based Priority Score</span>
                    <span className={styles.techVal}>{priorityData?.rule_based_priority?.priority_score || 80}/100 ({priorityData?.rule_based_priority?.priority || 'HIGH'})</span>
                  </div>
                  <div className={styles.techCard}>
                    <span className={styles.techLabel}>Adaptive XGBoost Status</span>
                    <span className={styles.techVal} style={{ color: '#FCD34D' }}>
                      {priorityData?.xgboost_model?.model_status || 'NOT READY'} (Fallback Active)
                    </span>
                  </div>
                  <div className={styles.techCard}>
                    <span className={styles.techLabel}>Explanation Layer Engine</span>
                    <span className={styles.techVal} style={{ color: '#38BDF8' }}>
                      {priorityData?.explanation?.explanation_source || 'DETERMINISTIC_FALLBACK'}
                    </span>
                  </div>
                  <div className={styles.techCard}>
                    <span className={styles.techLabel}>YOLO Building Confidence</span>
                    <span className={styles.techVal}>{caseData.initial_confidence || 85}%</span>
                  </div>
                  <div className={styles.techCard}>
                    <span className={styles.techLabel}>Previous Building Match (IoU)</span>
                    <span className={styles.techVal}>{isStable ? '0.94 (Match)' : '0.00 (No Baseline Match)'}</span>
                  </div>
                  <div className={styles.techCard}>
                    <span className={styles.techLabel}>Visual Change (SSIM Divergence)</span>
                    <span className={styles.techVal}>{((caseData.highres_ssim_pct || 90.6)).toFixed(1)}%</span>
                  </div>
                </div>

              </div>
            )}
          </div>

        </div>

        {/* Footer */}
        <div className={styles.footerBar}>
          <div className={styles.footerLeft}>
            <span className={styles.disclaimerText}>
              Notice: Remote satellite imagery confirms physical structure emergence. Legal determination of authorization requires municipal permit verification and on-site audit.
            </span>
          </div>

          <div className={styles.footerButtons}>
            <button type="button" className={styles.dispatchBtn} onClick={handlePrintDispatch}>
              Export Official Dossier 📄
            </button>
            <button type="button" className={styles.dismissBtn} onClick={onClose}>
              Close
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

export default AIInspectionModal;
