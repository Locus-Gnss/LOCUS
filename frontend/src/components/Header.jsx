import React, { useState, useEffect } from 'react';
import { Shield, Radio, Activity, Clock, RefreshCw, AlertTriangle } from 'lucide-react';

export default function Header({
  events = [],
  selectedEventId,
  onSelectEvent,
  deliberation = null,
  health = null,
  onRefresh,
  isLoading = false
}) {
  const [utcTime, setUtcTime] = useState(new Date().toUTCString().slice(17, 25));

  useEffect(() => {
    const timer = setInterval(() => {
      setUtcTime(new Date().toUTCString().slice(17, 25));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const defconLevel = deliberation?.risk_level || 'DEFCON_5_NOMINAL';
  const defconClass = defconLevel.includes('1')
    ? 'defcon-1'
    : defconLevel.includes('2')
    ? 'defcon-2'
    : defconLevel.includes('3')
    ? 'defcon-3'
    : defconLevel.includes('4')
    ? 'defcon-4'
    : 'defcon-5';

  const defconLabel = defconLevel.replace(/_/g, ' ');

  return (
    <header className="cyber-card" style={{ padding: '0.85rem 1.5rem', marginBottom: '1rem', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
      {/* Brand & System Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '6px',
          background: 'linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(168, 85, 247, 0.2))',
          border: '1px solid var(--cyan-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 12px rgba(0, 240, 255, 0.3)'
        }}>
          <Shield size={24} color="var(--cyan-primary)" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <h1 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.25rem', fontWeight: 900, letterSpacing: '0.08em', color: '#fff' }}>
              LOCUS
            </h1>
            <span style={{ fontFamily: 'var(--font-title)', fontSize: '0.8rem', color: 'var(--cyan-primary)', letterSpacing: '0.1em', background: 'rgba(0, 240, 255, 0.1)', padding: '0.1rem 0.4rem', borderRadius: '3px', border: '1px solid rgba(0, 240, 255, 0.2)' }}>
              v5.5 SOC
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', letterSpacing: '0.05em' }}>
            GNSS Cyber-Physical Security Operations Center
          </p>
        </div>
      </div>

      {/* Mid status: DEFCON & Provenance */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        {/* DEFCON Badge */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
          <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
            Threat Rating
          </span>
          <div className={`defcon-badge ${defconClass}`}>
            <AlertTriangle size={14} />
            <span>{defconLabel}</span>
          </div>
        </div>

        {/* Provenance Status */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
          <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
            Sensor Provenance
          </span>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.78rem',
            background: 'rgba(6, 11, 22, 0.7)',
            padding: '0.25rem 0.65rem',
            borderRadius: '4px',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            color: 'var(--text-main)'
          }}>
            <span className="live-dot live-dot-green"></span>
            <span>REAL L89HA TELEMETRY (REPLAY)</span>
          </div>
        </div>

        {/* Live Atomic UTC Clock */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
          <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
            Atomic UTC Tick
          </span>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.85rem',
            color: 'var(--cyan-primary)',
            background: 'rgba(0, 240, 255, 0.05)',
            padding: '0.25rem 0.65rem',
            borderRadius: '4px',
            border: '1px solid rgba(0, 240, 255, 0.2)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem'
          }}>
            <Clock size={13} />
            <span>{utcTime} UTC</span>
          </div>
        </div>
      </div>

      {/* Right: Active Event Selector & Refresh */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.15rem' }}>
            Forensic Incident Event:
          </label>
          <select
            className="cyber-select"
            value={selectedEventId || ''}
            onChange={(e) => onSelectEvent(e.target.value)}
            style={{ width: '150px' }}
          >
            {events.length > 0 ? (
              events.map((ev) => (
                <option key={ev.event_id} value={ev.event_id}>
                  {ev.event_id}
                </option>
              ))
            ) : (
              <option value="">No Events</option>
            )}
          </select>
        </div>

        <button
          className="cyber-btn"
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh Telemetry & Deliberation"
          style={{ height: '35px', marginTop: '1rem', padding: '0.3rem 0.75rem' }}
        >
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          <span>Sync</span>
        </button>
      </div>
    </header>
  );
}
