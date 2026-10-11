import React, { useState } from 'react';
import {
  MessageSquare,
  Send,
  Sparkles,
  Bot,
  Terminal,
  ShieldAlert,
  ArrowRight,
  BookOpen
} from 'lucide-react';
import { locusApi } from '../../api/locusApi';
import { QUICK_QUESTIONS } from '../FloatingChatbot';

export default function ChatbotView({
  selectedEventId,
  bundle,
  conversation = [],
  setConversation
}) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (customQuery) => {
    const q = (customQuery || query).trim();
    if (!q) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString()
    };
    setConversation((prev) => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res = await locusApi.querySoc(q, selectedEventId);
      const assistantMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        text: res.explanation || res.summary || 'SOC analysis complete.',
        data: res,
        timestamp: new Date().toLocaleTimeString()
      };
      setConversation((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setConversation((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'error',
          text: `Query failed: ${err.message || 'API connection failure'}`,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner */}
      <div className="cyber-card" style={{ borderLeft: '4px solid var(--cyan-primary)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <MessageSquare size={18} color="var(--cyan-primary)" />
            <div>
              <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.1rem' }}>
                SOC CHATBOT // FORENSIC INTELLIGENCE ASSISTANT
              </h2>
              <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: '0.2rem' }}>
                Grounded in active event <code>{selectedEventId}</code>, 10-D physical features, multi-detector findings, and ICAO/RTCA standards.
              </p>
            </div>
          </div>
          <span className="badge-normal" style={{ fontSize: '0.72rem' }}>
            DETERMINISTIC KNOWLEDGE GROUNDED
          </span>
        </div>
      </div>

      {/* Suggested Quick Question Chips */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {QUICK_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            className="cyber-btn"
            disabled={loading}
            onClick={() => handleSend(q)}
            style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <Sparkles size={12} color="var(--cyan-primary)" />
            <span>{q}</span>
          </button>
        ))}
      </div>

      {/* Main Conversation Terminal Window */}
      <div
        className="terminal-window"
        style={{
          minHeight: '440px',
          maxHeight: '600px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          padding: '1.25rem'
        }}
      >
        {conversation.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '6rem' }}>
            <Bot size={36} style={{ margin: '0 auto 0.75rem auto', opacity: 0.5 }} />
            <h4 style={{ fontFamily: 'var(--font-hud)', color: '#cbd5e1', marginBottom: '0.4rem' }}>
              SOC CHATBOT READY FOR INCIDENT AUDIT
            </h4>
            <p style={{ fontSize: '0.8rem', maxWidth: '500px', margin: '0 auto', color: 'var(--text-dim)' }}>
              Ask questions regarding active incident <strong>{selectedEventId}</strong>.
              All responses are derived exclusively from actual telemetry invariants, detector outputs, and regulatory documents.
            </p>
          </div>
        ) : (
          conversation.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.35rem',
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '85%'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.72rem' }}>
                <strong style={{
                  color: msg.role === 'user' ? 'var(--cyan-primary)' : (msg.role === 'error' ? '#f87171' : 'var(--purple-agent)'),
                  fontFamily: 'var(--font-mono)'
                }}>
                  {msg.role === 'user' ? 'OPERATOR' : 'LOCUS SOC BOT'}
                </strong>
                <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  [{msg.timestamp}]
                </span>
              </div>

              <div
                style={{
                  background: msg.role === 'user'
                    ? 'rgba(0, 240, 255, 0.12)'
                    : (msg.role === 'error' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(15, 23, 42, 0.85)'),
                  border: msg.role === 'user'
                    ? '1px solid var(--cyan-primary)'
                    : (msg.role === 'error' ? '1px solid var(--red-critical)' : '1px solid var(--border-subtle)'),
                  borderRadius: '6px',
                  padding: '0.75rem 0.95rem',
                  fontSize: '0.82rem',
                  lineHeight: 1.5,
                  color: msg.role === 'error' ? '#f87171' : '#f1f5f9'
                }}
              >
                <div>{msg.text}</div>

                {msg.data?.recommended_next_action && msg.data.recommended_next_action.length > 0 && (
                  <div style={{
                    marginTop: '0.65rem',
                    paddingTop: '0.5rem',
                    borderTop: '1px solid rgba(255,255,255,0.08)',
                    fontSize: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    color: 'var(--cyan-primary)'
                  }}>
                    <ArrowRight size={12} />
                    <span><strong>Mandated Action:</strong> {msg.data.recommended_next_action.join(', ')}</span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {loading && (
          <div style={{ alignSelf: 'flex-start', background: 'rgba(15, 23, 42, 0.85)', padding: '0.6rem 0.9rem', borderRadius: '6px', fontSize: '0.78rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
            Auditing 10-D features &amp; RAG regulatory corpus for {selectedEventId}...
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="cyber-card" style={{ padding: '0.75rem' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{ display: 'flex', gap: '0.6rem' }}
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Ask plain-English inquiry regarding event ${selectedEventId}...`}
            style={{
              flex: 1,
              background: 'rgba(6, 11, 22, 0.8)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              padding: '0.6rem 0.85rem',
              color: '#fff',
              fontSize: '0.85rem',
              fontFamily: 'var(--font-mono)',
              outline: 'none'
            }}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="cyber-btn"
            style={{
              padding: '0.6rem 1.4rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontWeight: 700
            }}
          >
            <Send size={14} />
            <span>Submit</span>
          </button>
        </form>
      </div>
    </div>
  );
}
