import React, { useState, useEffect, useRef } from 'react';
import styles from './AIInsightCard.module.css';

const CONFIDENCE_CONFIG = {
  HIGH:   { color: '#34D399', bg: 'rgba(52, 211, 153, 0.10)', border: 'rgba(52, 211, 153, 0.25)', label: 'High Confidence' },
  MEDIUM: { color: '#FBBF24', bg: 'rgba(251, 191, 36, 0.10)',  border: 'rgba(251, 191, 36, 0.25)', label: 'Medium Confidence' },
  LOW:    { color: '#F87171', bg: 'rgba(248, 113, 113, 0.10)', border: 'rgba(248, 113, 113, 0.25)', label: 'Low Confidence' },
};

/**
 * Animated typewriter effect that renders text character by character.
 */
function TypewriterText({ text, speed = 14, onDone }) {
  const [displayed, setDisplayed] = useState('');
  const idx = useRef(0);

  useEffect(() => {
    setDisplayed('');
    idx.current = 0;
    if (!text) return;

    const timer = setInterval(() => {
      if (idx.current < text.length) {
        setDisplayed(text.slice(0, idx.current + 1));
        idx.current++;
      } else {
        clearInterval(timer);
        onDone?.();
      }
    }, speed);

    return () => clearInterval(timer);
  }, [text, speed]);

  return <span>{displayed}<span className={styles.cursor}>|</span></span>;
}

export function AIInsightCard({
  location,
  selectedTier,
  hotspots = [],
  isStable = false,
}) {
  const [status, setStatus]       = useState('idle'); // idle | loading | done | error
  const [narrative, setNarrative] = useState(null);
  const [phase, setPhase]         = useState(0);       // 0=analysis typing, 1=prediction typing, 2=done

  const isHighRes = selectedTier === '0.6m';
  const tier06    = location?.tiers?.['0.6m'];
  const tier10    = location?.tiers?.['10m'];

  const infraPct    = isHighRes ? (tier06?.infraPct    ?? 0) : (tier10?.colorDiffPct ?? 0);
  const vegLossPct  = isHighRes ? (tier06?.vegLossPct  ?? 0) : 0;
  const vegGainPct  = isHighRes ? (tier06?.vegGainPct  ?? 0) : 0;
  const ssimScore   = isHighRes ? (tier06?.ssimScore   ?? 0.85) : (tier10?.ssimScore ?? 0.85);
  const ssimPct     = isHighRes ? (tier06?.ssimPct     ?? 0)    : (tier10?.ssimPct ?? 0);
  const beforeDate  = isHighRes ? (tier06?.beforeDate  ?? '2019-01-31') : (tier10?.beforeDate ?? '2022-01-01');
  const afterDate   = isHighRes ? (tier06?.afterDate   ?? '2025-01-30') : (tier10?.afterDate  ?? '2025-01-30');

  const hotspotTypes = hotspots
    .map(h => h.change_type_label || h.changeType || '')
    .filter(Boolean)
    .slice(0, 5);

  const handleGenerate = async () => {
    setStatus('loading');
    setNarrative(null);
    setPhase(0);

    try {
      const res = await fetch('/api/narrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location_name:  location?.name   || 'Unknown Location',
          before_date:    beforeDate,
          after_date:     afterDate,
          infra_pct:      infraPct,
          veg_loss_pct:   vegLossPct,
          veg_gain_pct:   vegGainPct,
          ssim_score:     ssimScore,
          ssim_pct:       ssimPct,
          tier:           selectedTier,
          hotspot_count:  hotspots.length,
          hotspot_types:  hotspotTypes,
          is_stable:      isStable,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setNarrative(data);
      setStatus('done');
    } catch (err) {
      console.error('[AIInsightCard] narrate error:', err);
      setStatus('error');
    }
  };

  const conf = narrative?.confidence ? CONFIDENCE_CONFIG[narrative.confidence] : null;

  return (
    <div className={styles.card}>
      {/* Header */}
      <div className={styles.cardHeader}>
        <div className={styles.headerLeft}>
          <span className={styles.sparkle}>✦</span>
          <span className={styles.cardTitle}>AI Change Narrative</span>
          <span className={styles.poweredBy}>Gemini Flash</span>
        </div>
        {conf && (
          <span
            className={styles.confBadge}
            style={{ color: conf.color, background: conf.bg, borderColor: conf.border }}
          >
            {conf.label}
          </span>
        )}
      </div>

      {/* Idle state */}
      {status === 'idle' && (
        <div className={styles.idleState}>
          <p className={styles.idleText}>
            Generate a plain-language summary of what changed in this location and what's predicted next.
          </p>
          <button className={styles.generateBtn} onClick={handleGenerate} type="button">
            <span className={styles.btnIcon}>⚡</span>
            <span>Generate AI Insight</span>
          </button>
        </div>
      )}

      {/* Loading */}
      {status === 'loading' && (
        <div className={styles.loadingState}>
          <div className={styles.loadingOrbs}>
            <span className={styles.orb} style={{ animationDelay: '0s' }} />
            <span className={styles.orb} style={{ animationDelay: '0.18s' }} />
            <span className={styles.orb} style={{ animationDelay: '0.36s' }} />
          </div>
          <span className={styles.loadingText}>Analysing satellite metrics…</span>
        </div>
      )}

      {/* Error */}
      {status === 'error' && (
        <div className={styles.errorState}>
          <span className={styles.errorIcon}>⚠</span>
          <span className={styles.errorText}>Could not reach the AI service. Check backend is running.</span>
          <button className={styles.retryBtn} onClick={handleGenerate} type="button">Retry</button>
        </div>
      )}

      {/* Narrative result */}
      {status === 'done' && narrative && (
        <div className={styles.narrativeBody}>

          {/* Tags */}
          {narrative.tags?.length > 0 && (
            <div className={styles.tagRow}>
              {narrative.tags.map((tag, i) => (
                <span key={i} className={styles.tag}>{tag}</span>
              ))}
            </div>
          )}

          {/* What Happened */}
          <div className={styles.section}>
            <div className={styles.sectionLabel}>
              <span className={styles.sectionDot} style={{ background: '#60A5FA' }} />
              What Happened
            </div>
            <p className={styles.sectionText}>
              {phase === 0
                ? <TypewriterText text={narrative.analysis} speed={10} onDone={() => setPhase(1)} />
                : narrative.analysis}
            </p>
          </div>

          {/* Prediction */}
          {phase >= 1 && (
            <div className={styles.section}>
              <div className={styles.sectionLabel}>
                <span className={styles.sectionDot} style={{ background: '#A78BFA' }} />
                Prediction (12–24 months)
              </div>
              <p className={styles.sectionText}>
                {phase === 1
                  ? <TypewriterText text={narrative.prediction} speed={10} onDone={() => setPhase(2)} />
                  : narrative.prediction}
              </p>
            </div>
          )}

          {/* Regenerate */}
          {phase >= 2 && (
            <button className={styles.regenBtn} onClick={handleGenerate} type="button">
              ↻ Regenerate
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default AIInsightCard;
