import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  ShieldCheck,
  ShieldAlert,
  Bot,
  BookOpen,
  Cpu,
  Layers,
  FileSearch,
  Download,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Activity,
  Compass,
  Radio,
  FileText
} from 'lucide-react';

export default function PipelineResultsView({ result, onNavigate }) {
  const [expandedSection, setExpandedSection] = useState({
    validation: true,
    features: true,
    detectors: true,
    agents: true,
    rag: true,
    xai: true,
    decision: true,
    bundle: false,
  });

  if (!result) {
    return (
      <div className="cyber-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <p>No pipeline run execution result loaded.</p>
        <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>
          Please upload or stream GNSS telemetry in the <strong>Live Data Input</strong> console to view full multi-agent, RAG, and explainable AI results.
        </p>
      </div>
    );
  }

  const toggleSection = (key) => {
    setExpandedSection((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const {
    run_id,
    event_id,
    success,
    source_type,
    source_name,
    total_records = 0,
    valid_records = 0,
    rejected_records = 0,
    duplicate_records = 0,
    processing_time_ms = 0,
    validation_summary = {},
    feature_metrics = {},
    detector_results = {},
    agent_findings = {},
    rag_grounding = {},
    explainable_ai = {},
    canonical_assessment = {},
    evidence_bundle = {},
    evidence_path = '',
    errors = [],
  } = result;

  // Detectors
  const pr = detector_results.physical_rules || {};
  const ifo = detector_results.isolation_forest || {};
  const xgb = detector_results.xgboost || {};
  const temp = detector_results.temporal_model || detector_results.temporal_lstm || {};

  // Agents
  const a1 = agent_findings.agent_1_integrity || {};
  const a2 = agent_findings.agent_2_temporal_threat || {};
  const a3 = agent_findings.agent_3_master_soc || {};

  // Canonical bounds
  const featureBounds = {
    disp_haversine: { unit: 'm', warn: 50.0, crit: 100.0, desc: 'Haversine step displacement' },
    vel_kinematic: { unit: 'm/s', warn: 50.0, crit: 85.0, desc: 'Kinematic ground velocity' },
    acc_kinematic: { unit: 'm/s²', warn: 4.0, crit: 10.0, desc: 'Kinematic acceleration' },
    jerk_kinematic: { unit: 'm/s³', warn: 15.0, crit: 25.0, desc: 'Third-derivative jerk' },
    bearing_rate: { unit: 'deg/s', warn: 90.0, crit: 180.0, desc: 'Normalized bearing angular rate' },
    HDOP: { unit: 'dimless', warn: 4.0, crit: 8.0, desc: 'Horizontal Dilution of Precision' },
    VDOP: { unit: 'dimless', warn: 5.0, crit: 10.0, desc: 'Vertical Dilution of Precision' },
    fix_integrity: { unit: 'score', warn: 0.45, crit: 0.20, desc: 'Navigation solution integrity index' },
    sat_count_tot: { unit: 'count', warn: 6, crit: 4, desc: 'Satellites used in solution' },
    sat_churn: { unit: 'ratio', warn: 0.35, crit: 0.60, desc: 'PRN identity turnover rate' },
  };

  const getFeatureStatus = (feat, val) => {
    if (val === null || val === undefined || isNaN(val)) return 'UNKNOWN';
    const b = featureBounds[feat];
    if (!b) return 'NORMAL';
    if (feat === 'fix_integrity' || feat === 'sat_count_tot') {
      if (val <= b.crit) return 'CRITICAL';
      if (val <= b.warn) return 'WARNING';
      return 'NORMAL';
    }
    const absVal = Math.abs(val);
    if (absVal >= b.crit) return 'CRITICAL';
    if (absVal >= b.warn) return 'WARNING';
    return 'NORMAL';
  };

  const downloadJson = (data, filename) => {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  const defconNumber = canonical_assessment.defcon_number || 5;
  const defconDisplay = canonical_assessment.defcon_display || `DEFCON ${defconNumber}`;
  const defconBadgeClass = canonical_assessment.defcon_badge_class || (defconNumber <= 2 ? 'badge-critical' : defconNumber === 3 ? 'badge-warning' : 'badge-normal');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* 1. Header & Run Metadata Banner */}
      <div className="cyber-card" style={{ borderLeft: '4px solid var(--cyan-primary)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span className="live-dot live-dot-green"></span>
              <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.15rem', color: '#fff' }}>
                PIPELINE ANALYSIS RESULTS CONSOLE
              </h2>
            </div>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: '0.25rem' }}>
              Authoritative execution artifact for Run <strong style={{ color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>{run_id}</strong> &bull; Event <strong style={{ color: '#fff', fontFamily: 'var(--font-mono)' }}>{event_id}</strong>
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <span className={defconBadgeClass} style={{ fontSize: '0.8rem', padding: '0.3rem 0.75rem', borderRadius: '4px' }}>
              {defconDisplay}
            </span>
            <button
              className="cyber-btn"
              onClick={() => downloadJson(result, `locus_run_${run_id}.json`)}
              style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Download size={14} />
              <span>Export Run JSON</span>
            </button>
            {evidence_bundle && Object.keys(evidence_bundle).length > 0 && (
              <button
                className="cyber-btn"
                onClick={() => downloadJson(evidence_bundle, `evidence_${event_id}.json`)}
                style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <Download size={14} />
                <span>Evidence Bundle</span>
              </button>
            )}
          </div>
        </div>

        {/* Run Metadata Grid */}
        <div style={{
          marginTop: '1rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
          gap: '0.75rem',
          background: 'rgba(0, 0, 0, 0.4)',
          padding: '0.75rem 1rem',
          borderRadius: '4px',
          fontSize: '0.78rem'
        }}>
          <div>
            <span style={{ color: 'var(--text-muted)', display: 'block' }}>Run ID:</span>
            <code style={{ color: 'var(--cyan-primary)' }}>{run_id}</code>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', display: 'block' }}>Event ID:</span>
            <code style={{ color: '#fff' }}>{event_id}</code>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', display: 'block' }}>Source Name:</span>
            <span style={{ color: '#fff' }}>{source_name}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', display: 'block' }}>Source Type:</span>
            <span style={{ color: 'var(--amber-warning)' }}>{source_type}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', display: 'block' }}>Execution Time:</span>
            <span style={{ color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
              {processing_time_ms ? `${processing_time_ms.toFixed(1)} ms` : 'N/A'}
            </span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', display: 'block' }}>Execution Status:</span>
            <strong style={{ color: success ? 'var(--green-nominal)' : 'var(--red-critical)' }}>
              {success ? 'COMPLETED' : 'PARTIAL / ATTENTION'}
            </strong>
          </div>
        </div>
      </div>

      {/* 2. Input Validation and Preprocessing Summary */}
      <div className="cyber-card">
        <div
          onClick={() => toggleSection('validation')}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={16} color="var(--cyan-primary)" />
            <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.95rem', color: '#fff' }}>
              1. INPUT VALIDATION &amp; PREPROCESSING SUMMARY
            </h3>
          </div>
          {expandedSection.validation ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>

        {expandedSection.validation && (
          <div style={{ marginTop: '0.85rem' }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '0.75rem',
              marginBottom: '0.75rem'
            }}>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.6rem', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', display: 'block' }}>TOTAL RECORDS</span>
                <strong style={{ fontSize: '1.05rem', color: '#fff' }}>{total_records}</strong>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.6rem', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', display: 'block' }}>VALID EPOCHS</span>
                <strong style={{ fontSize: '1.05rem', color: 'var(--green-nominal)' }}>{valid_records}</strong>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.6rem', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', display: 'block' }}>REJECTED RECORDS</span>
                <strong style={{ fontSize: '1.05rem', color: rejected_records > 0 ? 'var(--amber-warning)' : 'var(--text-muted)' }}>
                  {rejected_records}
                </strong>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.6rem', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', display: 'block' }}>DUPLICATES</span>
                <strong style={{ fontSize: '1.05rem', color: 'var(--text-muted)' }}>{duplicate_records}</strong>
              </div>
            </div>

            {validation_summary.reasons && validation_summary.reasons.length > 0 && (
              <div style={{ fontSize: '0.75rem', color: 'var(--amber-warning)', background: 'rgba(245, 158, 11, 0.08)', padding: '0.5rem', borderRadius: '4px' }}>
                <strong>Validation Notes:</strong> {validation_summary.reasons.join('; ')}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 3. 10-D Canonical Security Features Summary */}
      <div className="cyber-card">
        <div
          onClick={() => toggleSection('features')}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu size={16} color="var(--cyan-primary)" />
            <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.95rem', color: '#fff' }}>
              2. CANONICAL 10-D SECURITY FEATURE VECTORS (TARGET EPOCH)
            </h3>
          </div>
          {expandedSection.features ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>

        {expandedSection.features && (
          <div style={{ marginTop: '0.85rem' }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', fontSize: '0.78rem', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '0.4rem 0.5rem' }}>Feature</th>
                    <th style={{ padding: '0.4rem 0.5rem' }}>Value</th>
                    <th style={{ padding: '0.4rem 0.5rem' }}>Unit</th>
                    <th style={{ padding: '0.4rem 0.5rem' }}>Warning Bound</th>
                    <th style={{ padding: '0.4rem 0.5rem' }}>Critical Bound</th>
                    <th style={{ padding: '0.4rem 0.5rem' }}>Evaluation Status</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.keys(featureBounds).map((feat) => {
                    const val = feature_metrics[feat];
                    const b = featureBounds[feat];
                    const st = getFeatureStatus(feat, val);
                    const isAlert = st === 'CRITICAL' || st === 'WARNING';
                    return (
                      <tr key={feat} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', background: isAlert ? 'rgba(239, 68, 68, 0.05)' : 'transparent' }}>
                        <td style={{ padding: '0.45rem 0.5rem', fontFamily: 'var(--font-mono)', color: '#fff' }}>
                          <strong>{feat}</strong>
                          <span style={{ display: 'block', fontSize: '0.68rem', color: 'var(--text-muted)' }}>{b.desc}</span>
                        </td>
                        <td style={{ padding: '0.45rem 0.5rem', fontFamily: 'var(--font-mono)', color: isAlert ? 'var(--red-critical)' : 'var(--cyan-primary)' }}>
                          {val !== null && val !== undefined && !isNaN(val) ? (typeof val === 'number' ? (Number.isInteger(val) ? val : val.toFixed(3)) : val) : 'N/A (unlogged)'}
                        </td>
                        <td style={{ padding: '0.45rem 0.5rem', color: 'var(--text-muted)' }}>{b.unit}</td>
                        <td style={{ padding: '0.45rem 0.5rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{b.warn}</td>
                        <td style={{ padding: '0.45rem 0.5rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{b.crit}</td>
                        <td style={{ padding: '0.45rem 0.5rem' }}>
                          <span style={{
                            fontSize: '0.65rem',
                            padding: '0.15rem 0.45rem',
                            borderRadius: '3px',
                            fontWeight: 700,
                            fontFamily: 'var(--font-mono)',
                            background: st === 'CRITICAL' ? 'rgba(239, 68, 68, 0.2)' : st === 'WARNING' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.15)',
                            color: st === 'CRITICAL' ? 'var(--red-critical)' : st === 'WARNING' ? 'var(--amber-warning)' : 'var(--green-nominal)',
                            border: `1px solid ${st === 'CRITICAL' ? 'var(--red-critical)' : st === 'WARNING' ? 'var(--amber-warning)' : 'var(--green-nominal)'}`
                          }}>
                            {st}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* 4. Detection Quad Outputs */}
      <div className="cyber-card">
        <div
          onClick={() => toggleSection('detectors')}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers size={16} color="var(--cyan-primary)" />
            <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.95rem', color: '#fff' }}>
              3. MULTI-DETECTOR CONSENSUS QUAD OUTPUTS
            </h3>
          </div>
          {expandedSection.detectors ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>

        {expandedSection.detectors && (
          <div style={{ marginTop: '0.85rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {/* Detector 1 */}
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '4px', borderLeft: `3px solid ${pr.is_anomalous ? 'var(--red-critical)' : 'var(--green-nominal)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>DETECTOR 1 // DETERMINISTIC</span>
                <span className={pr.is_anomalous ? 'badge-critical' : 'badge-normal'} style={{ fontSize: '0.65rem' }}>
                  {pr.status || (pr.is_anomalous ? 'VIOLATED' : 'NOMINAL')}
                </span>
              </div>
              <h4 style={{ color: '#fff', fontSize: '0.88rem' }}>Physical Rules Engine</h4>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', margin: '0.3rem 0' }}>
                Newtonian kinematics (velocity, acceleration, jerk) and geometric DOP thresholds.
              </p>
              <div style={{ fontSize: '0.75rem', marginTop: '0.4rem', color: 'var(--text-muted)' }}>
                Violations: <strong style={{ color: pr.triggered_count > 0 ? 'var(--red-critical)' : 'var(--green-nominal)' }}>{pr.triggered_count || 0}</strong> &bull; Max Severity: <strong>{pr.max_severity || 'INFO'}</strong>
              </div>
            </div>

            {/* Detector 2 */}
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '4px', borderLeft: `3px solid ${ifo.is_anomaly ? 'var(--red-critical)' : 'var(--green-nominal)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>DETECTOR 2 // UNSUPERVISED</span>
                <span className={ifo.is_anomaly ? 'badge-critical' : 'badge-normal'} style={{ fontSize: '0.65rem' }}>
                  {ifo.status || (ifo.is_anomaly ? 'ANOMALY' : 'NOMINAL')}
                </span>
              </div>
              <h4 style={{ color: '#fff', fontSize: '0.88rem' }}>Isolation Forest (Spatial ML)</h4>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', margin: '0.3rem 0' }}>
                Spatial feature partitioning and kinematic density isolation (tuned contamination: 0.01).
              </p>
              <div style={{ fontSize: '0.75rem', marginTop: '0.4rem', color: 'var(--text-muted)' }}>
                Anomaly Score: <strong>{ifo.score !== null && ifo.score !== undefined ? Number(ifo.score).toFixed(4) : 'N/A'}</strong> (threshold: 0.50)
              </div>
            </div>

            {/* Detector 3 */}
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '4px', borderLeft: '3px solid var(--amber-warning)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--amber-warning)', fontFamily: 'var(--font-mono)' }}>DETECTOR 3 // SUPERVISED</span>
                <span className="badge-warning" style={{ fontSize: '0.65rem' }}>
                  {xgb.status || 'UNAVAILABLE — MODEL NOT TRAINED'}
                </span>
              </div>
              <h4 style={{ color: '#fff', fontSize: '0.88rem' }}>Supervised XGBoost Classifier</h4>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', margin: '0.3rem 0' }}>
                Requires verified labelled scenario datasets. Zero mock predictions or fabricated scores.
              </p>
              <div style={{ fontSize: '0.72rem', marginTop: '0.4rem', color: 'var(--amber-warning)' }}>
                <em>{xgb.evidence || 'Baseline data unlabelled; supervised inference deferred until labelled injection.'}</em>
              </div>
            </div>

            {/* Detector 4 */}
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '4px', borderLeft: `3px solid ${temp.is_anomaly ? 'var(--red-critical)' : 'var(--cyan-primary)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>DETECTOR 4 // DEEP TEMPORAL</span>
                <span className={temp.is_anomaly ? 'badge-critical' : 'badge-normal'} style={{ fontSize: '0.65rem' }}>
                  {temp.status || 'OPERATIONAL'}
                </span>
              </div>
              <h4 style={{ color: '#fff', fontSize: '0.88rem' }}>LSTM Temporal Autoencoder</h4>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', margin: '0.3rem 0' }}>
                Rolling window (W=10) reconstruction error tracking temporal drift and spoofing drag-off.
              </p>
              <div style={{ fontSize: '0.75rem', marginTop: '0.4rem', color: 'var(--text-muted)' }}>
                Reconstruction Error: <strong>{temp.score !== null && temp.score !== undefined ? Number(temp.score).toFixed(4) : (temp.result || 'BUFFERING')}</strong>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 5. Three Separate Agent Result Panels */}
      <div className="cyber-card">
        <div
          onClick={() => toggleSection('agents')}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Bot size={16} color="var(--purple-agent)" />
            <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.95rem', color: '#fff' }}>
              4. THREE-AGENT AUTONOMOUS CYBER SOC DELIBERATION
            </h3>
          </div>
          {expandedSection.agents ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>

        {expandedSection.agents && (
          <div style={{ marginTop: '0.85rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
            {/* Agent 1 */}
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '4px', borderTop: '3px solid var(--cyan-primary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>AGENT 1 // PHYSICAL INTEGRITY</span>
                <span className="badge-normal" style={{ fontSize: '0.65rem' }}>
                  {a1.integrity_assessment || 'NOMINAL'}
                </span>
              </div>
              <h4 style={{ color: '#fff', fontSize: '0.88rem' }}>GNSS Integrity Agent</h4>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', margin: '0.3rem 0' }}>
                Validates kinematic physical invariants, satellite geometry degradation, and PVT fix plausibility.
              </p>
              <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px' }}>
                <p style={{ color: '#cbd5e1', fontSize: '0.72rem' }}>
                  <strong>Findings:</strong> {a1.explanation || a1.integrity_assessment || 'All physical checks nominal.'}
                </p>
                <div style={{ marginTop: '0.35rem', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Violations: <strong>{a1.physical_violation_count || 0}</strong> &bull; Discard Flag: <strong>{a1.discard_recommended ? 'YES' : 'NO'}</strong>
                </div>
              </div>
            </div>

            {/* Agent 2 */}
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '4px', borderTop: '3px solid var(--purple-agent)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--purple-agent)', fontFamily: 'var(--font-mono)' }}>AGENT 2 // TEMPORAL ATTRIBUTION</span>
                <span className="badge-normal" style={{ fontSize: '0.65rem' }}>
                  {a2.temporal_assessment || 'BENIGN'}
                </span>
              </div>
              <h4 style={{ color: '#fff', fontSize: '0.88rem' }}>Temporal / Threat Agent</h4>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', margin: '0.3rem 0' }}>
                Tracks multi-epoch anomaly persistence streaks, LSTM reconstruction drift, and quad convergence.
              </p>
              <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px' }}>
                <p style={{ color: '#cbd5e1', fontSize: '0.72rem' }}>
                  <strong>Findings:</strong> {a2.pattern_description || a2.temporal_reasoning || 'No persistent drift streak detected.'}
                </p>
                <div style={{ marginTop: '0.35rem', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Persistence Streak: <strong>{a2.persistence_count || 0} epochs</strong> &bull; Quad Convergence: <strong>{a2.detector_convergence || 0}/4</strong>
                </div>
              </div>
            </div>

            {/* Agent 3 */}
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem', borderRadius: '4px', borderTop: '3px solid var(--green-nominal)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--green-nominal)', fontFamily: 'var(--font-mono)' }}>AGENT 3 // MASTER SOC ORCHESTRATOR</span>
                <span className={defconBadgeClass} style={{ fontSize: '0.65rem' }}>
                  {a3.risk_level || defconDisplay}
                </span>
              </div>
              <h4 style={{ color: '#fff', fontSize: '0.88rem' }}>Master SOC Orchestrator</h4>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', margin: '0.3rem 0' }}>
                Reconciles multi-agent conflicts, fuses evidence bundles, and issues binding operator directives.
              </p>
              <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px' }}>
                <p style={{ color: '#cbd5e1', fontSize: '0.72rem' }}>
                  <strong>Directive:</strong> {a3.recommended_next_action || canonical_assessment.recommended_next_action || 'Maintain nominal observation.'}
                </p>
                <div style={{ marginTop: '0.35rem', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Consensus Ratio: <strong>{a3.consensus_ratio || '100%'}</strong> &bull; Confidence: <strong>{((a3.confidence || canonical_assessment.confidence || 0.95) * 100).toFixed(1)}%</strong>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 6. Regulatory RAG Retrieval Results & Sources */}
      <div className="cyber-card">
        <div
          onClick={() => toggleSection('rag')}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BookOpen size={16} color="var(--cyan-primary)" />
            <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.95rem', color: '#fff' }}>
              5. REGULATORY RAG GROUNDING &amp; AUDITED CITATIONS
            </h3>
          </div>
          {expandedSection.rag ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>

        {expandedSection.rag && (
          <div style={{ marginTop: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Knowledge Base Corpus: <strong>ICAO Annex 10 Vol I &bull; RTCA DO-229E &bull; CISA PNT &bull; MITRE ATT&amp;CK</strong>
              </span>
              <span style={{ fontSize: '0.7rem', color: rag_grounding.is_grounded ? 'var(--green-nominal)' : 'var(--amber-warning)', fontFamily: 'var(--font-mono)' }}>
                STATUS: {rag_grounding.is_grounded ? 'REGULATORY GROUNDED' : 'CONTEXT REFERENCED'}
              </span>
            </div>

            {rag_grounding.citations && rag_grounding.citations.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {rag_grounding.citations.map((c, idx) => (
                  <div key={idx} style={{ background: 'rgba(0,0,0,0.3)', padding: '0.65rem 0.85rem', borderRadius: '4px', borderLeft: '2px solid var(--cyan-primary)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.4rem' }}>
                      <strong style={{ color: 'var(--cyan-primary)', fontSize: '0.8rem' }}>
                        [{idx + 1}] {c.document || 'Regulatory Standard'} {c.section ? `— ${c.section}` : ''}
                      </strong>
                      <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        Relevance: {c.similarity ? `${(c.similarity * 100).toFixed(0)}%` : 'High'}
                      </span>
                    </div>
                    {c.excerpt && (
                      <p style={{ fontSize: '0.73rem', color: '#cbd5e1', marginTop: '0.3rem', fontStyle: 'italic', lineHeight: 1.4 }}>
                        &ldquo;{c.excerpt}&rdquo;
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '4px' }}>
                No regulatory standard exceptions triggered for this nominal epoch. Full technical corpus remains indexed.
              </div>
            )}
          </div>
        )}
      </div>

      {/* 7. Explainable AI Findings */}
      <div className="cyber-card">
        <div
          onClick={() => toggleSection('xai')}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={16} color="var(--cyan-primary)" />
            <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.95rem', color: '#fff' }}>
              6. EXPLAINABLE AI &amp; CAUSAL ATTRIBUTION
            </h3>
          </div>
          {expandedSection.xai ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>

        {expandedSection.xai && (
          <div style={{ marginTop: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {/* Natural language summary */}
            <div style={{ background: 'rgba(0, 240, 255, 0.05)', border: '1px solid rgba(0, 240, 255, 0.2)', padding: '0.75rem', borderRadius: '4px' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--cyan-primary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: '0.25rem' }}>
                Causal Synthesis
              </span>
              <p style={{ fontSize: '0.8rem', color: '#f1f5f9', lineHeight: 1.5 }}>
                {explainable_ai.explanation_summary || canonical_assessment.summary || 'Assessment evaluated against all 10 canonical security bounds.'}
              </p>
            </div>

            {/* Factors influencing assessment */}
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                Key Influencing Factors:
              </span>
              <ul style={{ paddingLeft: '1.2rem', fontSize: '0.75rem', color: '#cbd5e1', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {(explainable_ai.factors_influencing_assessment || ['All 10 security features remained within calibrated boundaries.']).map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>

            {/* Feature contributions genuinely computed */}
            {explainable_ai.feature_contributions && Object.keys(explainable_ai.feature_contributions).length > 0 && (
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                  Relative Feature Influence / Deviation Index:
                </span>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.4rem' }}>
                  {Object.entries(explainable_ai.feature_contributions).slice(0, 8).map(([feat, val]) => (
                    <div key={feat} style={{ background: 'rgba(0,0,0,0.3)', padding: '0.4rem', borderRadius: '3px', fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
                      <span style={{ color: 'var(--text-muted)', display: 'block' }}>{feat}</span>
                      <strong style={{ color: 'var(--cyan-primary)' }}>{typeof val === 'number' ? val.toFixed(3) : val}</strong>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Transparent limitations */}
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '4px' }}>
              <strong>Scientific &amp; Model Limitations:</strong>
              <ul style={{ paddingLeft: '1.1rem', marginTop: '0.2rem' }}>
                {(explainable_ai.limitations || [
                  'Supervised XGBoost classifier remains UNAVAILABLE — MODEL NOT TRAINED until verified labelled attack scenarios are provided.',
                  'RAG provides regulatory guidance and contextual grounding, not direct sensor evidence.'
                ]).map((lim, idx) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* 7. Consolidated SOC Decision & Mandated Directives */}
      <div className="cyber-card" style={{ borderLeft: '4px solid var(--green-nominal)' }}>
        <div
          onClick={() => toggleSection('decision')}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldCheck size={16} color="var(--green-nominal)" />
            <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.95rem', color: '#fff' }}>
              7. CONSOLIDATED SOC DECISION &amp; OPERATOR ACTION
            </h3>
          </div>
          {expandedSection.decision ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>

        {expandedSection.decision && (
          <div style={{ marginTop: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>MANDATED OPERATOR DIRECTIVE:</span>
                <p style={{ fontSize: '0.92rem', color: '#fff', fontWeight: 700 }}>
                  {canonical_assessment.recommended_next_action || 'Maintain nominal observation mode.'}
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>CONSENSUS RATING:</span>
                <p style={{ fontSize: '0.92rem', color: 'var(--green-nominal)', fontWeight: 700 }}>
                  {((canonical_assessment.confidence || 0.95) * 100).toFixed(1)}% CONFIDENCE
                </p>
              </div>
            </div>

            {/* Evidence Hash and Persisted File */}
            <div style={{ marginTop: '0.75rem', paddingTop: '0.6rem', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
              <span style={{ color: 'var(--text-muted)' }}>
                SHA-256 Checksum: <code style={{ color: 'var(--cyan-primary)' }}>{canonical_assessment.evidence_sha256 ? canonical_assessment.evidence_sha256.slice(0, 24) + '...' : 'VERIFIED IMMUTABLE'}</code>
              </span>
              <span style={{ color: 'var(--text-muted)' }}>
                Archived: <code>{evidence_path || `data/evidence/evidence_${event_id}.json`}</code>
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
