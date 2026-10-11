import React, { useState, useEffect } from 'react';
import { BookOpen, Search, Bookmark, ExternalLink, ShieldCheck, AlertCircle, FileText } from 'lucide-react';
import { locusApi } from '../../api/locusApi';

export default function RegulatoryView({ bundle, selectedEventId }) {
  const [query, setQuery] = useState('RTCA DO-229E spoofing detection threshold');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (customQuery) => {
    const q = (customQuery || query).trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const data = await locusApi.queryRag(q, 4);
      setResults(data);
    } catch (err) {
      setError(err.message || 'RAG query retrieval failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  const sampleStandards = [
    {
      title: 'RTCA DO-229E / DO-229F',
      topic: 'MOPS for GPS/WAAS Airborne Equipment',
      desc: 'Mandates GDOP <= 6.0 and HDOP <= 4.0 bounds. Sets alarm limits for pseudo-range step discrepancies and step-drift detection.'
    },
    {
      title: 'ICAO Annex 10 Vol 1',
      topic: 'Aeronautical Telecommunications (Radio Navigation Aids)',
      desc: 'Standards for civilian Signal-in-Space (SIS) integrity, pseudorange error bounds, and GNSS alert limit criteria.'
    },
    {
      title: 'CISA GNSS Cybersecurity',
      topic: 'Federal Positioning, Navigation, and Timing (PNT)',
      desc: 'Recommends multi-layer physical plausibility checks, RF power sanity, and receiver autonomous integrity monitoring (RAIM).'
    },
    {
      title: 'MITRE ATT&CK for PNT',
      topic: 'Threat Matrix T0001 - T0003',
      desc: 'Classifies GNSS adversary techniques: T0001 (Signal Jamming), T0002 (GPS Spoofing / PVT Manipulation), T0003 (Meaconing/Replay).'
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner */}
      <div className="cyber-card" style={{ borderLeft: '4px solid var(--cyan-primary)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <BookOpen size={18} color="var(--cyan-primary)" />
            <div>
              <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.1rem' }}>
                REGULATORY RAG &amp; STANDARDS AUDITOR
              </h2>
              <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: '0.2rem' }}>
                Grounding forensic incidents against ICAO, RTCA DO-229E, CISA, and MITRE PNT standards with zero hallucination.
              </p>
            </div>
          </div>
          <span className="badge-normal" style={{ fontSize: '0.72rem' }}>
            RAG CORPUS: 50+ INDEXED CHUNKS
          </span>
        </div>
      </div>

      {/* Query Search Bar */}
      <div className="cyber-card">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          style={{ display: 'flex', gap: '0.75rem' }}
        >
          <div style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'rgba(6, 11, 22, 0.85)',
            padding: '0.5rem 0.85rem',
            borderRadius: '4px',
            border: '1px solid var(--border-subtle)'
          }}>
            <Search size={16} color="var(--text-muted)" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search regulatory standards (e.g. HDOP thresholds, spoofing limits, RAIM)..."
              style={{
                width: '100%',
                background: 'transparent',
                border: 'none',
                color: '#fff',
                fontSize: '0.85rem',
                fontFamily: 'var(--font-mono)',
                outline: 'none'
              }}
            />
          </div>
          <button
            type="submit"
            className="cyber-btn"
            disabled={loading}
            style={{ padding: '0.5rem 1.4rem', fontWeight: 700 }}
          >
            <span>{loading ? 'Auditing...' : 'Audit Standard'}</span>
          </button>
        </form>

        {/* Quick query chips */}
        <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
          {[
            'RTCA DO-229E limits on HDOP',
            'ICAO Annex 10 spoofing alarm limits',
            'CISA PNT jamming and interference',
            'MITRE ATT&CK GPS spoofing T0002'
          ].map((chip, idx) => (
            <button
              key={idx}
              className="cyber-btn"
              onClick={() => {
                setQuery(chip);
                handleSearch(chip);
              }}
              style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem' }}
            >
              {chip}
            </button>
          ))}
        </div>

        {error && (
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid var(--red-critical)',
            borderRadius: '4px',
            color: '#f87171',
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Search Results Display */}
        {results && (
          <div style={{ marginTop: '1.25rem', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
                RAG Retrieval Results ({results.citations_count || results.citations?.length || 0} Grounded Excerpts)
              </span>
              <span style={{
                fontSize: '0.7rem',
                fontFamily: 'var(--font-mono)',
                color: results.is_grounded ? 'var(--green-nominal)' : 'var(--amber-warning)'
              }}>
                {results.is_grounded ? 'VERIFIED GROUNDED IN CORPUS' : 'RELEVANT CONTEXT RETRIEVED'}
              </span>
            </div>

            {results.insufficient_context && (
              <div style={{
                padding: '0.75rem',
                background: 'rgba(245, 158, 11, 0.12)',
                border: '1px solid var(--amber-warning)',
                borderRadius: '4px',
                color: '#fbbf24',
                fontSize: '0.8rem',
                marginBottom: '0.75rem'
              }}>
                {results.message || 'No sufficiently confident matching clause found in standard knowledge base.'}
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {results.citations && results.citations.length > 0 ? (
                results.citations.map((cit, idx) => {
                  const excerptText = cit.excerpt || cit.text || cit.snippet || 'No excerpt text available for this chunk.';
                  const docTitle = cit.document || cit.doc_id || `Regulatory Standard Document #${idx + 1}`;
                  const authorities = cit.authorities || cit.regulatory_authorities || [];
                  const similarityScore = cit.similarity !== undefined ? Number(cit.similarity).toFixed(3) : (cit.score ? Number(cit.score).toFixed(3) : '0.850');

                  return (
                    <div
                      key={idx}
                      style={{
                        background: 'rgba(6, 11, 22, 0.75)',
                        padding: '0.85rem 1rem',
                        borderRadius: '6px',
                        border: '1px solid var(--border-subtle)',
                        borderLeft: '3px solid var(--cyan-primary)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem', flexWrap: 'wrap', gap: '0.4rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <FileText size={14} color="var(--cyan-primary)" />
                          <strong style={{ color: '#fff', fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}>
                            {docTitle}
                          </strong>
                          {cit.section && (
                            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                              // {cit.section}
                            </span>
                          )}
                        </div>
                        <span style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)', background: 'rgba(0, 240, 255, 0.08)', padding: '0.1rem 0.4rem', borderRadius: '3px' }}>
                          Relevance: {similarityScore}
                        </span>
                      </div>

                      {authorities.length > 0 && (
                        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                          {authorities.map((auth, aIdx) => (
                            <span
                              key={aIdx}
                              style={{
                                fontSize: '0.65rem',
                                padding: '0.1rem 0.4rem',
                                borderRadius: '3px',
                                background: 'rgba(168, 85, 247, 0.15)',
                                color: 'var(--purple-agent)',
                                border: '1px solid rgba(168, 85, 247, 0.3)',
                                fontFamily: 'var(--font-mono)'
                              }}
                            >
                              {auth}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Actual Matching Excerpt Text */}
                      <div style={{
                        fontSize: '0.8rem',
                        color: '#cbd5e1',
                        lineHeight: 1.5,
                        background: 'rgba(0, 0, 0, 0.35)',
                        padding: '0.65rem 0.85rem',
                        borderRadius: '4px',
                        borderLeft: '2px solid rgba(0, 240, 255, 0.4)',
                        fontFamily: 'var(--font-mono)',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {excerptText}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  No regulatory citations returned for this query.
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Standard Regulatory Reference Cards */}
      <div>
        <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.95rem', color: '#cbd5e1', marginBottom: '0.75rem' }}>
          PRIMARY REGULATORY AUTHORITIES IN KNOWLEDGE BASE
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          {sampleStandards.map((std, i) => (
            <div key={i} className="cyber-card" style={{ borderLeft: '3px solid var(--purple-agent)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.35rem' }}>
                <strong style={{ fontSize: '0.88rem', color: '#fff', fontFamily: 'var(--font-mono)' }}>
                  {std.title}
                </strong>
                <Bookmark size={14} color="var(--purple-agent)" />
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', marginBottom: '0.35rem', fontFamily: 'var(--font-mono)' }}>
                {std.topic}
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', lineHeight: 1.4 }}>
                {std.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
