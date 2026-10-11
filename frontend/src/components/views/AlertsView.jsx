import React, { useState } from 'react';
import { AlertOctagon, Search, Filter, ArrowRight } from 'lucide-react';

export default function AlertsView({ alerts = [], selectedEventId, onSelectEvent }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  const filtered = alerts.filter((a) => {
    const matchesSearch = (a.alert_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           a.event_id?.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesSeverity = filterSeverity === 'ALL' || a.severity === filterSeverity;
    return matchesSearch && matchesSeverity;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner & Filters */}
      <div className="cyber-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <AlertOctagon size={18} color="var(--red-critical)" />
              <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.1rem' }}>
                SECURITY ALERT CENTER & FORENSIC TRIAGE
              </h2>
            </div>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: '0.2rem' }}>
              Active detection events flagged by the Detection Quad and synthesized by the Master SOC Orchestrator.
            </p>
          </div>

          {/* Search & Filter Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(6, 11, 22, 0.8)', padding: '0.25rem 0.65rem', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
              <Search size={14} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Search event / alert..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ background: 'transparent', border: 'none', color: '#fff', fontSize: '0.8rem', fontFamily: 'var(--font-mono)', outline: 'none' }}
              />
            </div>

            <select
              className="cyber-select"
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              style={{ fontSize: '0.8rem' }}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical Only</option>
              <option value="WARNING">Warning Only</option>
              <option value="INFO">Info Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="cyber-card" style={{ padding: '0' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-glow)', background: 'rgba(0, 240, 255, 0.04)', textAlign: 'left', color: 'var(--cyan-primary)' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Alert ID</th>
                <th style={{ padding: '0.75rem 1rem' }}>Event Ref</th>
                <th style={{ padding: '0.75rem 1rem' }}>Timestamp (UTC)</th>
                <th style={{ padding: '0.75rem 1rem' }}>Severity</th>
                <th style={{ padding: '0.75rem 1rem' }}>Incident Type</th>
                <th style={{ padding: '0.75rem 1rem' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length > 0 ? (
                filtered.map((al) => {
                  const isSelected = al.event_id === selectedEventId;
                  const isCritical = al.severity === 'CRITICAL' || al.alert_id.includes('4_22');
                  return (
                    <tr
                      key={al.alert_id}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        background: isSelected ? 'rgba(0, 240, 255, 0.08)' : 'transparent',
                        transition: 'background 0.2s'
                      }}
                    >
                      <td style={{ padding: '0.7rem 1rem', fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)', fontWeight: 600 }}>
                        {al.alert_id}
                      </td>
                      <td style={{ padding: '0.7rem 1rem', fontFamily: 'var(--font-mono)' }}>
                        {al.event_id}
                      </td>
                      <td style={{ padding: '0.7rem 1rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        {al.timestamp || al.timestamp_utc || 'N/A'}
                      </td>
                      <td style={{ padding: '0.7rem 1rem' }}>
                        <span style={{
                          fontFamily: 'var(--font-hud)',
                          fontSize: '0.7rem',
                          padding: '0.2rem 0.5rem',
                          borderRadius: '3px',
                          background: isCritical ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                          color: isCritical ? 'var(--red-critical)' : 'var(--amber-warning)',
                          border: `1px solid ${isCritical ? 'var(--red-critical)' : 'var(--amber-warning)'}`
                        }}>
                          {al.severity || 'WARNING'}
                        </span>
                      </td>
                      <td style={{ padding: '0.7rem 1rem', color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
                        {al.event_type || al.title || (al.affected_features?.length > 0 ? al.affected_features.join(', ') : 'DETECTOR_FLAGGED')}
                      </td>
                      <td style={{ padding: '0.7rem 1rem' }}>
                        <button
                          className={`cyber-btn ${isSelected ? 'cyber-btn-active' : ''}`}
                          onClick={() => onSelectEvent(al.event_id)}
                          style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem' }}
                        >
                          {isSelected ? 'Active' : 'Inspect'} <ArrowRight size={11} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="6" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No matching incidents found in queue.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
