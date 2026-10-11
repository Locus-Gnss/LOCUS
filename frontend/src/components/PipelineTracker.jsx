import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ArrowRight,
  Database,
  ShieldCheck,
  Cpu,
  Layers,
  Bot,
  BookOpen,
  FileSearch,
  LayoutDashboard,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export const PIPELINE_STAGES = [
  {
    id: 'ingestion',
    name: 'Data Ingestion',
    icon: Database,
    desc: 'Receives raw NMEA strings, JSON payloads, or CSV telemetry stream.',
    defaultDetails: 'Raw stream buffered and parsed into memory.'
  },
  {
    id: 'validation',
    name: 'Validation',
    icon: ShieldCheck,
    desc: 'Sanitizes WGS-84 coordinates, schema types, and sentence checksums.',
    defaultDetails: 'WGS-84 latitude/longitude bounds (-90..90, -180..180) verified.'
  },
  {
    id: 'preprocessing',
    name: 'Preprocessing',
    icon: Cpu,
    desc: 'Monotonic time ordering, deduplication, and max 5.0s gap bounds.',
    defaultDetails: 'Chronological epoch alignment and duplicate removal executed.'
  },
  {
    id: 'features',
    name: 'Feature Engineering',
    icon: Layers,
    desc: 'Computes canonical 10-D spatial, kinematic, and geometric vector.',
    defaultDetails: '10-D vector: Haversine disp, vel, acc, jerk, bearing, DOP, churn.'
  },
  {
    id: 'detection',
    name: 'Detection Engine',
    icon: ShieldCheck,
    desc: 'Multi-detector quad: Physical rules, Isolation Forest, XGBoost*, LSTM.',
    defaultDetails: 'Physical invariants, spatial outlier, and temporal drift evaluated.'
  },
  {
    id: 'agents',
    name: 'Multi-Agent Analysis',
    icon: Bot,
    desc: 'Integrity Agent and Temporal Threat Agent deliberate independently.',
    defaultDetails: 'Kinematic health vs. temporal persistence streak analyzed.'
  },
  {
    id: 'rag',
    name: 'RAG Retrieval',
    icon: BookOpen,
    desc: 'Grounds findings against ICAO Annex 10, RTCA DO-229E, and CISA specs.',
    defaultDetails: 'Aviation & PNT regulatory corpus audited with vector similarity.'
  },
  {
    id: 'soc_decision',
    name: 'SOC Decision',
    icon: LayoutDashboard,
    desc: 'Master SOC Orchestrator reconciles conflicts and assigns DEFCON.',
    defaultDetails: 'Consensus synthesized; mandatory mitigation directives issued.'
  },
  {
    id: 'evidence',
    name: 'Evidence Storage',
    icon: FileSearch,
    desc: 'Cryptographic SHA-256 evidence bundle generated and archived.',
    defaultDetails: 'Immutable payload hashed with SHA-256 checksum.'
  },
  {
    id: 'results',
    name: 'Results Dashboard',
    icon: CheckCircle2,
    desc: 'Synchronizes authoritative canonical assessment across all consoles.',
    defaultDetails: 'Event dispatched to Executive Overview, Quad, and Alert Center.'
  }
];

