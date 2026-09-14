import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Rectangle, Polygon, useMap } from 'react-leaflet';
import L from 'leaflet';
import styles from './LocationMap.module.css';

/**
 * Controller to smoothly center map when selected location or hotspot changes
 */
function MapCenterController({ selectedLocation, selectedHotspot }) {
  const map = useMap();

  useEffect(() => {
    if (selectedHotspot?.latitude && selectedHotspot?.longitude) {
      map.setView([selectedHotspot.latitude, selectedHotspot.longitude], Math.max(map.getZoom(), 14), {
        animate: true,
        duration: 0.6
      });
    } else if (selectedLocation?.coordinates) {
      map.setView(selectedLocation.coordinates, Math.max(map.getZoom(), 12), {
        animate: true,
        duration: 0.8
      });
    }
  }, [selectedLocation, selectedHotspot, map]);

  return null;
}

/**
 * Generates custom minimalist SVG pin icon for sector locations
 */
function createCustomPin(status, isSelected, isPreview) {
  let fillColor = '#C96F3E'; // flagged / default
  if (status === 'stable') fillColor = '#3D8B7A';
  if (status === 'elevated') fillColor = '#C98638';

  const pulseRing = isSelected
    ? `<div style="position: absolute; top: -4px; left: -4px; width: 26px; height: 26px; border-radius: 50%; border: 2px solid ${fillColor}; opacity: 0.6; animation: pinPulse 2s infinite ease-out;"></div>`
    : '';

  const dashedClass = isPreview ? 'border-style: dashed;' : '';

  const html = `
    <div style="position: relative; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center;">
      ${pulseRing}
      <div style="
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: ${fillColor};
        border: 2px solid #FFFFFF;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
        cursor: pointer;
        transition: transform 0.15s ease;
        ${dashedClass}
        transform: ${isSelected ? 'scale(1.3)' : 'scale(1)'};
      "></div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-map-pin',
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    popupAnchor: [0, -10]
  });
}

/**
 * Generates priority badge pin icon for candidate hotspots
 */
function createHotspotPin(priority, isSelected, label) {
  let bgColor = '#EA580C'; // HIGH
  if (priority === 'CRITICAL') bgColor = '#DC2626';
  if (priority === 'MEDIUM') bgColor = '#D97706';
  if (priority === 'LOW') bgColor = '#16A34A';

  const pulse = isSelected
    ? `<div style="position: absolute; top: -3px; left: -3px; width: 28px; height: 28px; border-radius: 50%; border: 2px solid ${bgColor}; animation: pinPulse 1.5s infinite ease-out;"></div>`
    : '';

  const html = `
    <div style="position: relative; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;">
      ${pulse}
      <div style="
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: ${bgColor};
        border: 2px solid #FFFFFF;
        box-shadow: 0 2px 8px rgba(0,0,0,0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        font-weight: bold;
        font-size: 8px;
        font-family: monospace;
        cursor: pointer;
        transform: ${isSelected ? 'scale(1.25)' : 'scale(1)'};
      ">🎯</div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'hotspot-map-pin',
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -12]
  });
}

