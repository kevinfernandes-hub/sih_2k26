import React from 'react';
import styles from './AgentProgressModal.module.css';

export function AgentProgressModal({
  isOpen,
  logs = [],
  currentStep = 0,
  totalSteps = 10,
  statusText = '',
  locationName = '',
  isFinished = false,
  errorMessage = '',
  onClose,
  onViewCase
}) {
  if (!isOpen) return null;

  const progressPct = Math.min(100, Math.round((currentStep / totalSteps) * 100));

  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true" aria-labelledby="agent-title">
      <div className={styles.modalContent}>
        {/* Header */}
        <div className={styles.modalHeader}>
          <div className={styles.titleGroup}>
            <div className={styles.agentBadge}>
              <span className={styles.pulseDot} />
              EARTHWATCH AGENT
            </div>
            <h2 id="agent-title" className={styles.title}>
              {isFinished
                ? `Investigation Complete: ${locationName}`
                : `Autonomous Change Audit: ${locationName || 'Nagpur AOI'}`}
            </h2>
          </div>
          {isFinished && (
            <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close modal">
              &times;
            </button>
          )}
        </div>

        {/* Progress Bar */}
        <div className={styles.progressContainer}>
          <div className={styles.progressBarWrapper}>
            <div
              className={`${styles.progressBar} ${isFinished ? styles.progressFinished : ''}`}
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <div className={styles.progressMeta}>
            <span className={styles.stepCounter}>
              Step {currentStep} of {totalSteps}
            </span>
            <span className={styles.statusLabel}>{isFinished ? '100% Verified' : `${progressPct}% Complete`}</span>
          </div>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className={styles.errorBanner} role="alert">
            <span className={styles.errorIcon}>⚠️</span>
            <div className={styles.errorInfo}>
              <strong>Investigation Notice</strong>
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Step by Step Execution Logs */}
        <div className={styles.logsList} role="log" aria-live="polite">
          {logs.map((log, idx) => {
            const isDone = log.status === 'DONE';
            const isCurrent = log.status === 'IN_PROGRESS';

            return (
              <div
                key={idx}
                className={`${styles.logItem} ${isDone ? styles.logDone : isCurrent ? styles.logActive : ''}`}
              >
                <div className={styles.logIndicator}>
                  {isDone ? (
                    <span className={styles.checkIcon}>✓</span>
                  ) : isCurrent ? (
                    <span className={styles.spinner} />
                  ) : (
                    <span className={styles.pendingDot} />
                  )}
                </div>
                <div className={styles.logBody}>
                  <div className={styles.logTitleRow}>
                    <span className={styles.logTitle}>{log.title}</span>
                    <span className={styles.logStepNumber}>Step {log.step}</span>
                  </div>
                  {log.detail && <p className={styles.logDetail}>{log.detail}</p>}
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Footer */}
        <div className={styles.modalFooter}>
          <div className={styles.footerNote}>
            <span>Workflow: SEARCH → PLAN → SCAN → REASON → ZOOM → VERIFY → CROSS-CHECK → REPORT</span>
          </div>
          {isFinished ? (
            <div className={styles.footerActions}>
              <button type="button" className={styles.dismissBtn} onClick={onClose}>
                Back to Map
              </button>
              <button
                type="button"
                className={styles.viewCaseBtn}
                onClick={() => {
                  onClose();
                  if (onViewCase) onViewCase();
                }}
              >
                🔍 Inspect High-Res Hotspot & Export Dossier →
              </button>
            </div>
          ) : (
            <div className={styles.executingText}>
              <span className={styles.spinnerMini} />
              Executing tool pipeline on Copernicus CDSE & Esri Wayback...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AgentProgressModal;
