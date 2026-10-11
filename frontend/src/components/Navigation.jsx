import React from 'react';
import {
  LayoutDashboard,
  Upload,
  CheckCircle2,
  Activity,
  MapPin,
  Cpu,
  Layers,
  AlertOctagon,
  FileSearch,
  Bot,
  BookOpen,
  MessageSquare,
  HeartPulse
} from 'lucide-react';

export default function Navigation({ activeTab, onSelectTab, alertsCount = 0 }) {
  const tabs = [
    { id: 'overview', label: 'Executive Overview', icon: LayoutDashboard },
    { id: 'ingestion', label: 'Live Data Input', icon: Upload },
    { id: 'results', label: 'Pipeline Results', icon: CheckCircle2 },
    { id: 'telemetry', label: 'Live Telemetry', icon: Activity },
    { id: 'map', label: 'Geospatial Map', icon: MapPin },
    { id: 'features', label: '10-D Security Vectors', icon: Cpu },
    { id: 'detectors', label: 'Detection Quad', icon: Layers },
    { id: 'alerts', label: 'Alert Center', icon: AlertOctagon, count: alertsCount },
    { id: 'evidence', label: 'Evidence Bundle', icon: FileSearch },
    { id: 'agents', label: '3-Agent Cyber SOC', icon: Bot },
    { id: 'regulatory', label: 'Regulatory RAG', icon: BookOpen },
    { id: 'chatbot', label: 'SOC Chatbot', icon: MessageSquare },
    { id: 'health', label: 'System Health', icon: HeartPulse },
  ];

  return (
    <nav style={{ display: 'flex', gap: '0.4rem', overflowX: 'auto', paddingBottom: '0.5rem', marginBottom: '1.25rem' }}>
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            className={`cyber-btn ${isActive ? 'cyber-btn-active' : ''}`}
            onClick={() => onSelectTab(tab.id)}
            style={{
              padding: '0.45rem 0.85rem',
              whiteSpace: 'nowrap',
              fontSize: '0.8rem',
              borderRadius: '6px'
            }}
          >
            <Icon size={14} />
            <span>{tab.label}</span>
            {tab.count !== undefined && tab.count > 0 && (
              <span style={{
                background: 'rgba(239, 68, 68, 0.25)',
                color: '#ff4d6d',
                border: '1px solid var(--red-critical)',
                fontSize: '0.65rem',
                padding: '0.05rem 0.35rem',
                borderRadius: '10px',
                fontWeight: 700
              }}>
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
}
