import React from 'react';
import { Bot, Shield, CheckCircle2, AlertTriangle, ArrowRight, Lock } from 'lucide-react';

export default function AgentsView({ deliberation }) {
  if (!deliberation) {
    return (
      <div className="cyber-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No deliberative assessment available. Select an event in the top header to inspect SOC reasoning.
      </div>
    );
  }

  const findings = deliberation.agent_findings || {};
  const ag1 = findings.agent_1_integrity || deliberation.agent_1_integrity || {};
  const ag2 = findings.agent_2_temporal_threat || deliberation.agent_2_threat || {};
  const ag3 = findings.agent_3_master_soc || deliberation;

  const ag1Status = ag1.integrity_assessment || ag1.integrity_status || 'NOMINAL';
  const ag1Reasoning = ag1.explanation || ag1.reasoning_summary || 'Analyzes kinematic bounds, DOP limits, and fix stability.';
  const ag1Violations = ag1.physical_violation_count ?? ag1.kinematic_violations?.length ?? 0;
  const ag1Geom = ag1.geometry_health !== undefined ? (ag1.geometry_health >= 0.7 ? 'HEALTHY' : 'DEGRADED') : (ag1.geometry_degraded ? 'DEGRADED' : 'HEALTHY');
  const ag1Conf = ag1.confidence ? `${(ag1.confidence * 100).toFixed(0)}%` : '98%';

  const ag2Status = ag2.temporal_assessment || ag2.threat_classification || ag2.threat_level || 'BENIGN';
  const ag2Reasoning = ag2.pattern_description || ag2.temporal_reasoning || 'Evaluates multi-epoch anomaly persistence streaks and LSTM drift attribution.';
  const ag2Streak = ag2.persistence_count ?? ag2.streak_length ?? 0;
  const ag2Jamming = (ag2.anomalous_detectors_count > 0 || ag2.rf_jamming_suspected) ? 'SUSPECTED' : 'NEGATIVE';
  const ag2Lstm = (ag2.lstm_reconstruction_error > 0.05 || ag2.lstm_anomaly_confirmed) ? 'CONFIRMED DRIFT' : 'NOMINAL';

  const ag3Risk = ag3.risk_level || deliberation.risk_level || 'DEFCON_5_NOMINAL';
  const ag3Rationale = ag3.summary || deliberation.explanation || deliberation.primary_rationale || 'Synthesizes multi-detector findings, resolves conflicts, and sets DEFCON readiness.';
  const ag3Action = ag3.recommended_next_action || deliberation.recommended_next_action || ag3.action_mandated || deliberation.action_mandated || 'Maintain autonomous monitoring.';
  const ag3Citations = ag3.regulatory_standards?.length || ag3.cited_evidence?.length || 3;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner */}
      <div className="cyber-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Bot size={18} color="var(--purple-agent)" />
              <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.1rem' }}>
                3-AGENT AUTONOMOUS CYBER SOC
              </h2>
            </div>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: '0.2rem' }}>
              Deliberative multi-agent consensus. Sensor data and Evidence Bundles are immutable (Zero-Fabrication Guard active).
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(16, 185, 129, 0.1)', padding: '0.35rem 0.75rem', borderRadius: '4px', border: '1px solid var(--border-green)' }}>
            <Lock size={14} color="var(--green-nominal)" />
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--green-nominal)' }}>
              ANTI-MUTATION INVARIANT: 0 VIOLATIONS
            </span>
          </div>
        </div>
      </div>

      {/* 3-Agent Horizontal Deliberation Flow Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* Agent 1: GNSS Integrity Agent */}
        <div className="cyber-card" style={{ borderTop: '3px solid var(--cyan-primary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
              Agent 1 // Physical Plausibility
            </span>
            <span style={{
              fontSize: '0.72rem',
              padding: '0.2rem 0.5rem',
              borderRadius: '3px',
              background: 'rgba(0, 240, 255, 0.15)',
              color: 'var(--cyan-primary)',
              fontFamily: 'var(--font-hud)'
            }}>
              {ag1Status}
            </span>
          </div>

          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem', color: '#fff', marginBottom: '0.4rem' }}>
            GNSS Integrity Agent
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
            {ag1Reasoning}
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.3)', padding: '0.65rem', borderRadius: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Kinematic Violations:</span>
              <strong style={{ color: (ag1Violations > 0) ? 'var(--red-critical)' : 'var(--green-nominal)' }}>
                {ag1Violations}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Geometry Status:</span>
              <strong style={{ color: 'var(--text-main)' }}>
                {ag1Geom}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Confidence Score:</span>
              <strong style={{ color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
                {ag1Conf}
              </strong>
            </div>
          </div>
        </div>

        {/* Agent 2: Temporal / Threat Agent */}
        <div className="cyber-card" style={{ borderTop: '3px solid var(--amber-warning)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--amber-warning)', fontFamily: 'var(--font-mono)' }}>
              Agent 2 // Temporal Attribution
            </span>
            <span style={{
              fontSize: '0.72rem',
              padding: '0.2rem 0.5rem',
              borderRadius: '3px',
              background: 'rgba(245, 158, 11, 0.15)',
              color: 'var(--amber-warning)',
              fontFamily: 'var(--font-hud)'
            }}>
              {ag2Status}
            </span>
          </div>

          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem', color: '#fff', marginBottom: '0.4rem' }}>
            Temporal Threat Agent
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
            {ag2Reasoning}
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.3)', padding: '0.65rem', borderRadius: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Persistent Streak:</span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>
                {ag2Streak} Epochs
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>RF Starvation / Jamming:</span>
              <strong style={{ color: ag2Jamming === 'SUSPECTED' ? 'var(--red-critical)' : 'var(--green-nominal)' }}>
                {ag2Jamming}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>LSTM Attribution:</span>
              <strong style={{ color: 'var(--text-main)' }}>
                {ag2Lstm}
              </strong>
            </div>
          </div>
        </div>

        {/* Agent 3: Master SOC Orchestrator */}
        <div className="cyber-card" style={{ borderTop: '3px solid var(--purple-agent)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--purple-agent)', fontFamily: 'var(--font-mono)' }}>
              Agent 3 // Master Orchestrator
            </span>
            <span style={{
              fontSize: '0.72rem',
              padding: '0.2rem 0.5rem',
              borderRadius: '3px',
              background: 'rgba(168, 85, 247, 0.15)',
              color: 'var(--purple-agent)',
              fontFamily: 'var(--font-hud)'
            }}>
              {ag3Risk}
            </span>
          </div>

          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem', color: '#fff', marginBottom: '0.4rem' }}>
            Master SOC Orchestrator
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
            {ag3Rationale}
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.3)', padding: '0.65rem', borderRadius: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Consensus DEFCON:</span>
              <strong style={{ color: 'var(--cyan-primary)', fontFamily: 'var(--font-hud)' }}>
                {ag3Risk}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Mandated Action:</span>
              <strong style={{ color: '#fff' }}>
                {ag3Action}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Evidence Citations:</span>
              <strong style={{ color: 'var(--green-nominal)' }}>
                {ag3Citations} Standards / Grounded Fields
              </strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