export default function PipelineTracker({
  runId,
  currentStageId,
  stageData = {},
  isExecuting = false,
  compact = false,
  selectedStageId,
  onSelectStage
}) {
  const [expandedStage, setExpandedStage] = useState(null);

  const getStageStatus = (stageId, index) => {
    if (stageData[stageId]?.status) {
      return stageData[stageId].status;
    }
    if (isExecuting) {
      const currentIndex = PIPELINE_STAGES.findIndex((s) => s.id === currentStageId);
      if (currentIndex === -1) return 'PENDING';
      if (index < currentIndex) return 'COMPLETED';
      if (index === currentIndex) return 'RUNNING';
      return 'PENDING';
    }
    // Default when viewing an existing completed event
    return 'COMPLETED';
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'RUNNING':
        return {
          text: 'RUNNING',
          bg: 'rgba(0, 240, 255, 0.15)',
          color: 'var(--cyan-primary)',
          border: '1px solid var(--cyan-primary)'
        };
      case 'COMPLETED':
      case 'DONE':
        return {
          text: 'COMPLETED',
          bg: 'rgba(16, 185, 129, 0.15)',
          color: 'var(--green-nominal)',
          border: '1px solid var(--green-nominal)'
        };
      case 'FAILED':
        return {
          text: 'FAILED',
          bg: 'rgba(239, 68, 68, 0.2)',
          color: 'var(--red-critical)',
          border: '1px solid var(--red-critical)'
        };
      case 'UNAVAILABLE':
        return {
          text: 'UNAVAILABLE',
          bg: 'rgba(245, 158, 11, 0.15)',
          color: 'var(--amber-warning)',
          border: '1px solid var(--amber-warning)'
        };
      default:
        return {
          text: 'PENDING',
          bg: 'rgba(255, 255, 255, 0.05)',
          color: 'var(--text-muted)',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        };
    }
  };

  if (compact) {
    return (
      <div className="cyber-card" style={{ padding: '0.85rem 1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-hud)', textTransform: 'uppercase', color: 'var(--cyan-primary)', letterSpacing: '0.08em' }}>
            CYBER-PHYSICAL SECURITY PIPELINE FLOW (10 STAGES)
          </span>
          {runId && (
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Run ID: <strong style={{ color: '#fff' }}>{runId}</strong>
            </span>
          )}
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(95px, 1fr))',
          gap: '0.4rem',
          alignItems: 'center'
        }}>
          {PIPELINE_STAGES.map((stage, idx) => {
            const status = getStageStatus(stage.id, idx);
            const badge = getStatusBadge(status);
            return (
              <div
                key={stage.id}
                style={{
                  background: 'rgba(5, 8, 16, 0.85)',
                  border: badge.border,
                  borderRadius: '4px',
                  padding: '0.45rem 0.35rem',
                  textAlign: 'center'
                }}
              >
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#e2e8f0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {stage.name}
                </div>
                <div style={{ marginTop: '0.25rem' }}>
                  <span style={{
                    fontSize: '0.6rem',
                    fontFamily: 'var(--font-mono)',
                    padding: '0.05rem 0.3rem',
                    borderRadius: '2px',
                    background: badge.bg,
                    color: badge.color,
                    fontWeight: 600
                  }}>
                    {badge.text}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="cyber-card" style={{ borderLeft: '4px solid var(--cyan-primary)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem', color: '#fff' }}>
            END-TO-END SECURITY ANALYSIS PIPELINE
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.15rem' }}>
            Deterministic 10-stage progression tracking real backend execution and artifact generation.
          </p>
        </div>
        {runId && (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--cyan-primary)', background: 'rgba(0, 240, 255, 0.08)', padding: '0.2rem 0.6rem', borderRadius: '4px', border: '1px solid rgba(0, 240, 255, 0.2)' }}>
            RUN ID: {runId}
          </div>
        )}
      </div>

      {/* Connected 10-Stage Flow Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '0.65rem'
        }}>
          {PIPELINE_STAGES.map((stage, idx) => {
            const status = getStageStatus(stage.id, idx);
            const badge = getStatusBadge(status);
            const Icon = stage.icon;
            const details = stageData[stage.id]?.details || stage.defaultDetails;
            const duration = stageData[stage.id]?.duration_ms;
            const recordCount = stageData[stage.id]?.records_count;
            const isSelected = selectedStageId === stage.id || expandedStage === stage.id;

            return (
              <div
                key={stage.id}
                onClick={() => {
                  setExpandedStage(expandedStage === stage.id ? null : stage.id);
                  if (onSelectStage) onSelectStage(stage.id);
                }}
                style={{
                  background: isSelected ? 'rgba(0, 240, 255, 0.06)' : 'rgba(5, 8, 16, 0.7)',
                  border: isSelected ? '1px solid var(--cyan-primary)' : badge.border,
                  borderRadius: '6px',
                  padding: '0.65rem 0.75rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      0{idx + 1}
                    </span>
                    <Icon size={14} color="var(--cyan-primary)" />
                  </div>
                  <span style={{
                    fontSize: '0.62rem',
                    fontFamily: 'var(--font-mono)',
                    padding: '0.1rem 0.35rem',
                    borderRadius: '3px',
                    background: badge.bg,
                    color: badge.color,
                    fontWeight: 700
                  }}>
                    {badge.text}
                  </span>
                </div>

                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f1f5f9', marginBottom: '0.2rem' }}>
                  {stage.name}
                </div>

                <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', lineHeight: 1.3 }}>
                  {stage.desc}
                </div>

                {(duration !== undefined || recordCount !== undefined) && (
                  <div style={{ marginTop: '0.4rem', paddingTop: '0.35rem', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    {recordCount !== undefined && <span>{recordCount} records</span>}
                    {duration !== undefined && <span>{duration.toFixed(1)}ms</span>}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Selected / Expanded Stage Output Detail Box */}
        {expandedStage && (
          <div style={{
            marginTop: '0.5rem',
            padding: '0.85rem 1rem',
            background: 'rgba(0, 0, 0, 0.45)',
            border: '1px solid var(--border-glow)',
            borderRadius: '6px',
            fontSize: '0.78rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <strong style={{ color: 'var(--cyan-primary)', fontFamily: 'var(--font-hud)' }}>
                STAGE AUDIT: {PIPELINE_STAGES.find((s) => s.id === expandedStage)?.name?.toUpperCase()}
              </strong>
              <button
                className="cyber-btn"
                onClick={() => setExpandedStage(null)}
                style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem' }}
              >
                Close
              </button>
            </div>
            <p style={{ color: '#cbd5e1', lineHeight: 1.4 }}>
              {stageData[expandedStage]?.details || PIPELINE_STAGES.find((s) => s.id === expandedStage)?.defaultDetails}
            </p>
            {stageData[expandedStage]?.error && (
              <div style={{ marginTop: '0.4rem', color: '#f87171', fontFamily: 'var(--font-mono)' }}>
                Error: {stageData[expandedStage].error}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
