import React, { useState } from 'react';
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Bot,
  AlertCircle,
  Minimize2,
  Maximize2,
  RefreshCw,
  Terminal,
  ChevronRight
} from 'lucide-react';
import { locusApi } from '../api/locusApi';

export const QUICK_QUESTIONS = [
  'Why was this event flagged?',
  'Summarize the 10-D features.',
  'What evidence supports this threat assessment?',
  'Which detectors disagree?',
  'What does the retrieved regulatory context say?'
];

export default function FloatingChatbot({
  selectedEventId,
  bundle,
  conversation = [],
  setConversation
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (questionText) => {
    const q = (questionText || inputQuery).trim();
    if (!q) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString()
    };

    setConversation((prev) => [...prev, userMessage]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const res = await locusApi.querySoc(q, selectedEventId);
      const botMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        text: res.explanation || res.summary || 'Assessment concluded.',
        data: res,
        timestamp: new Date().toLocaleTimeString()
      };
      setConversation((prev) => [...prev, botMessage]);
    } catch (err) {
      const errorMessage = {
        id: Date.now() + 1,
        role: 'error',
        text: `Query failed: ${err.message || 'Unable to connect to SOC API'}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setConversation((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Launcher Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            zIndex: 9999,
            background: 'linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%)',
            border: '1px solid var(--cyan-primary)',
            boxShadow: '0 0 16px rgba(0, 240, 255, 0.4)',
            borderRadius: '24px',
            padding: '0.65rem 1.15rem',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            cursor: 'pointer',
            fontFamily: 'var(--font-hud)',
            fontSize: '0.8rem',
            letterSpacing: '0.05em',
            transition: 'all 0.2s ease'
          }}
        >
          <div style={{ position: 'relative' }}>
            <MessageSquare size={16} color="var(--cyan-primary)" />
            <span style={{
              position: 'absolute',
              top: '-2px',
              right: '-2px',
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: 'var(--green-nominal)',
              boxShadow: '0 0 6px var(--green-nominal)'
            }}></span>
          </div>
          <span>SOC CHATBOT</span>
        </button>
      )}

      {/* Floating Compact Chatbot Drawer / Modal */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            width: '390px',
            maxWidth: 'calc(100vw - 40px)',
            height: '520px',
            maxHeight: 'calc(100vh - 40px)',
            zIndex: 10000,
            background: '#070b14',
            border: '1px solid var(--cyan-primary)',
            borderRadius: '8px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 240, 255, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '0.65rem 0.85rem',
              background: 'linear-gradient(90deg, #0d1b2a 0%, #111e33 100%)',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <Bot size={16} color="var(--cyan-primary)" />
              <span style={{ fontFamily: 'var(--font-hud)', fontSize: '0.82rem', color: '#fff', letterSpacing: '0.04em' }}>
                SOC CHATBOT
              </span>
              <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)', background: 'rgba(0, 240, 255, 0.1)', padding: '0.1rem 0.35rem', borderRadius: '3px' }}>
                {selectedEventId}
              </span>
            </div>

            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              <X size={16} />
            </button>
          </div>

          {/* Quick Question Chips */}
          <div
            style={{
              padding: '0.4rem 0.65rem',
              background: 'rgba(0,0,0,0.3)',
              borderBottom: '1px solid rgba(255,255,255,0.04)',
              display: 'flex',
              gap: '0.35rem',
              overflowX: 'auto',
              whiteSpace: 'nowrap'
            }}
          >
            {QUICK_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                disabled={isLoading}
                style={{
                  background: 'rgba(0, 240, 255, 0.08)',
                  border: '1px solid rgba(0, 240, 255, 0.25)',
                  borderRadius: '12px',
                  padding: '0.2rem 0.55rem',
                  color: 'var(--text-main)',
                  fontSize: '0.68rem',
                  fontFamily: 'var(--font-mono)',
                  cursor: isLoading ? 'not-allowed' : 'pointer'
                }}
              >
                {q}
              </button>
            ))}
          </div>

          {/* Message List */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '0.75rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.65rem'
            }}
          >
            {conversation.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '4rem', fontSize: '0.75rem' }}>
                <Terminal size={24} style={{ margin: '0 auto 0.5rem auto', opacity: 0.5 }} />
                <p>Ask questions regarding active incident <strong>{selectedEventId}</strong>.</p>
                <p style={{ marginTop: '0.35rem', fontSize: '0.7rem' }}>Grounded in real evidence &amp; regulatory standards.</p>
              </div>
            ) : (
              conversation.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    maxWidth: '85%',
                    background: msg.role === 'user'
                      ? 'rgba(0, 240, 255, 0.15)'
                      : msg.role === 'error'
                      ? 'rgba(239, 68, 68, 0.2)'
                      : 'rgba(15, 23, 42, 0.85)',
                    border: msg.role === 'user'
                      ? '1px solid var(--cyan-primary)'
                      : msg.role === 'error'
                      ? '1px solid var(--red-critical)'
                      : '1px solid var(--border-subtle)',
                    borderRadius: '6px',
                    padding: '0.5rem 0.65rem',
                    fontSize: '0.75rem',
                    lineHeight: 1.4
                  }}
                >
                  <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginBottom: '0.2rem', fontFamily: 'var(--font-mono)' }}>
                    {msg.role === 'user' ? 'OPERATOR' : 'LOCUS SOC BOT'} [{msg.timestamp}]
                  </div>
                  <div style={{ color: msg.role === 'error' ? '#f87171' : '#f1f5f9' }}>
                    {msg.text}
                  </div>

                  {msg.data?.recommended_next_action && msg.data.recommended_next_action.length > 0 && (
                    <div style={{ marginTop: '0.4rem', paddingTop: '0.35rem', borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: '0.68rem', color: 'var(--cyan-primary)' }}>
                      <strong>Mandated:</strong> {msg.data.recommended_next_action.join(', ')}
                    </div>
                  )}
                </div>
              ))
            )}

            {isLoading && (
              <div style={{ alignSelf: 'flex-start', background: 'rgba(15, 23, 42, 0.85)', padding: '0.5rem 0.75rem', borderRadius: '6px', fontSize: '0.72rem', color: 'var(--cyan-primary)' }}>
                Auditing active evidence &amp; RAG standards...
              </div>
            )}
          </div>

          {/* Input Box */}
          <div
            style={{
              padding: '0.55rem',
              borderTop: '1px solid var(--border-subtle)',
              background: '#070b14',
              display: 'flex',
              gap: '0.4rem'
            }}
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSend();
              }}
              placeholder={`Ask about ${selectedEventId}...`}
              style={{
                flex: 1,
                background: 'rgba(0,0,0,0.5)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
                color: '#fff',
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                padding: '0.4rem 0.6rem',
                outline: 'none'
              }}
            />
            <button
              onClick={() => handleSend()}
              disabled={isLoading || !inputQuery.trim()}
              className="cyber-btn"
              style={{
                padding: '0.4rem 0.65rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Send size={12} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
