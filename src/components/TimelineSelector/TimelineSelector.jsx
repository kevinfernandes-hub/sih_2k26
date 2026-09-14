import React, { useState, useEffect, useMemo } from 'react';
import styles from './TimelineSelector.module.css';

export function TimelineSelector({
  location,
  onAnalyzeDates,
  isAnalyzing,
  currentBeforeDate,
  currentAfterDate,
  onResetDates
}) {
  const [availableDates, setAvailableDates] = useState([]);
  const [isLoadingDates, setIsLoadingDates] = useState(false);
  const [errorLoadingDates, setErrorLoadingDates] = useState(false);
  const [selectedBefore, setSelectedBefore] = useState(currentBeforeDate || '2022-01-15');
  const [selectedAfter, setSelectedAfter] = useState(currentAfterDate || '2025-01-27');
  const [hoveredDate, setHoveredDate] = useState(null);

  // Synchronize when current dates or location change
  useEffect(() => {
    if (currentBeforeDate) setSelectedBefore(currentBeforeDate);
    if (currentAfterDate) setSelectedAfter(currentAfterDate);
  }, [currentBeforeDate, currentAfterDate, location?.id]);

  // Fetch available dates from backend catalog API
  useEffect(() => {
    if (!location?.coordinates) return;
    const [lat, lng] = location.coordinates;

    setIsLoadingDates(true);
    setErrorLoadingDates(false);

    const controller = new AbortController();
    fetch(`/api/available-dates?lat=${lat}&lng=${lng}&start_date=2020-01-01&end_date=2025-03-01`, {
      signal: controller.signal
    })
      .then((res) => (res.ok ? res.json() : Promise.reject(res)))
      .then((data) => {
        if (data?.dates && Array.isArray(data.dates)) {
          setAvailableDates(data.dates);
        } else {
          setAvailableDates([]);
        }
        setIsLoadingDates(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          console.warn('Could not load catalog dates:', err);
          setErrorLoadingDates(true);
          setIsLoadingDates(false);
        }
      });

    return () => controller.abort();
  }, [location?.coordinates]);

  // Min and max timestamps for horizontal positioning
  const { minTime, maxTime, totalDuration } = useMemo(() => {
    if (availableDates.length === 0) {
      const min = new Date('2020-01-01').getTime();
      const max = new Date('2025-03-01').getTime();
      return { minTime: min, maxTime: max, totalDuration: max - min };
    }
    const min = new Date(availableDates[0].date).getTime();
    const max = new Date(availableDates[availableDates.length - 1].date).getTime();
    return { minTime: min, maxTime: max, totalDuration: Math.max(1, max - min) };
  }, [availableDates]);

  // Check if selected dates are < 90 days apart
  const isShortInterval = useMemo(() => {
    if (!selectedBefore || !selectedAfter) return false;
    const d1 = new Date(selectedBefore).getTime();
    const d2 = new Date(selectedAfter).getTime();
    const diffDays = Math.abs(d2 - d1) / (1000 * 60 * 60 * 24);
    return diffDays < 90;
  }, [selectedBefore, selectedAfter]);

  const handleDateClick = (dateItem) => {
    if (!dateItem.usable) return;

    const clickedDate = dateItem.date;
    const clickedTime = new Date(clickedDate).getTime();
    const beforeTime = new Date(selectedBefore).getTime();

    // If clicking earlier than before, or if user wants to reset before
    if (clickedTime <= beforeTime) {
      setSelectedBefore(clickedDate);
    } else {
      setSelectedAfter(clickedDate);
    }
  };

  const handleApply = () => {
    if (!selectedBefore || !selectedAfter || isAnalyzing) return;

    // Ensure chronological order
    let b = selectedBefore;
    let a = selectedAfter;
    if (new Date(b).getTime() > new Date(a).getTime()) {
      [b, a] = [a, b];
    }
    onAnalyzeDates(b, a);
  };

  return (
    <div className={styles.timelineContainer} aria-label="Sentinel-2 Satellite Pass Timeline">
      <div className={styles.headerRow}>
        <div className={styles.titleGroup}>
          <span className={styles.title}>Sentinel-2 Satellite Passes</span>
          <span className={styles.subtitle}>
            {isLoadingDates
              ? 'Querying CDSE Archive...'
              : `${availableDates.filter((d) => d.usable).length} usable passes (<15% cloud cover)`}
          </span>
        </div>

        {/* Selected Date Badges */}
        <div className={styles.selectionGroup}>
          <div className={styles.datePill}>
            <span className={`${styles.roleBadge} ${styles.beforeBadge}`}>B</span>
            <span className={styles.dateText}>{selectedBefore}</span>
          </div>
          <span className={styles.arrowIcon}>&rarr;</span>
          <div className={styles.datePill}>
            <span className={`${styles.roleBadge} ${styles.afterBadge}`}>A</span>
            <span className={styles.dateText}>{selectedAfter}</span>
          </div>

          <button
            type="button"
            className={styles.analyzeBtn}
            onClick={handleApply}
            disabled={isAnalyzing || isLoadingDates}
            title="Fetch and analyze satellite imagery for this exact date pair"
          >
            {isAnalyzing ? 'Analyzing...' : 'Analyze Custom Pair'}
          </button>

          {onResetDates && (
            <button
              type="button"
              className={styles.resetBtn}
              onClick={onResetDates}
              title="Reset to default seasonal baseline"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {isShortInterval && (
        <div className={styles.shortIntervalNotice}>
          <span>ⓘ</span>
          <span>Selected dates are &lt;90 days apart. Physical ground alterations may be subtle over short time spans.</span>
        </div>
      )}

      {/* Interactive Timeline Track */}
      <div className={styles.trackWrapper}>
        <div className={styles.timelineTrack}>
          {/* Year Grid Lines */}
          {['2020', '2021', '2022', '2023', '2024', '2025'].map((year) => {
            const yrTime = new Date(`${year}-01-01`).getTime();
            const pct = Math.max(0, Math.min(100, ((yrTime - minTime) / totalDuration) * 100));
            return (
              <div key={year} className={styles.yearMarker} style={{ left: `${pct}%` }}>
                <span className={styles.yearLabel}>{year}</span>
              </div>
            );
          })}

          {/* Active Range Highlight */}
          {selectedBefore && selectedAfter && (
            <div
              className={styles.rangeHighlight}
              style={{
                left: `${Math.max(
                  0,
                  ((new Date(selectedBefore).getTime() - minTime) / totalDuration) * 100
                )}%`,
                width: `${Math.max(
                  0.5,
                  ((new Date(selectedAfter).getTime() - new Date(selectedBefore).getTime()) /
                    totalDuration) *
                    100
                )}%`
              }}
            />
          )}

          {/* Date Points */}
          {availableDates.map((item) => {
            const itemTime = new Date(item.date).getTime();
            const pct = Math.max(0, Math.min(100, ((itemTime - minTime) / totalDuration) * 100));
            const isBefore = item.date === selectedBefore;
            const isAfter = item.date === selectedAfter;
            const isSelected = isBefore || isAfter;

            return (
              <div
                key={item.date}
                className={`${styles.dateDot} ${item.usable ? styles.usable : styles.cloudy} ${
                  isSelected ? styles.selectedDot : ''
                }`}
                style={{ left: `${pct}%` }}
                onClick={() => handleDateClick(item)}
                onMouseEnter={() => setHoveredDate(item)}
                onMouseLeave={() => setHoveredDate(null)}
                tabIndex={item.usable ? 0 : -1}
                role="button"
                aria-label={`Sentinel-2 pass on ${item.date}, ${item.cloud_cover}% cloud cover`}
              >
                {isSelected && (
                  <span className={`${styles.dotTag} ${isBefore ? styles.beforeTag : styles.afterTag}`}>
                    {isBefore ? 'B' : 'A'}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Hover Tooltip */}
        {hoveredDate && (
          <div className={styles.hoverTooltip}>
            <strong>{hoveredDate.date}</strong> — Cloud cover:{' '}
            <span style={{ color: hoveredDate.usable ? 'var(--status-stable)' : 'var(--accent-primary)' }}>
              {hoveredDate.cloud_cover}%
            </span>
            {!hoveredDate.usable && (
              <span className={styles.cloudyWarning}> (Too cloudy for change analysis &ge;15%)</span>
            )}
            {hoveredDate.usable && <span className={styles.clickHint}> &bull; Click to select</span>}
          </div>
        )}
      </div>

      {errorLoadingDates && (
        <div className={styles.errorNotice}>
          Could not load satellite catalog passes for this coordinate. You can still run baseline analysis.
        </div>
      )}
    </div>
  );
}
