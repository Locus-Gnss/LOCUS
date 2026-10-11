/**
 * LOCUS Cyber SOC API Client
 * Connects frontend directly to FastAPI REST backend on :8000
 */

const rawBase = import.meta.env.VITE_API_URL || '';
const BASE_URL = rawBase.trim().replace(/\/+$/, '');

export function getApiBaseUrl() {
  return BASE_URL || 'http://127.0.0.1:8000';
}

async function request(endpoint, options = {}) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${BASE_URL}${cleanEndpoint}`;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || 45000);
    const res = await fetch(url, {
      signal: options.signal || controller.signal,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    clearTimeout(timeoutId);
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    if (err.name === 'AbortError') {
      const coldMsg = 'Backend request timed out (service may be waking from cold start). Please wait 30 seconds and retry.';
      console.warn(coldMsg);
      throw new Error(coldMsg);
    }
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const locusApi = {
  getBaseUrl: getApiBaseUrl,
  // System Health
  getHealth: () => request('/api/health'),

  // Events & Evidence
  getEvents: () => request('/api/events'),
  getEventDetail: (eventId) => request(`/api/events/${eventId}`),
  getEvidence: (eventId) => request(`/api/evidence/${eventId}`),

  // Telemetry
  getLatestTelemetry: () => request('/api/telemetry/latest'),
  getTelemetryHistory: (limit = 100, sessionId = null) => {
    let q = `?limit=${limit}`;
    if (sessionId) q += `&session_id=${sessionId}`;
    return request(`/api/telemetry/history${q}`);
  },

  // 10-D Security Features
  getLatestFeatures: () => request('/api/features/latest'),

  // Alerts
  getAlerts: () => request('/api/alerts'),
  getAlertDetail: (alertId) => request(`/api/alerts/${alertId}`),

  // SOC Agents
  getAgentsStatus: () => request('/api/agents/status'),
  deliberateEvent: (eventId) => request('/api/soc/deliberate', {
    method: 'POST',
    body: JSON.stringify({ event_id: eventId }),
  }),

  // Regulatory RAG & NL Query
  queryRag: (query, topK = 3) => request('/api/rag/query', {
    method: 'POST',
    body: JSON.stringify({ query, top_k: topK }),
  }),

  querySoc: (query, eventId = null) => request('/api/query', {
    method: 'POST',
    body: JSON.stringify({ query, event_id: eventId }),
  }),

  // Canonical Assessment (Single Source of Truth)
  getCanonicalAssessment: (eventId) => request(`/api/events/${eventId}/assessment`),

  // Live Data Pipeline Ingestion
  processPipeline: (payload) => request('/api/pipeline/process', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  getLatestPipelineRun: () => request('/api/pipeline/latest'),
  getPipelineRun: (runId) => request(`/api/pipeline/runs/${runId}`),

  // Model Readiness and Controlled Training
  getModelsStatus: () => request('/api/models/status'),
  getXGBoostInfo: () => request('/api/models/xgboost/info'),
  trainModel: (payload) => request('/api/models/train', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
};
