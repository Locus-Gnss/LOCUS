import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, useMap } from 'react-leaflet';
import { MapPin, Navigation, Eye, AlertTriangle, Key, Layers, Globe, Settings, ExternalLink, RefreshCw, CheckCircle2 } from 'lucide-react';

/**
 * Helper component that manages Leaflet map instance lifecycle,
 * handles viewport re-centering when events change, and invalidates size on resize.
 */
function MapController({ center, validPoints }) {
  const map = useMap();

  // Re-center when centerPos changes (e.g. user selects a different forensic event)
  useEffect(() => {
    if (center && !isNaN(center[0]) && !isNaN(center[1]) && center[0] !== 0 && center[1] !== 0) {
      map.setView(center, map.getZoom(), { animate: true });
    }
  }, [center, map]);

  // Invalidate size on initial mount and when container dimensions change
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 120);

    const container = map.getContainer();
    let resizeObserver = null;
    if (container && window.ResizeObserver) {
      resizeObserver = new ResizeObserver(() => {
        map.invalidateSize();
      });
      resizeObserver.observe(container);
    }

    return () => {
      clearTimeout(timer);
      if (resizeObserver) resizeObserver.disconnect();
    };
  }, [map]);

  return null;
}

export default function MapView({ telemetryHistory = [], bundle }) {
  const [showPolyline, setShowPolyline] = useState(true);
  // Default basemap is CARTO Dark per specifications
  const [basemap, setBasemap] = useState('carto'); // 'carto' | 'satellite' | 'cyber_dark'

  // Load API key from Vite environment variable or localStorage
  const envKey = (import.meta.env.VITE_CARTO_API_KEY || import.meta.env.VITE_MAP_TOKEN || '').trim();
  const [cartoApiKey, setCartoApiKey] = useState(() => localStorage.getItem('locus_carto_api_key') || envKey);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [tempKey, setTempKey] = useState(cartoApiKey);

  // Tile health / error tracking
  const [tileError, setTileError] = useState(false);
  const [tileLoaded, setTileLoaded] = useState(false);

  // Fallback default coordinates if telemetry history is empty
  const defaultPos = [23.1043149, 72.5924906]; // L89HA Test Base
  const hasEventLocation = Boolean(
    bundle?.location?.latitude &&
    bundle?.location?.longitude &&
    Number(bundle.location.latitude) !== 0 &&
    !isNaN(Number(bundle.location.latitude))
  );

  const centerPos = hasEventLocation
    ? [Number(bundle.location.latitude), Number(bundle.location.longitude)]
    : defaultPos;

  // Filter records with valid latitude/longitude
  const validPoints = telemetryHistory
    .filter((r) => r.latitude && r.longitude && Number(r.latitude) !== 0 && !isNaN(Number(r.latitude)))
    .slice(-150);

  const polylineCoords = validPoints.map((r) => [Number(r.latitude), Number(r.longitude)]);

  const handleSaveKey = () => {
    const clean = tempKey.trim();
    localStorage.setItem('locus_carto_api_key', clean);
    setCartoApiKey(clean);
    setShowKeyModal(false);
    setTileError(false);
  };

  const handleClearKey = () => {
    localStorage.removeItem('locus_carto_api_key');
    setCartoApiKey(envKey || '');
    setTempKey(envKey || '');
    setShowKeyModal(false);
    setTileError(false);
  };

  // Determine tile URL & attribution based on selected basemap
  const getTileConfig = () => {
    if (basemap === 'satellite') {
      return {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution: '&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        subdomains: 'abc',
        maxZoom: 19,
        className: ''
      };
    }

    if (basemap === 'cyber_dark') {
      return {
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        subdomains: 'abc',
        maxZoom: 19,
        className: 'map-cyber-dark'
      };
    }

    // Default: Official CARTO Dark Matter raster tiles
    // Supported subdomains: a, b, c, d. If API key is provided, append ?key=KEY
    const keyParam = cartoApiKey ? `?key=${encodeURIComponent(cartoApiKey)}` : '';
    return {
      url: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png${keyParam}`,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 20,
      className: ''
    };
  };

  const tileConfig = getTileConfig();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Map Header Card */}
      <div className="cyber-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <MapPin size={18} color="var(--cyan-primary)" />
              <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.1rem' }}>
                GEOSPATIAL TRAJECTORY TRACKING
              </h2>
            </div>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: '0.2rem' }}>
              High-precision kinematic trajectory tracing. Nominal (Cyan/Green), Degraded HDOP (Amber), Spoofed Teleportation (Red).
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            {/* Basemap Switcher */}
            <div style={{ display: 'flex', gap: '0.25rem', background: 'rgba(5, 8, 16, 0.8)', padding: '0.2rem', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
              <button
                className={`cyber-btn ${basemap === 'carto' ? 'cyber-btn-active' : ''}`}
                onClick={() => { setBasemap('carto'); setTileError(false); }}
                style={{ padding: '0.25rem 0.55rem', fontSize: '0.7rem' }}
                title="Official CARTO Dark Matter Basemap"
              >
                CARTO Dark
              </button>
              <button
                className={`cyber-btn ${basemap === 'satellite' ? 'cyber-btn-active' : ''}`}
                onClick={() => { setBasemap('satellite'); setTileError(false); }}
                style={{ padding: '0.25rem 0.55rem', fontSize: '0.7rem' }}
                title="Orbital Satellite Imagery (ESRI)"
              >
                Satellite
              </button>
              <button
                className={`cyber-btn ${basemap === 'cyber_dark' ? 'cyber-btn-active' : ''}`}
                onClick={() => { setBasemap('cyber_dark'); setTileError(false); }}
                style={{ padding: '0.25rem 0.55rem', fontSize: '0.7rem' }}
                title="Inverted OpenStreetMap Dark Style"
              >
                OSM Inverted
              </button>
            </div>

            {/* API Key Modal Button */}
            <button
              className="cyber-btn"
              onClick={() => { setTempKey(cartoApiKey); setShowKeyModal(true); }}
              style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}
              title="Configure CARTO Map Key"
            >
              <Key size={13} color={cartoApiKey ? 'var(--green-nominal)' : 'var(--cyan-primary)'} />
              <span>{cartoApiKey ? 'CARTO Key: Set' : 'CARTO Key'}</span>
            </button>

            {/* Trajectory Polyline Toggle */}
            <button
              className={`cyber-btn ${showPolyline ? 'cyber-btn-active' : ''}`}
              onClick={() => setShowPolyline(!showPolyline)}
              style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}
            >
              <Navigation size={13} />
              <span>Vector ({polylineCoords.length} pts)</span>
            </button>
          </div>
        </div>

        {/* Tile Error / Fallback Banner */}
        {tileError && basemap === 'carto' && (
          <div style={{
            marginTop: '0.75rem',
            padding: '0.55rem 0.85rem',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid var(--red-critical)',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.78rem',
            color: '#fca5a5'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertTriangle size={15} color="var(--red-critical)" />
              <span>
                CARTO tile loading interrupted. If your network blocks direct tile CDNs, switch to Satellite or OSM Inverted.
              </span>
            </div>
            <button
              className="cyber-btn"
              onClick={() => { setBasemap('satellite'); setTileError(false); }}
              style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem', color: '#fff' }}
            >
              Switch to Satellite
            </button>
          </div>
        )}

        {!hasEventLocation && (
          <div style={{
            marginTop: '0.6rem',
            padding: '0.45rem 0.75rem',
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            borderRadius: '4px',
            fontSize: '0.74rem',
            color: 'var(--amber-warning)'
          }}>
            Note: Active event ({bundle?.event_id || 'None'}) has no fix coordinates in telemetry record. Displaying test base reference.
          </div>
        )}
      </div>

      {/* API Key Configuration Modal */}
      {showKeyModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        }}>
          <div className="cyber-card" style={{ maxWidth: '540px', width: '92%', border: '1px solid var(--cyan-primary)', boxShadow: '0 0 30px rgba(0, 240, 255, 0.25)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Key size={18} color="var(--cyan-primary)" />
                <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem' }}>CARTO BASEMAP KEY CONFIGURATION</h3>
              </div>
              <button
                onClick={() => setShowKeyModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-dim)', marginBottom: '0.85rem', lineHeight: '1.5' }}>
              CARTO Dark Matter raster tiles load openly for non-commercial and evaluation usage. If your organization uses a licensed CARTO account, you can configure your key below or via <code style={{ color: 'var(--cyan-primary)' }}>VITE_CARTO_API_KEY</code> in <code style={{ color: 'var(--cyan-primary)' }}>frontend/.env.local</code>.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.25rem' }}>
              <label style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                CARTO API KEY / TOKEN (Optional):
              </label>
              <input
                type="text"
                className="cyber-input"
                placeholder="Leave blank for public open tiles, or paste CARTO key"
                value={tempKey}
                onChange={(e) => setTempKey(e.target.value)}
                style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}
              />
              <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                Keys are stored locally in browser session storage and never transmitted to external telemetry logs.
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button
                className="cyber-btn"
                onClick={handleClearKey}
                style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}
              >
                Reset / Clear Key
              </button>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button className="cyber-btn" onClick={() => setShowKeyModal(false)}>
                  Cancel
                </button>
                <button className="cyber-btn cyber-btn-active" onClick={handleSaveKey}>
                  Apply Key
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Leaflet Map Card */}
      <div className={`cyber-card ${tileConfig.className}`} style={{ padding: '0.5rem', height: '540px', position: 'relative' }}>
        <div style={{ width: '100%', height: '100%', borderRadius: '6px', overflow: 'hidden' }}>
          <MapContainer
            center={centerPos}
            zoom={16}
            scrollWheelZoom={true}
            style={{ width: '100%', height: '100%', background: '#070b13' }}
          >
            {/* Map Lifecycle & Center Controller */}
            <MapController center={centerPos} validPoints={validPoints} />

            {/* Active Basemap Tile Layer */}
            <TileLayer
              key={basemap + (cartoApiKey || 'open')}
              attribution={tileConfig.attribution}
              url={tileConfig.url}
              subdomains={tileConfig.subdomains || 'abcd'}
              maxZoom={tileConfig.maxZoom || 20}
              eventHandlers={{
                tileerror: (e) => {
                  setTileError(true);
                },
                load: () => {
                  setTileLoaded(true);
                  setTileError(false);
                }
              }}
            />

            {/* Trajectory Polyline */}
            {showPolyline && polylineCoords.length > 1 && (
              <Polyline
                positions={polylineCoords}
                pathOptions={{ color: '#00f0ff', weight: 3, opacity: 0.75, dashArray: '6 6' }}
              />
            )}

            {/* Individual GPS Epoch Waypoints */}
            {validPoints.map((pt, idx) => {
              const isWarning = Number(pt.hdop) > 4.0;
              const isAnomaly = Number(pt.speed_kmh) > 120.0;
              const color = isAnomaly ? '#ef4444' : isWarning ? '#f59e0b' : '#00f0ff';
              const radius = isAnomaly ? 7 : 4;

              return (
                <CircleMarker
                  key={idx}
                  center={[Number(pt.latitude), Number(pt.longitude)]}
                  radius={radius}
                  pathOptions={{
                    fillColor: color,
                    fillOpacity: 0.85,
                    color: color,
                    weight: 1.5
                  }}
                >
                  <Popup>
                    <div style={{ color: '#000', fontSize: '0.8rem', fontFamily: 'monospace' }}>
                      <strong>Epoch #{pt.epoch_id || idx + 1}</strong><br />
                      Time: {pt.timestamp_utc?.slice(11, 19) || 'N/A'}<br />
                      Lat: {Number(pt.latitude).toFixed(6)}°<br />
                      Lon: {Number(pt.longitude).toFixed(6)}°<br />
                      Speed: {Number(pt.speed_kmh || 0).toFixed(1)} km/h<br />
                      HDOP: {Number(pt.hdop || 1).toFixed(2)}<br />
                      Status: {isAnomaly ? 'CRITICAL ANOMALY' : isWarning ? 'WARNING' : 'NOMINAL'}
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}

            {/* Current Selected Event Highlight Marker */}
            {hasEventLocation && (
              <CircleMarker
                center={[Number(bundle.location.latitude), Number(bundle.location.longitude)]}
                radius={10}
                pathOptions={{
                  fillColor: bundle.physical_rules?.is_anomalous ? '#ef4444' : '#10b981',
                  fillOpacity: 0.95,
                  color: '#ffffff',
                  weight: 2.5
                }}
              >
                <Popup>
                  <div style={{ color: '#000', fontSize: '0.82rem', fontFamily: 'monospace' }}>
                    <strong>Active Forensic Event: {bundle.event_id}</strong><br />
                    DEFCON: {bundle.physical_rules?.is_anomalous ? 'DEFCON 1/2' : 'DEFCON 5'}<br />
                    Displacement: {bundle.security_features?.disp_haversine !== undefined && bundle.security_features?.disp_haversine !== null ? Number(bundle.security_features.disp_haversine).toFixed(2) : 'N/A'} m<br />
                    Velocity: {bundle.security_features?.vel_kinematic !== undefined && bundle.security_features?.vel_kinematic !== null ? Number(bundle.security_features.vel_kinematic).toFixed(2) : 'N/A'} m/s
                  </div>
                </Popup>
              </CircleMarker>
            )}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
