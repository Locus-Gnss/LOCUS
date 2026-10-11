import React, { useState } from 'react';
import { Activity, Gauge, Navigation, Compass, Signal, ArrowDownUp } from 'lucide-react';

export default function TelemetryView({ telemetryHistory = [], telemetryLatest }) {
  const [metricFilter, setMetricFilter] = useState('speed');

  const records = telemetryHistory.slice(-50); // Show recent 50 epochs

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner */}
      <div className="cyber-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.1rem', marginBottom: '0.25rem' }}>
              LIVE GNSS TELEMETRY & EPOCH STREAM
            </h2>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem' }}>
              High-frequency multi-sentence NMEA stream aggregates. Zero interpolation or synthetic smoothing.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {['speed', 'hdop', 'altitude', 'satellites'].map((m) => (
              <button
                key={m}
                className={`cyber-btn ${metricFilter === m ? 'cyber-btn-active' : ''}`}
                onClick={() => setMetricFilter(m)}
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
              >
                {m.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* SVG Time-Series Chart */}
      <div className="cyber-card">
        <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--cyan-primary)' }}>
          {metricFilter.toUpperCase()} TIME-SERIES TREND (RECENT {records.length} EPOCHS)
        </h3>

        {records.length > 0 ? (
          <div style={{ width: '100%', height: '240px', position: 'relative', background: 'rgba(5, 8, 16, 0.75)', borderRadius: '6px', padding: '1rem', border: '1px solid var(--border-subtle)' }}>
            <svg viewBox="0 0 800 200" style={{ width: '100%', height: '100%', overflow: 'visible' }}>
              {/* Grid Lines */}
              <line x1="0" y1="50" x2="800" y2="50" stroke="rgba(0, 240, 255, 0.08)" strokeDasharray="4 4" />
              <line x1="0" y1="100" x2="800" y2="100" stroke="rgba(0, 240, 255, 0.08)" strokeDasharray="4 4" />
              <line x1="0" y1="150" x2="800" y2="150" stroke="rgba(0, 240, 255, 0.08)" strokeDasharray="4 4" />

              {/* Data Plot */}
              {(() => {
                const vals = records.map((r) => {
                  if (metricFilter === 'speed') return Number(r.speed_kmh || 0);
                  if (metricFilter === 'hdop') return Number(r.hdop || 1);
                  if (metricFilter === 'altitude') return Number(r.altitude_m || 50);
                  if (metricFilter === 'satellites') return Number(r.satellites_used || 12);
                  return 0;
                });
                const min = Math.min(...vals, 0);
                const max = Math.max(...vals, 1) * 1.15;
                const points = vals.map((v, idx) => {
                  const x = (idx / (vals.length - 1 || 1)) * 800;
                  const y = 180 - ((v - min) / (max - min || 1)) * 160;
                  return `${x},${y}`;
                }).join(' ');

                return (
                  <>
                    <polyline
                      fill="none"
                      stroke="var(--cyan-primary)"
                      strokeWidth="2.5"
                      points={points}
                      style={{ filter: 'drop-shadow(0 0 6px var(--cyan-primary))' }}
                    />
                    {vals.map((v, idx) => {
                      const x = (idx / (vals.length - 1 || 1)) * 800;
                      const y = 180 - ((v - min) / (max - min || 1)) * 160;
                      return (
                        <circle
                          key={idx}
                          cx={x}
                          cy={y}
                          r="3"
                          fill="var(--bg-darker)"
                          stroke="var(--cyan-primary)"
                          strokeWidth="1.5"
                        />
                      );
                    })}
                  </>
                );
              })()}
            </svg>
          </div>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No telemetry records loaded.
          </div>
        )}
      </div>

      {/* Epoch Telemetry Records Table */}
      <div className="cyber-card">
        <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
          Recent Telemetry Observations (Last 15 Records)
        </h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-glow)', textAlign: 'left', color: 'var(--cyan-primary)' }}>
                <th style={{ padding: '0.5rem' }}>Epoch / Time</th>
                <th style={{ padding: '0.5rem' }}>Latitude</th>
                <th style={{ padding: '0.5rem' }}>Longitude</th>
                <th style={{ padding: '0.5rem' }}>Altitude (m)</th>
                <th style={{ padding: '0.5rem' }}>Speed (km/h)</th>
                <th style={{ padding: '0.5rem' }}>Heading (°)</th>
                <th style={{ padding: '0.5rem' }}>HDOP</th>
                <th style={{ padding: '0.5rem' }}>Sats Used</th>
              </tr>
            </thead>
            <tbody>
              {records.slice(-15).reverse().map((r, i) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '0.45rem', color: 'var(--text-dim)' }}>
                    {r.timestamp_utc?.slice(11, 19) || `Tick #${i}`}
                  </td>
                  <td style={{ padding: '0.45rem' }}>{Number(r.latitude || 0).toFixed(6)}°</td>
                  <td style={{ padding: '0.45rem' }}>{Number(r.longitude || 0).toFixed(6)}°</td>
                  <td style={{ padding: '0.45rem' }}>{Number(r.altitude_m || 0).toFixed(1)} m</td>
                  <td style={{ padding: '0.45rem', color: Number(r.speed_kmh) > 50 ? 'var(--amber-warning)' : 'var(--text-main)' }}>
                    {Number(r.speed_kmh || 0).toFixed(1)}
                  </td>
                  <td style={{ padding: '0.45rem' }}>{Number(r.heading_deg || 0).toFixed(1)}°</td>
                  <td style={{ padding: '0.45rem', color: Number(r.hdop) > 4 ? 'var(--red-critical)' : 'var(--green-nominal)' }}>
                    {Number(r.hdop || 1).toFixed(2)}
                  </td>
                  <td style={{ padding: '0.45rem', color: 'var(--cyan-primary)' }}>
                    {r.satellites_used || r.satellites_in_view || 18}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
