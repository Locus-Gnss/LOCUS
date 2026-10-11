import React, { useState } from 'react';
import { Terminal, Send, Sparkles, AlertCircle } from 'lucide-react';
import { locusApi } from '../../api/locusApi';

export default function QueryView({ selectedEventId, bundle }) {
  const [query, setQuery] = useState('Why was this event flagged?');
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);

  const presets = [
    'Why was this event flagged?',
    'Is there evidence of cognitive drag-off?',
    'Summarize kinematic velocity and acceleration bounds',
    'Evaluate constellation geometry and satellite churn',
  ];

  const handleSend = async (customQuery) => {
    const q = customQuery || query;
    if (!q.trim()) return;

    const userMsg = { role: 'operator', text: q, time: new Date().toLocaleTimeString() };
    setConversation((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await locusApi.querySoc(q, selectedEventId);
      const assistantMsg = {
        role: 'locus-soc',
        time: new Date().toLocaleTimeString(),
        data: res,
      };
      setConversation((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setConversation((prev) => [
        ...prev,
        {
          role: 'system-error',
          time: new Date().toLocaleTimeString(),
          text: `Query processing failed: ${err.message}`,
        },
      ]);
    } finally {
      setLoading(false);
      setQuery('');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner */}
      <div className="cyber-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Terminal size={18} color="var(--cyan-primary)" />
          <div>
            <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.1rem' }}>
              NATURAL-LANGUAGE FORENSIC QUERY TERMINAL
            </h2>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: '0.2rem' }}>
              Ask plain-English forensic inquiries. Grounded strictly in active Evidence Bundle <code>{selectedEventId}</code> with zero fabrication.
            </p>
          </div>
        </div>
      </div>

      {/* Preset Query Chips */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {presets.map((p, idx) => (
          <button
            key={idx}
            className="cyber-btn"
            onClick={() => {
              setQuery(p);
              handleSend(p);
            }}
            style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
          >
            <Sparkles size={12} />
            <span>{p}</span>
          </button>
        ))}
      </div>

      {/* Terminal Conversation Window */}
      <div className="terminal-window" style={{ minHeight: '380px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {conversation.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '4rem' }}>
            <Terminal size={32} style={{ margin: '0 auto 0.75rem auto', opacity: 0.4 }} />
            <p>Terminal ready. Enter an operational query below or select a preset.</p>
          </div>
        ) : (
          conversation.map((msg, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span style={{
                  color: msg.role === 'operator' ? 'var(--cyan-primary)' : 'var(--purple-agent)',
                  fontWeight: 700
                }}>
                  {msg.role === 'operator' ? 'OPERATOR' : 'LOCUS SOC AI'}
                </span>
                <span>[{msg.time}]</span>
              </div>

              {msg.text && (
                <div style={{
                  padding: '0.6rem 0.85rem',
                  borderRadius: '4px',
                  background: msg.role === 'operator' ? 'rgba(0, 240, 255, 0.08)' : 'rgba(239, 68, 68, 0.1)',
                  color: msg.role === 'operator' ? '#e2e8f0' : '#f87171',
                  border: '1px solid var(--border-subtle)'
                }}>
                  {msg.text}
                </div>
              )}

              {msg.data && (
                <div style={{
                  padding: '0.85rem',
                  borderRadius: '4px',
                  background: 'rgba(13, 20, 38, 0.75)',
                  border: '1px solid var(--border-glow)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', borderBottom: '1px solid rgba(0,240,255,0.1)', paddingBottom: '0.4rem' }}>
                    <span style={{ color: 'var(--cyan-primary)', fontFamily: 'var(--font-hud)', fontSize: '0.8rem' }}>
                      Status: {msg.data.current_status || 'NOMINAL'}
                    </span>
                    <span style={{ color: 'var(--green-nominal)', fontSize: '0.72rem' }}>
                      DEFCON: {msg.data.defcon_level || 'DEFCON_5'}
                    </span>
                  </div>

                  <p style={{ color: '#f1f5f9', fontSize: '0.84rem', lineHeight: 1.5, marginBottom: '0.65rem' }}>
                    {msg.data.explanation || msg.data.response || 'No explanation generated.'}
                  </p>

                  {msg.data.cited_evidence && msg.data.cited_evidence.length > 0 && (
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '0.4rem' }}>
                      <strong style={{ color: 'var(--cyan-primary)' }}>Verified Evidence Fields: </strong>
                      {msg.data.cited_evidence.join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Input Box */}
      <div className="cyber-card" style={{ padding: '0.65rem' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{ display: 'flex', gap: '0.5rem' }}
        >
          <input
            type="text"
            className="cyber-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type query to SOC assistant..."
            style={{ flex: 1, padding: '0.6rem 0.85rem' }}
          />
          <button type="submit" className="cyber-btn cyber-btn-active" disabled={loading} style={{ padding: '0.6rem 1rem' }}>
            <Send size={14} />
            <span>{loading ? 'Analyzing...' : 'Execute'}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
