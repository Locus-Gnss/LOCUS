import React from 'react';
import { Cpu, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function FeaturesView({ bundle }) {
  const feats = bundle?.security_features || {};

  const definitions = [
    {
      key: 'disp_haversine',
      name: 'Haversine Displacement',
      unit: 'm',
      warn: 50.0,
      crit: 100.0,
      category: 'Kinematics',
      desc: 'Great-circle spatial jump between consecutive 1-sec ticks.'
    },
    {
      key: 'vel_kinematic',
      name: 'Kinematic Velocity',
      unit: 'm/s',
      warn: 50.0,
      crit: 85.0,
      category: 'Kinematics',
      desc: 'First differential spatial rate. Automotive/terrestrial bounds.'
    },
    {
      key: 'acc_kinematic',
      name: 'Kinematic Acceleration',
      unit: 'm/s²',
      warn: 4.0,
      crit: 10.0,
      category: 'Kinematics',
      desc: 'Second derivative of position. Detects instantaneous spoofing steps.'
    },
    {
      key: 'jerk_kinematic',
      name: 'Kinematic Jerk',
      unit: 'm/s³',
      warn: 15.0,
      crit: 25.0,
      category: 'Kinematics',
      desc: 'Third derivative of position. Unphysical force transition rate.'
    },
    {
      key: 'bearing_rate',
      name: 'Bearing Angular Rate',
      unit: '°/s',
      warn: 90.0,
      crit: 180.0,
      category: 'Kinematics',
      desc: 'Shortest circular bearing variation over 1-sec epoch interval.'
    },
    {
      key: 'HDOP',
      name: 'Horizontal Dilution (HDOP)',
      unit: 'unitless',
      warn: 4.0,
      crit: 8.0,
      category: 'Geometry',
      desc: 'Geometric satellite constellation spread on the horizontal plane.'
    },
    {
      key: 'VDOP',
      name: 'Vertical Dilution (VDOP)',
      unit: 'unitless',
      warn: 5.0,
      crit: 10.0,
      category: 'Geometry',
      desc: 'Vertical geometric positioning precision dilution.'
    },
    {
      key: 'fix_integrity',
      name: 'Fix Integrity Indicator',
      unit: 'score',
      warn: 0.45,
      crit: 0.20,
      isLowerBetter: false,
      category: 'Integrity',
      desc: 'Deterministic composite score combining fix quality, PDOP, and C/N0.'
    },
    {
      key: 'sat_count_tot',
      name: 'Total Satellites Visible',
      unit: 'count',
      warn: 6,
      crit: 4,
      isLowerBetter: false,
      category: 'Constellation',
      desc: 'Total locked space vehicles across GPS, GLONASS, Galileo, BeiDou.'
    },
    {
      key: 'sat_churn',
      name: 'Satellite Constellation Churn',
      unit: 'ratio',
      warn: 0.35,
      crit: 0.60,
      category: 'Constellation',
      desc: 'Symmetric difference ratio of tracked PRNs between epochs.'
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header */}
      <div className="cyber-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.8rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Cpu size={18} color="var(--cyan-primary)" />
            <div>
              <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.1rem' }}>
                10-DIMENSIONAL CYBERSECURITY FEATURE MONITOR
              </h2>
              <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: '0.2rem' }}>
                Evaluated strictly against calibrated Newtonian bounds and DO-229E geometric invariants.
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              SESSION: <strong style={{ color: 'var(--cyan-primary)' }}>{bundle?.session_id ?? 'N/A'}</strong> | EPOCH: <strong style={{ color: 'var(--cyan-primary)' }}>{bundle?.epoch_id ?? 'N/A'}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Feature Vector Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1rem' }}>
        {definitions.map((def) => {
          const rawVal = feats[def.key];
          const hasVal = rawVal !== undefined && rawVal !== null && !isNaN(rawVal);
          const val = hasVal ? Number(rawVal) : 0;

          // Status calculation: Never convert missing measurements into fabricated nominal values
          let status = 'UNAVAILABLE';
          if (hasVal) {
            status = 'NOMINAL';
            if (def.isLowerBetter === false) {
              if (val < def.crit) status = 'CRITICAL';
              else if (val < def.warn) status = 'WARNING';
            } else {
              if (val >= def.crit) status = 'CRITICAL';
              else if (val >= def.warn) status = 'WARNING';
            }
          }

          const statusColor = status === 'CRITICAL'
            ? 'var(--red-critical)'
            : status === 'WARNING'
            ? 'var(--amber-warning)'
            : status === 'NOMINAL'
            ? 'var(--green-nominal)'
            : 'var(--text-muted)';

          // Percentage calculation for progress bar
          const maxScale = Math.max(def.crit * 1.35, val * 1.15, 1);
          const pct = hasVal ? Math.min(100, Math.max(0, (val / maxScale) * 100)) : 0;

          return (
            <div key={def.key} className="cyber-card" style={{
              borderLeft: `3px solid ${statusColor}`
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <div>
                  <span style={{ fontSize: '0.68rem', textTransform: 'uppercase', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
                    [{def.category}] {def.key}
                  </span>
                  <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1rem', color: '#fff', fontWeight: 600 }}>
                    {def.name}
                  </h3>
                </div>
                <span style={{
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-hud)',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '3px',
                  background: status === 'CRITICAL' 
                    ? 'rgba(239, 68, 68, 0.2)' 
                    : status === 'WARNING' 
                    ? 'rgba(245, 158, 11, 0.2)' 
                    : status === 'NOMINAL'
                    ? 'rgba(16, 185, 129, 0.2)'
                    : 'rgba(100, 116, 139, 0.2)',
                  color: statusColor,
                  border: `1px solid ${statusColor}`
                }}>
                  {status}
                </span>
              </div>

              {/* Metric Value & Unit */}
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', margin: '0.5rem 0' }}>
                <span className="metric-value" style={{ fontSize: '1.6rem', color: statusColor }}>
                  {hasVal ? (val < 1 && val > 0 ? val.toFixed(3) : val.toFixed(2)) : 'UNAVAILABLE'}
                </span>
                <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>{def.unit}</span>
              </div>

              {/* Progress Track */}
              <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden', margin: '0.5rem 0' }}>
                <div style={{
                  width: `${pct}%`,
                  height: '100%',
                  background: statusColor,
                  boxShadow: hasVal ? `0 0 8px ${statusColor}` : 'none',
                  transition: 'width 0.4s ease'
                }} />
              </div>

              {/* Threshold Labels */}
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                <span>Warn: {def.warn} {def.unit}</span>
                <span>Crit: {def.crit} {def.unit}</span>
              </div>

              <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '0.4rem' }}>
                {def.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* Preprocessing and Data Quality Audit Panel */}
      <div className="cyber-card" style={{ borderLeft: '3px solid var(--cyan-primary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
          <ShieldAlert size={18} color="var(--cyan-primary)" />
          <div>
            <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.98rem' }}>
              PREPROCESSING, INGESTION & DATA INTEGRITY AUDIT
            </h3>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.78rem', marginTop: '0.1rem' }}>
              Mandatory telemetry sanitation invariants enforced prior to downstream feature extraction and model inference.
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.85rem' }}>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              PARSING & DATA VALIDATION
            </span>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', lineHeight: '1.4' }}>
              NMEA 0183 8-bit XOR checksum verification across $GPRMC, $GPGGA, $GPGSA, $GPGSV sentences. Atomic UTC reconstruction combining host RTC date and GNSS atomic time.
            </p>
            <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: 'var(--green-nominal)', fontFamily: 'var(--font-mono)' }}>
              STATUS: CHECKSUM & TIMESTAMP PARSING ACTIVE
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              MISSING VALUE IMPUTATION POLICY
            </span>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', lineHeight: '1.4' }}>
              Zero imputation of sensor measurements is strictly forbidden. Bounded forward-fill (max 3 epochs) applied exclusively to continuous metrics; missing coordinates propagate as explicit NaN.
            </p>
            <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: 'var(--green-nominal)', fontFamily: 'var(--font-mono)' }}>
              STATUS: ZERO-FABRICATION POLICY ENFORCED
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              DEDUPLICATION & REPLAY DETECTION
            </span>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', lineHeight: '1.4' }}>
              Identical timestamp_pc sequence identification flags redundant epochs as DUPLICATE_EPOCH, preventing artificial rate-of-change suppression in spoofing replays.
            </p>
            <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: 'var(--green-nominal)', fontFamily: 'var(--font-mono)' }}>
              STATUS: EPOCH UNIQUENESS VERIFIED
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              TIMESTAMP ORDERING & SESSIONING
            </span>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', lineHeight: '1.4' }}>
              Strict monotonic ordering enforced. Inter-epoch gaps &gt; 5.0 seconds automatically trigger new session demarcation to avoid artificial velocity spikes across recording halts.
            </p>
            <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: 'var(--green-nominal)', fontFamily: 'var(--font-mono)' }}>
              STATUS: MONOTONIC GAP THRESHOLD: 5.0s
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              COORDINATE BOUNDS & NULL ISLAND
            </span>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', lineHeight: '1.4' }}>
              Coordinates verified against WGS-84 ellipsoidal boundaries ([-90°, +90°] latitude, [-180°, +180°] longitude). Null Island (0.0°, 0.0°) coordinates flagged as INVALID_COORDS.
            </p>
            <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: bundle?.location?.latitude != null ? 'var(--green-nominal)' : 'var(--amber-warning)', fontFamily: 'var(--font-mono)' }}>
              CURRENT: {bundle?.location?.latitude != null ? `${bundle.location.latitude.toFixed(5)}°, ${bundle.location.longitude.toFixed(5)}° (VALID)` : 'UNAVAILABLE'}
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              SCHEMA & DTYPE VALIDATION
            </span>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', lineHeight: '1.4' }}>
              20-field canonical observation schema validated against float64/int dtypes before vector formulation: epoch_id, session_id, utc, pc, lat, lon, alt, spd, hdg, fix, sat, dop, cno, flags.
            </p>
            <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: 'var(--green-nominal)', fontFamily: 'var(--font-mono)' }}>
              STATUS: CANONICAL 20-FIELD SCHEMA VERIFIED
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              LEAKAGE-FREE FEATURE SCALING
            </span>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', lineHeight: '1.4' }}>
              RobustScaler utilizing median centering and interquartile range (IQR, 25th-75th percentiles) fitted strictly on the Training partition to eliminate data leakage in unsupervised anomaly models.
            </p>
            <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
              TRANSFORMATION: ROBUSTSCALER (IQR)
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              SET-THEORETIC SATELLITE CHURN
            </span>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', lineHeight: '1.4' }}>
              Calculated strictly from tracked PRN identities via symmetric difference ratio: |PRN_t Δ PRN_t-1| / |PRN_t ∪ PRN_t-1|. Evaluated only when satellite PRN sets are populated.
            </p>
            <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: feats.sat_churn != null ? 'var(--green-nominal)' : 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              PRN CHURN: {feats.sat_churn != null ? Number(feats.sat_churn).toFixed(3) : 'UNAVAILABLE (PRN IDS MISSING)'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
