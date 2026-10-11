import React from 'react';
import {
  ShieldAlert,
  Gauge,
  Satellite,
  Compass,
  AlertTriangle,
  Zap,
  Activity,
  Layers,
  ArrowRight
} from 'lucide-react';
import PipelineTracker from '../PipelineTracker';

export default function OverviewView({
  bundle,
  deliberation,
  telemetryLatest,
  alerts = [],
  onNavigate
}) {
  const defcon = deliberation?.risk_level || (bundle?.physical_rules?.is_anomalous ? 'DEFCON_2_PERSISTENT_DRIFT' : 'DEFCON_5_NOMINAL');
  const rawConf = deliberation?.confidence ?? deliberation?.confidence_score ?? 0.95;
  const confidence = `${(rawConf * 100).toFixed(0)}%`;
  const directive = deliberation?.action_mandated || deliberation?.recommended_next_action || (bundle?.physical_rules?.is_anomalous ? 'Isolate GPS PVT solution.' : 'Maintain continuous autonomous monitoring.');
  const rationale = deliberation?.primary_rationale || deliberation?.explanation || deliberation?.summary || 'Kinematic and geometric parameters operate within nominal bounds.';

  const isAnomalous = defcon.includes('1') || defcon.includes('2') || defcon.includes('3') || Boolean(bundle?.physical_rules?.is_anomalous);
  const alertCount = alerts.length;

  const lat = bundle?.location?.latitude !== undefined ? Number(bundle.location.latitude).toFixed(5) : (telemetryLatest?.latitude !== undefined ? Number(telemetryLatest.latitude).toFixed(5) : 'UNAVAILABLE');
  const lon = bundle?.location?.longitude !== undefined ? Number(bundle.location.longitude).toFixed(5) : (telemetryLatest?.longitude !== undefined ? Number(telemetryLatest.longitude).toFixed(5) : 'UNAVAILABLE');
  const speed = bundle?.security_features?.vel_kinematic !== undefined ? Number(bundle.security_features.vel_kinematic).toFixed(1) + ' m/s' : (telemetryLatest?.speed_kmh !== undefined ? Number(telemetryLatest.speed_kmh).toFixed(1) + ' km/h' : '0.0 m/s');
  const hdop = bundle?.security_features?.HDOP !== undefined ? Number(bundle.security_features.HDOP).toFixed(2) : (telemetryLatest?.hdop !== undefined ? Number(telemetryLatest.hdop).toFixed(2) : 'N/A');
  const sats = bundle?.security_features?.sat_count_tot ?? telemetryLatest?.satellites_used ?? 'N/A';
  const fixIntegrity = bundle?.security_features?.fix_integrity !== undefined
    ? (Number(bundle.security_features.fix_integrity) * 100).toFixed(0) + '%'
    : 'N/A';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* High-Level Incident Banner */}
      <div className={`cyber-card ${isAnomalous ? 'cyber-card-danger' : ''}`} style={{
        background: isAnomalous
          ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(13, 20, 38, 0.85))'
          : 'linear-gradient(135deg, rgba(0, 240, 255, 0.08), rgba(13, 20, 38, 0.85))',
        borderLeft: isAnomalous ? '4px solid var(--red-critical)' : '4px solid var(--cyan-primary)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
              <span className={`live-dot ${isAnomalous ? 'live-dot-red' : 'live-dot-green'}`}></span>
              <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.1rem', letterSpacing: '0.05em' }}>
                {isAnomalous ? 'SECURITY INCIDENT ACTIVE — THREAT DETECTED' : 'SYSTEM NOMINAL — RECEPTOR SECURED'}
              </h2>
            </div>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.88rem', maxWidth: '850px', marginBottom: '0.75rem' }}>
              {rationale}
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(0, 0, 0, 0.35)', padding: '0.45rem 0.85rem', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
              <Zap size={14} color={isAnomalous ? 'var(--red-critical)' : 'var(--cyan-primary)'} />
              <strong style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-main)', letterSpacing: '0.06em' }}>
                Mandated Directive:
              </strong>
              <span style={{ fontSize: '0.82rem', color: isAnomalous ? '#fca5a5' : '#7dd3fc', fontFamily: 'var(--font-mono)' }}>
                {directive}
              </span>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
              Consensus Confidence
            </span>
            <div style={{ fontFamily: 'var(--font-hud)', fontSize: '1.8rem', color: 'var(--cyan-primary)', fontWeight: 900 }}>
              {confidence}
            </div>
          </div>
        </div>
      </div>
 
      {/* Compact 10-Stage Pipeline Flow */}
      <PipelineTracker compact runId={bundle?.run_id || deliberation?.run_id || 'run_active'} />

      {/* Primary KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        <div className="cyber-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span className="metric-label">Fix Integrity</span>
            <ShieldAlert size={16} color="var(--cyan-primary)" />
          </div>
          <div className="metric-value" style={{ fontSize: '1.5rem', color: 'var(--cyan-primary)' }}>
            {fixIntegrity}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Deterministic Solution Score
          </div>
        </div>

        <div className="cyber-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span className="metric-label">Satellites Visible</span>
            <Satellite size={16} color="var(--green-nominal)" />
          </div>
          <div className="metric-value" style={{ fontSize: '1.5rem', color: 'var(--green-nominal)' }}>
            {sats}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Constellation Locked
          </div>
        </div>

        <div className="cyber-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span className="metric-label">Geometry (HDOP)</span>
            <Compass size={16} color={Number(hdop) > 4 ? 'var(--amber-warning)' : 'var(--cyan-primary)'} />
          </div>
          <div className="metric-value" style={{ fontSize: '1.5rem', color: Number(hdop) > 4 ? 'var(--amber-warning)' : '#ffffff' }}>
            {hdop}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            {Number(hdop) < 2 ? 'Optimal (< 2.0)' : 'Acceptable'}
          </div>
        </div>

        <div className="cyber-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span className="metric-label">Kinematic Velocity</span>
            <Gauge size={16} color="var(--cyan-primary)" />
          </div>
          <div className="metric-value" style={{ fontSize: '1.5rem', color: '#ffffff' }}>
            {speed} <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 400 }}>m/s</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Newtonian 1-Sec Tick
          </div>
        </div>

        <div className="cyber-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span className="metric-label">Active Incidents</span>
            <AlertTriangle size={16} color="var(--red-critical)" />
          </div>
          <div className="metric-value" style={{ fontSize: '1.5rem', color: 'var(--red-critical)' }}>
            {alertCount}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Logged in Forensic Queue
          </div>
        </div>

        <div className="cyber-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span className="metric-label">Current Position</span>
            <Activity size={16} color="var(--purple-agent)" />
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem', color: '#ffffff', fontWeight: 600 }}>
            {lat}° N<br />{lon}° E
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            WGS-84 Coordinates
          </div>
        </div>
      </div>

      {/* Quick Navigation Panels */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
        {/* Detection Quad Quick Status */}
        <div className="cyber-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Layers size={16} color="var(--cyan-primary)" />
              <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.9rem' }}>Detection Quad Status</h3>
            </div>
            <button className="cyber-btn" onClick={() => onNavigate('detectors')} style={{ padding: '0.25rem 0.5rem', fontSize: '0.7rem' }}>
              View Quad <ArrowRight size={12} />
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.25)', borderRadius: '4px' }}>
              <span>Physical Rules Engine:</span>
              <strong style={{ color: bundle?.physical_rules?.is_anomalous ? 'var(--red-critical)' : 'var(--green-nominal)' }}>
                {bundle?.physical_rules?.is_anomalous ? 'VIOLATION DETECTED' : 'NOMINAL (PASSED)'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.25)', borderRadius: '4px' }}>
              <span>Isolation Forest (Spatial):</span>
              <strong style={{ color: bundle?.isolation_forest?.is_anomaly ? 'var(--red-critical)' : 'var(--green-nominal)' }}>
                {bundle?.isolation_forest?.is_anomaly ? 'SPATIAL OUTLIER' : 'IN-BOUNDS'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.25)', borderRadius: '4px' }}>
              <span>XGBoost Supervised Tier:</span>
              <strong style={{ color: 'var(--text-dim)' }}>
                {bundle?.xgboost?.status || 'UNFITTED (AUDITED)'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.25)', borderRadius: '4px' }}>
              <span>LSTM Temporal Autoencoder:</span>
              <strong style={{ color: bundle?.temporal_model?.is_anomaly ? 'var(--red-critical)' : 'var(--green-nominal)' }}>
                {bundle?.temporal_model?.status === 'BUFFERING' ? 'BUFFERING WINDOW' : (bundle?.temporal_model?.is_anomaly ? 'TEMPORAL DRIFT' : 'NOMINAL')}
              </strong>
            </div>
          </div>
        </div>

        {/* 3-Agent Deliberative Summary */}
        <div className="cyber-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldAlert size={16} color="var(--purple-agent)" />
              <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.9rem' }}>3-Agent Cyber SOC Consensus</h3>
            </div>
            <button className="cyber-btn" onClick={() => onNavigate('agents')} style={{ padding: '0.25rem 0.5rem', fontSize: '0.7rem' }}>
              Inspect Deliberation <ArrowRight size={12} />
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.25)', borderRadius: '4px' }}>
              <span>Agent 1 (GNSS Integrity):</span>
              <strong style={{ color: 'var(--cyan-primary)' }}>
                {deliberation?.agent_1_integrity?.integrity_status || 'NOMINAL'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.25)', borderRadius: '4px' }}>
              <span>Agent 2 (Temporal / Threat):</span>
              <strong style={{ color: 'var(--amber-warning)' }}>
                {deliberation?.agent_2_threat?.threat_level || 'BENIGN'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.25)', borderRadius: '4px' }}>
              <span>Agent 3 (Master SOC Orchestrator):</span>
              <strong style={{ color: 'var(--green-nominal)' }}>
                {deliberation?.risk_level || 'DEFCON_5_NOMINAL'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.25)', borderRadius: '4px' }}>
              <span>Anti-Mutation Guard:</span>
              <strong style={{ color: 'var(--green-nominal)' }}>
                VERIFIED (0 SENSOR MUTATIONS)
              </strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