export function LocationMap({
  locations,
  selectedLocation,
  onSelectLocation,
  hotspots = [],
  selectedHotspotId,
  onSelectHotspot,
  onInspectHotspot
}) {
  const defaultCenter = [21.1458, 79.0882];
  const defaultZoom = 12;

  const selectedHotspot = hotspots.find((h) => h.hotspot_id === selectedHotspotId);

  // Compute AOI boundary rectangle if available
  let aoiBounds = null;
  if (selectedLocation?.coordinates) {
    const [lat, lng] = selectedLocation.coordinates;
    const padding = 0.024;
    aoiBounds = [
      [lat - padding, lng - padding],
      [lat + padding, lng + padding]
    ];
  }

  return (
    <div className={styles.mapWrapper} aria-label="Nagpur Sector Geospatial Map">
      <MapContainer
        center={selectedLocation?.coordinates || defaultCenter}
        zoom={defaultZoom}
        scrollWheelZoom={true}
        className={styles.mapCanvas}
        zoomControl={true}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
          maxZoom={19}
        />

        <MapCenterController
          selectedLocation={selectedLocation}
          selectedHotspot={selectedHotspot}
        />

        {/* AOI Analysis Boundary Rectangle */}
        {aoiBounds && (
          <Rectangle
            bounds={aoiBounds}
            pathOptions={{
              color: 'var(--accent-primary, #C96F3E)',
              weight: 1.5,
              dashArray: '4, 4',
              fillColor: 'var(--accent-primary, #C96F3E)',
              fillOpacity: 0.04
            }}
          />
        )}

        {/* Selected Candidate Detailed Hotspot Polygons */}
        {selectedHotspot?.hotspots?.map((h, hIdx) => {
          if (!h.polygon_wgs84 || h.polygon_wgs84.length < 3) return null;
          // Leaflet expects [lat, lon], our polygon_wgs84 is [lon, lat]
          const leafletPositions = h.polygon_wgs84.map(pt => [pt[1], pt[0]]);
          
          let pColor = '#EA580C';
          let pFill = '#EA580C';
          if (h.change_type === 'NEW') { pColor = '#283CEB'; pFill = '#283CEB'; }
          else if (h.change_type === 'EXPANDED') { pColor = '#1E8CF0'; pFill = '#1E8CF0'; }

          return (
            <Polygon
              key={`hs-poly-${hIdx}`}
              positions={leafletPositions}
              pathOptions={{
                color: pColor,
                weight: 2,
                fillColor: pFill,
                fillOpacity: 0.35
              }}
            >
              <Popup className={styles.popupCustom}>
                <div className={styles.popupContent}>
                  <strong>{h.hotspot_id || h.change_type_label || 'Detected Change'}</strong>
                  <span>Area: {h.area_formatted || `${h.area_m2} m²`}</span>
                </div>
              </Popup>
            </Polygon>
          );
        })}

        {/* Vector Ground Change Polygons */}
        {(selectedLocation?.polygons || selectedLocation?.aiInspection?.polygons || selectedLocation?.fieldReport?.polygons || []).map((poly, pIdx) => {
          if (!poly?.coordinates || poly.coordinates.length < 3) return null;
          return (
            <Polygon
              key={poly.polygon_id || pIdx}
              positions={poly.coordinates}
              pathOptions={{
                color: '#DC2626',
                weight: 2,
                fillColor: '#EA580C',
                fillOpacity: 0.28
              }}
            >
              <Popup className={styles.popupCustom}>
                <div className={styles.popupContent}>
                  <strong>{poly.polygon_id || 'Ground Change Polygon'}</strong>
                  <span>Calculated Area: {poly.area_m2?.toLocaleString()} m²</span>
                  <span style={{ fontSize: '10px', color: '#64748B' }}>Cadastral Contour Vector</span>
                </div>
              </Popup>
            </Polygon>
          );
        })}

        {/* Sector Locations Markers */}
        {locations.map((loc) => {
          if (!loc.coordinates) return null;
          const isSelected = loc.id === selectedLocation?.id;
          const icon = createCustomPin(loc.status, isSelected, loc.isPreview);

          return (
            <Marker
              key={loc.id}
              position={loc.coordinates}
              icon={icon}
              eventHandlers={{
                click: () => onSelectLocation(loc.id)
              }}
            >
              <Popup className={styles.popupCustom}>
                <div className={styles.popupContent}>
                  <strong>{loc.name}</strong>
                  <span>{loc.coords}</span>
                  <div className={styles.popupStats}>
                    <span>Δ {loc.colorDiff?.toFixed(2)}%</span>
                    <span>SSIM {(loc.ssimArea || 9.2).toFixed(1)}%</span>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Candidate Hotspot Markers */}
        {hotspots.map((h) => {
          if (!h.latitude || !h.longitude) return null;
          const isSelected = h.hotspot_id === selectedHotspotId;
          const icon = createHotspotPin(h.priority, isSelected, h.hotspot_id);

          return (
            <Marker
              key={h.hotspot_id}
              position={[h.latitude, h.longitude]}
              icon={icon}
              eventHandlers={{
                click: () => {
                  if (onSelectHotspot) onSelectHotspot(h.hotspot_id);
                }
              }}
            >
              <Popup className={styles.popupCustom}>
                <div className={styles.popupContent}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: 'bold', color: 'var(--accent-primary)' }}>{h.hotspot_id}</span>
                    <span style={{ fontSize: '9px', fontWeight: 'bold', background: h.priority === 'CRITICAL' ? '#FEE2E2' : '#FFEDD5', color: h.priority === 'CRITICAL' ? '#DC2626' : '#EA580C', padding: '1px 5px', borderRadius: '3px' }}>
                      {h.priority}
                    </span>
                  </div>
                  <strong>{h.name}</strong>
                  <span>Area: {h.area_formatted || `${h.area_m2} m²`}</span>
                  <span>Confidence: {h.final_confidence || h.initial_confidence || 82}%</span>
                  {onInspectHotspot && (
                    <button
                      type="button"
                      style={{
                        marginTop: '6px',
                        background: 'var(--accent-primary, #C96F3E)',
                        color: '#FFFFFF',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '4px 8px',
                        fontSize: '10px',
                        fontWeight: 'bold',
                        cursor: 'pointer'
                      }}
                      onClick={() => onInspectHotspot(h.hotspot_id)}
                    >
                      Analyze change
                    </button>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Map Legend Bar */}
      <div className={styles.mapLegend}>
        <span className={styles.legendItem}>
          <span className={`${styles.legendDot} ${styles.stableDot}`} /> Reference
        </span>
        <span className={styles.legendItem}>
          <span className={`${styles.legendDot} ${styles.elevatedDot}`} /> Elevated change
        </span>
        <span className={styles.legendItem}>
          <span className={`${styles.legendDot} ${styles.flaggedDot}`} /> Flagged change
        </span>
        <span className={styles.legendItem} style={{ color: '#DC2626' }}>
          🎯 Hotspot
        </span>
      </div>
    </div>
  );
}

export default LocationMap;
