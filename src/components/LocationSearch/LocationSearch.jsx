import React, { useState, useRef, useEffect } from 'react';
import styles from './LocationSearch.module.css';

export function LocationSearch({
  locations,
  selectedLocation,
  searchQuery,
  onSearchChange,
  onSelectLocation,
  onRequestLiveAnalysis,
  isScanning,
  errorMessage,
  onClearError,
  canAnalyzeSelectedLocation = false
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [locationInput, setLocationInput] = useState('');
  const containerRef = useRef(null);

  // Sync input value with the currently selected location
  useEffect(() => {
    if (selectedLocation) {
      setLocationInput(selectedLocation.name);
    }
  }, [selectedLocation]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredLocations = locations.filter((loc) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    const tokens = q.replace(/[^a-z0-9]/g, ' ').split(/\s+/).filter(Boolean);
    const locText = (loc.name + " " + (loc.subtitle || "") + " " + loc.id).toLowerCase().replace(/[^a-z0-9]/g, " ");
    return tokens.every((token) => locText.includes(token));
  });

  const handleAgentSubmit = (e) => {
    e.preventDefault();
    const query = locationInput.trim() || searchQuery.trim() || selectedLocation?.name;
    console.log('[FETCH] button clicked', { query, isScanning, selectedLocation });
    if (!query || isScanning) return;
    onRequestLiveAnalysis(query);
    setIsOpen(false);
  };

  const matchingExistingLocation = filteredLocations.find((location) => {
    const tokens = locationInput.toLowerCase().replace(/[^a-z0-9]/g, ' ').split(/\s+/).filter(Boolean);
    const locationText = `${location.name} ${location.subtitle || ''} ${location.id}`.toLowerCase().replace(/[^a-z0-9]/g, ' ');
    return tokens.length > 0 && tokens.every((token) => locationText.includes(token));
  });
  
  // Use selected location if no explicit input is being typed
  const effectiveLocation = locationInput.trim() ? matchingExistingLocation : selectedLocation;
  
  const hasImagery = effectiveLocation?.imageryAvailable;
  const isComplete = effectiveLocation?.analysisComplete;

  let buttonText = 'FETCH SATELLITE IMAGERY';
  if (isScanning) {
    buttonText = 'ANALYZING...';
  } else if (isComplete) {
    buttonText = 'ANALYSIS COMPLETE';
  } else if (hasImagery) {
    buttonText = 'ANALYZE AREA';
  }

  return (
    <div className={styles.searchContainer} ref={containerRef}>
      {/* Optional AOI browser */}
      <form onSubmit={handleAgentSubmit} className={styles.agentSearchForm}>
        <div className={styles.inputWrapper}>
          <svg className={styles.searchIcon} viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
              clipRule="evenodd"
            />
          </svg>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Browse a demo AOI or enter a location..."
            value={locationInput}
            onChange={(e) => {
              setLocationInput(e.target.value);
              onSearchChange(e.target.value);
              setIsOpen(true);
              if (onClearError) onClearError();
            }}
            onFocus={() => setIsOpen(true)}
            disabled={isScanning}
            aria-label="Browse satellite analysis area"
          />
          {locationInput && (
            <button
              type="button"
              className={styles.clearBtn}
              onClick={() => {
                setLocationInput('');
                onSearchChange('');
                setIsOpen(false);
              }}
              aria-label="Clear search"
            >
              &times;
            </button>
          )}
        </div>

        <button
          type="submit"
          className={styles.runAgentBtn}
          disabled={!locationInput.trim() || isScanning}
          title="Run pipeline for the selected area"
        >
          {isScanning ? (
            <>
              <span className={styles.spinnerMini} />
              <span>{buttonText}</span>
            </>
          ) : (
            <>
              <span className={styles.agentSparkle}>⚡</span>
              <span>{buttonText}</span>
            </>
          )}
        </button>
      </form>

      {/* Error Notice */}
      {errorMessage && (
        <div className={styles.errorBanner} role="alert">
          <div className={styles.errorHeader}>
            <span className={styles.errorTitle}>Analysis Notice</span>
            <button type="button" className={styles.errorClose} onClick={onClearError}>
              &times;
            </button>
          </div>
          <span className={styles.errorText}>{errorMessage}</span>
        </div>
      )}

      {/* Autocomplete / Recent AOI Dropdown */}
      {isOpen && locationInput && (
        <div className={styles.dropdown}>
          {filteredLocations.length > 0 ? (
            <>
              <div className={styles.dropdownHeader}>Available demo areas</div>
              {filteredLocations.map((loc) => (
                <div
                  key={loc.id}
                  className={styles.dropdownItem}
                  onClick={() => {
                    onSelectLocation(loc.id);
                    setLocationInput(loc.name);
                    setIsOpen(false);
                  }}
                >
                  <div className={styles.dropdownItemHeader}>
                    <span className={styles.dropdownName}>{loc.name}</span>
                    <span className={`${styles.statusDot} ${styles[loc.status]}`} />
                  </div>
                  <span className={styles.dropdownSubtitle}>{loc.subtitle}</span>
                </div>
              ))}
            </>
          ) : null}

          {/* Prompt to analyze a new area */}
          <div className={styles.dynamicPromptCard}>
            <span className={styles.dynamicPromptText}>
              Analyze satellite imagery for <strong>&ldquo;{locationInput}&rdquo;</strong>
            </span>
            <button
              type="button"
              className={styles.triggerDynamicAgentBtn}
              onClick={() => {
                onRequestLiveAnalysis(locationInput);
                setIsOpen(false);
              }}
              >
              Run change analysis for &ldquo;{locationInput}&rdquo; &rarr;
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default LocationSearch;
